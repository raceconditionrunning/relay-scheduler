#!/usr/bin/env python3

import argparse
import csv
import datetime
import glob
import json
import os
import pathlib

import clorm
import xxhash
from clingo.ast import ProgramBuilder, parse_files
from clorm import desc, FactBase
from clorm.clingo import Control

from relay_scheduler.domain import LegCoverage, LegPaceK, Run, ExchangeName, Leg, \
    LegDistK, LegAscent, Objective, LegDescent, LeaderOn, Ascent, Descent, make_standard_func_ctx, \
    PreferredDistanceK, PreferredPaceK, DurationPrecision, DistancePrecision, WillingToLead, DistanceK, \
    PreferredEndExchange, CommuteDistanceK
from relay_scheduler.legs import load_from_legs_bundle, legs_to_facts, relay_to_geojson
from relay_scheduler.participants import participants_to_facts, load_participants
from relay_scheduler.schedule import assignments_to_str, schedule_to_str, schedule_to_rows, extract_schedule, \
    extract_assignments
from relay_scheduler.transformer import FloatPaceTransformer


def save_solution(passthrough_args, start_time, event_name="", file_name="solution", atoms=None):
    out = {**passthrough_args}
    out["startTime"] = start_time.isoformat()
    out["foundTime"] = datetime.datetime.now().isoformat()
    out["computeTime"] = (datetime.datetime.now() - start_time).total_seconds()
    out_dir = f"solutions/{event_name}_{start_time.isoformat().replace(':', '_')}"
    # Create solutions directory if it doesn't exist
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    with open(f"{out_dir}/{file_name}.json", "w") as f:
        json.dump(out, f, indent=2)
    with open(f"{out_dir}/{file_name}.csv", "w") as f:
        rows = schedule_to_rows(out["schedule"])
        writer = csv.writer(f)
        writer.writerows(rows)
    if atoms:
        with open(f"{out_dir}/{file_name}.lp", "w") as f:
            for atom in atoms:
                f.write(f"{atom}.\n")


def build_ctrl(args):
    # Clorm's `Control` wrapper will try to parse model facts into the predicates defined in domain.py.
    ctrl = Control(
        unifier=[LegCoverage, LegPaceK(args.duration_precision), Run, LegDistK(args.distance_precision), ExchangeName,
                 Leg,
                 LegDistK(args.distance_precision), LegAscent, LegDescent, Objective, LeaderOn,
                 DistanceK(args.distance_precision), Ascent, Descent, PreferredDistanceK(args.distance_precision),
                 PreferredPaceK(args.duration_precision), PreferredEndExchange,
                 CommuteDistanceK(args.distance_precision)])
    # Makes exceptions inscrutable. Disable if you need to debug
    # ctrl.configuration.solve.parallel_mode = "4,split"
    # ctrl.configuration.solve.opt_mode = "optN"
    with ProgramBuilder(ctrl) as b:
        t = FloatPaceTransformer(args.distance_precision)
        # All ASP files in the year directory
        year_files = glob.glob(f"{args.event}/*.lp")
        parse_files(
            ["scheduling-domain.lp"] + year_files,
            lambda stm: b.add(t.visit(stm)))
    return ctrl


