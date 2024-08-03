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
from relay_scheduler.schedule import assignments_to_str, schedule_to_str, schedule_to_rows
from relay_scheduler.transformer import FloatPaceTransformer


def extract_schedule(facts: clorm.FactBase, distance_precision: float, duration_precision: float):
    LegDist, LegPace = LegDistK(distance_precision), LegPaceK(duration_precision)
    runners_on_legs = {leg_num: list(runners) for leg_num, runners in
                       facts.query(Run).group_by(Run.leg_id).select(Run.runner).all()}
    leader_on_leg = {leg_num: list(runners)[0] for leg_num, runners in
                     facts.query(LeaderOn).group_by(LeaderOn.leg_id).select(LeaderOn.runner).all()}
    exchange_names = dict(facts.query(ExchangeName).select(ExchangeName.id, ExchangeName.name).all())
    legs = list(facts.query(Leg).order_by(Leg.id).all())
    leg_paces = list(facts.query(LegPace).order_by(LegPace.leg).select(LegPace.pace).all())
    leg_ascent = list(facts.query(Ascent).order_by(Ascent.start_id).select(Ascent.ascent).all())
    leg_descent = list(facts.query(Descent).order_by(Descent.start_id).select(Descent.descent).all())
    leg_dist = list(facts.query(LegDist).order_by(LegDist.leg).select(LegDist.dist).all())

    schedule = []
    for leg_num in range(len(legs)):
        exchange_start, exchange_end = legs[leg_num].start_id, legs[leg_num].end_id
        details = {}
        details["leg"] = leg_num
        details["start_exchange_name"] = exchange_names[exchange_start]
        details["end_exchange_name"] = exchange_names[exchange_end]
        details["start_exchange"] = exchange_start
        details["end_exchange"] = exchange_end
        details["runners"] = runners_on_legs[leg_num]
        details["leader"] = leader_on_leg[leg_num]
        details["pace_mi"] = leg_paces[leg_num]
        details["distance_mi"] = leg_dist[leg_num]
        details["ascent_ft"] = leg_ascent[leg_num]
        details["descent_ft"] = leg_descent[leg_num]
        schedule.append(details)
    return schedule


def extract_assignments(facts: clorm.FactBase, distance_precision: float, duration_precision: float):
    PreferredDistance, PreferredPace, LegPace, Distance, CommuteDistance = PreferredDistanceK(distance_precision), PreferredPaceK(duration_precision), LegPaceK(
        duration_precision), DistanceK(distance_precision), CommuteDistanceK(distance_precision)

    all_exchanges = {runner: list(exchange_pairs)
                     for runner, exchange_pairs in facts.query(Run, Leg)
                     .group_by(Run.runner)
                     .join(Run.leg_id == Leg.id)
                     .order_by(Run.leg_id)
                     .select(Leg.start_id, Leg.end_id).all()
                     }
    all_exchanges = {runner: [x[0] for x in exchange_pairs] + [exchange_pairs[-1][1]] for runner, exchange_pairs in all_exchanges.items()}
    start_end_exchanges = {runner: (exchanges[0], exchanges[-1]) for runner, exchanges in all_exchanges.items()}
    exchange_names = dict(facts.query(ExchangeName).select(ExchangeName.id, ExchangeName.name).all())
    legs = {runner: list(leg_ids)
            for runner, leg_ids in
            facts.query(Run)
            .group_by(Run.runner)
            .order_by(Run.leg_id)
            .select(Run.leg_id).all()
            }
    leg_paces = {runner: list(paces)
                 for runner, paces in
                 facts.query(Run, LegPace)
                 .group_by(Run.runner)
                 .join(Run.leg_id == LegPace.leg)
                 .order_by(desc(Run.leg_id))
                 .select(LegPace.pace).all()
                 }
    preferred_paces = {runner: list(preferred_pace)[0] for runner, preferred_pace in
                       facts.query(PreferredPace).group_by(PreferredPace.name).select(PreferredPace.pace).all()}
    pace_deviations = {runner: list(map(lambda actual: actual - preferred_paces[runner], paces)) for runner, paces in leg_paces.items()}
    runner_pref_end = dict(facts.query(PreferredEndExchange).select(PreferredEndExchange.name, PreferredEndExchange.exchange_id).all())
    runner_end_dev = {runner: facts.query(CommuteDistance).where(CommuteDistance.start_id == start_end_exchanges[runner][1], CommuteDistance.end_id == runner_pref_end[runner]).select(CommuteDistance.dist).first() for runner in runner_pref_end.keys()}
    runner_preferred_dist = dict(facts.query(PreferredDistance)
                        .select(PreferredDistance.name, PreferredDistance.distance)
                        .all())

    runner_names = list(sorted(legs.keys()))

    # We're not using the auxilliary predicates because, unless the user specified an optimization directive
    # that needs, them they won't be grounded. We recompute here in any case
    total_dist = {name: sum(dists) for name, dists in
                    facts.query(Run, Leg, Distance).group_by(Run.runner).join(Leg.id == Run.leg_id, Distance.start_id == Leg.start_id, Distance.end_id == Leg.end_id).select(Distance.dist).all()}
    runner_dist_dev = {name: total_dist[name] - preferred_dist for name, preferred_dist in runner_preferred_dist.items()}
    total_ascent = {name: sum(ascents) for name, ascents in
                    facts.query(Run, Leg, Ascent).group_by(Run.runner).join(Leg.id == Run.leg_id, Ascent.start_id == Leg.start_id, Ascent.end_id == Leg.end_id).order_by(
                        Run.leg_id).select(Ascent.ascent).all()}
    total_descent = {name: sum(ascents) for name, ascents in
                    facts.query(Run, Leg, Descent).group_by(Run.runner).join(Leg.id == Run.leg_id, Descent.start_id == Leg.start_id, Descent.end_id == Leg.end_id).order_by(
                        Run.leg_id).select(Descent.descent).all()}

    assignments = []
    for runner in sorted(runner_names):
        details = {}
        details["runner"] = runner
        details["legs"] = legs[runner]
        details["start_exchange"] = exchange_names[start_end_exchanges[runner][0]]
        details["end_exchange"] = exchange_names[start_end_exchanges[runner][1]]
        details["paces"] = leg_paces[runner]
        details["distance_mi"] = total_dist[runner]
        details["ascent_ft"] = total_ascent[runner]
        details["descent_ft"] = total_descent[runner]
        details["loss_distance"] = runner_dist_dev[runner]
        details["loss_end"] = runner_end_dev.get(runner, 0) # If no entry, user has no preference
        details["loss_pace"] = pace_deviations[runner]
        assignments.append(details)
    return assignments


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


def main(args):
    event = args.event
    save_ground_model = args.save_ground_program
    save_all_models = args.save_all_models
    team = args.team
    event_name = event
    if team:
        event_name += f"_{team}"
    # Clorm's `Control` wrapper will try to parse model facts into the predicates defined in domain.py.
    ctrl = Control(
        unifier=[LegCoverage, LegPaceK(args.duration_precision), Run, LegDistK(args.distance_precision), ExchangeName, Leg,
                 LegDistK(args.distance_precision), LegAscent, LegDescent, Objective, LeaderOn, DistanceK(args.distance_precision), Ascent, Descent, PreferredDistanceK(args.distance_precision), PreferredPaceK(args.duration_precision), PreferredEndExchange, CommuteDistanceK(args.distance_precision)])
    # Makes exceptions inscrutable. Disable if you need to debug
    #ctrl.configuration.solve.parallel_mode = "4,split"
    #ctrl.configuration.solve.opt_mode = "optN"
    with ProgramBuilder(ctrl) as b:
        t = FloatPaceTransformer(args.distance_precision)
        # All ASP files in the year directory
        year_files = glob.glob(f"{event}/*.lp")
        if team:
            # User wants specific team, don't include other team files
            year_files = list(filter(lambda x: ("team" in x and team in x) or "team" not in x, year_files))
        parse_files(
            ["scheduling-domain.lp"] + year_files,
            lambda stm: b.add(t.visit(stm)))

    # You can supply a bundle of GPX legs and we'll
    # turn them into facts. Otherwise, all the facts
    # need to be in an .lp file in the folder.
    if os.path.isdir(f"{event}/legs"):
        legs = load_from_legs_bundle(f"{event}/legs")
        # Dump out geojson representation so you can check map
        with open(f"{event}/relay.geojson", "w") as f:
            json.dump(legs_to_geojson(legs), f, indent=2)
        facts = legs_to_facts(legs, distance_precision=args.distance_precision,
                              duration_precision=args.duration_precision)
        ctrl.add_facts(FactBase(facts))

    # Load team participants from TSV, if the file exists.
    # Otherwise, these facts need to be in an .lp file.
    if team and os.path.exists(f"{event}/team-{team}.tsv"):
        participants = load_participants(pathlib.Path(f"{event}/team-{team}.tsv"))
        # Extract the name -> ID mapping from facts so far
        exchanges = clorm.unify([ExchangeName], [x.symbol for x in ctrl.symbolic_atoms.by_signature("exchangeName", 2)])
        exchanges = dict(exchanges.query(ExchangeName).select(ExchangeName.name, ExchangeName.id).all())
        facts = participants_to_facts(participants, exchanges, args.distance_precision, args.duration_precision)
        ctrl.add_facts(FactBase(facts))

    # Add precision facts so ASP can be written using the same precision
    # e.g. preferredDist("Runner", @k("10.5",P)) , distancePrecision(P).
    ctrl.add_facts(
        FactBase(
            [DistancePrecision(str(args.distance_precision)),
             DurationPrecision(str(args.duration_precision))
             ]))

    print("Starting grounding at", datetime.datetime.now())
    ctrl.ground([("base", [])], context=make_standard_func_ctx())
    if save_ground_model:
        with open("program.lp", 'w') as f:
            for atom in ctrl.symbolic_atoms:
                f.write(f"{atom.symbol}.\n")
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