def main(args):
    event = args.event
    save_ground_model = args.save_ground_program
    save_all_models = args.save_all_models
    team = args.team
    event_name = event
    if team:
        event_name += f"_{team}"
    team_program = [(team, [])] if team else []
    ctrl = build_ctrl(args)
    additional_facts = []

    # You can supply a bundle of GPX legs and we'll
    # turn them into facts. Otherwise, all the facts
    # need to be in an .lp file in the folder.
    if os.path.isdir(f"{event}/legs"):
        legs_data = load_from_legs_bundle(f"{event}/legs")
        facts = legs_to_facts(legs_data, distance_precision=args.distance_precision,
                              duration_precision=args.duration_precision)
        additional_facts.extend(facts)

    # Load team participants from TSV, if the file exists.
    # Otherwise, these facts need to be in an .lp file.
    if team and os.path.exists(f"{event}/team-{team}.tsv"):
        participants = load_participants(pathlib.Path(f"{event}/team-{team}.tsv"))
        # Extract the name -> ID mapping from facts so far.
        # Get from control in case they were in .lp files
        exchanges = clorm.unify([ExchangeName], [x.symbol for x in ctrl.symbolic_atoms.by_signature("exchangeName", 2)])
        # Get from extra facts if came from leg bundle
        exchanges.add(additional_facts)
        exchanges = dict(exchanges.query(ExchangeName).select(ExchangeName.name, ExchangeName.id).all())
        facts = participants_to_facts(participants, exchanges, args.distance_precision, args.duration_precision)
        additional_facts.extend(facts)

    # Add precision facts so ASP can be written using the same precision
    # e.g. preferredDist("Runner", @k("10.5",P)) , distancePrecision(P).
    additional_facts.extend(
        [DistancePrecision(str(args.distance_precision)),
            DurationPrecision(str(args.duration_precision))
            ])
    to_add = FactBase(additional_facts)
    with open(f"{event}/facts.lpx", "w") as f:
        f.writelines(to_add.asp_str())
    ctrl.add_facts(to_add)

    print("Starting grounding at", datetime.datetime.now())
    ctrl.ground([("base", [])] + team_program, context=make_standard_func_ctx())

    if save_ground_model:
        with open("program.lpx", 'w') as f:
            for atom in ctrl.symbolic_atoms:
                f.write(f"{atom.symbol}.\n")

    # Dump out geojson representation so you can check map
    with open(f"{event}/relay.geojson", "w") as f:
        sequences = clorm.unify([Leg], [x.symbol for x in ctrl.symbolic_atoms.by_signature("leg", 3)])
        sequences = {start_end: list(index) for start_end, index in sequences.query(Leg).group_by(Leg.start_id, Leg.end_id).select(Leg.id).all()}
        json.dump(relay_to_geojson(legs_data, sequences), f, indent=2)

    solve_start_time = datetime.datetime.now()
    print("Starting solve at", solve_start_time)
    model_id = 0
    first_optimal_id = None
    def on_model(model):
        nonlocal model_id
        nonlocal first_optimal_id
        facts = model.facts(atoms=True)
        # This hash should only be used for comparing solutions generated using the same version/dependencies. Clorm
        # may change its string representation in the future, and the facts for a solution depend on the Python
        # bindings for the predicates that we've specified.
        factbase_hash = xxhash.xxh64_hexdigest(facts.asp_str(sorted=True))
        objectives_by_priority = dict(facts.query(Objective).order_by(desc(Objective.priority)).select(Objective.priority, Objective.name).all())
        schedule, assignments = extract_schedule(facts, args.distance_precision, args.duration_precision), extract_assignments(facts, args.distance_precision, args.duration_precision)
        print(assignments_to_str(assignments))
        print(schedule_to_str(schedule))
        costs = {objectives_by_priority[priority]: cost for priority, cost in zip(model.priority, model.cost)}
        print(costs)
        file_name = "solution"
        if save_all_models:
            file_name = f"{model_id}"
        elif model.optimality_proven:
            if not first_optimal_id:
                first_optimal_id = model_id
            file_name += f"_{model_id - first_optimal_id}"
        save_solution({
            "costs": costs,
            "distance_precision": args.distance_precision,
            "duration_precision": args.duration_precision,
            #"elevation_precision": args.elevation_precision,
            "optimal": model.optimality_proven,
            "schedule": schedule,
            "assignments": assignments,
            "hash": factbase_hash
        },
            solve_start_time, event_name, file_name, atoms=model.symbols(atoms=True))

        model_id += 1

    ctrl.solve(on_model=on_model)
    print("Finished solve at", datetime.datetime.now())
    print("Elapsed time:", datetime.datetime.now() - solve_start_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    asp_subdir_paths = glob.glob("*/*.lp")
    subdirs = set([str(pathlib.Path(p).parent) for p in asp_subdir_paths])
    parser.add_argument("event", choices=subdirs, help="Path to directory containing relay domain .lp files")
    parser.add_argument("--save-all-models", action="store_true", help="Save all (even non-optimal) models found while solving")
    parser.add_argument("--team", default=None, type=str, help="Include a file named 'team-<TEAM>.lp' and ignore all other .lp files beginning with 'team'. Useful for scheduling separate groups.")
    parser.add_argument("--save-ground-program", action="store_true", help="Store the ground program to 'program.lp'. Use to debug lengthy ground-times, and to see which rules cause your domain to grow")
    parser.add_argument("--distance-precision", default=2.0, type=float, help="Number of decimal places of fixed precision to convert distance terms to")
    # Not implemented yet. Consider implementing if using elevation/duration optimization criteria heavily and programs are too big.
    #parser.add_argument("--elevation-precision", default=0.0, type=float, help="Number of decimal places of fixed precision to convert elevation terms to")
    parser.add_argument("--duration-precision", default=0.0, type=float, help="Number of decimal places of fixed precision to convert distance terms to")
    args = parser.parse_args()
    main(args)
