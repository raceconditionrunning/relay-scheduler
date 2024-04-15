#!/usr/bin/env python3

import argparse
import csv
import datetime
import glob
import json
import math
import os
import pathlib
from typing import Iterable, List, Type, Optional

import clingo
import clingo.ast as ast
import clorm
import xxhash
from clingo.ast import ProgramBuilder, parse_files, Transformer
from clingo.symbol import Number
from clorm import desc, FactBase
from clorm.clingo import Control

from relay_scheduler.domain import LegCoverage, LegPaceK, Run, ExchangeName, Leg, EndDeviationK, \
    LegDistK, TotalDistK, LegAscent, Objective, LegDescent, LeaderOn, Ascent, Descent, make_standard_func_ctx, \
    PreferredDistanceK, PreferredPaceK
from relay_scheduler.legs import load_from_legs_bundle, legs_to_geojson, legs_to_facts
from relay_scheduler.schedule import assignments_to_str, schedule_to_str, schedule_to_rows


class FloatPaceTransformer(Transformer):
    """
    Transforms terms of the form k("1.5") into k(150), and k("1:30") into k(90).
    """

    def __init__(self, distance_precision=2.0, duration_precision=0.0):
        self.distance_precision = distance_precision
        self.duration_precision = duration_precision

    def visit_SymbolicTerm(self, node):
        if node.symbol.type == clingo.SymbolType.String:
            if ":" in node.symbol.string:
                # Parse duration (e.g. 8:00 or 12:30)
                seconds = sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(node.symbol.string.split(":"))))
                seconds = math.ceil(seconds * 10 ** self.duration_precision)
                return ast.SymbolicTerm(node.location, Number(seconds))
            try:
                as_float = float(node.symbol.string)
                as_int = math.ceil(as_float * 10 ** self.distance_precision)
                return ast.SymbolicTerm(node.location, Number(as_int))
            except ValueError:
                return node
        return node


def get_predicate_clases_for_names(names: List[str], predicates: Iterable[Type[clorm.Predicate]]) -> List[Type[Optional[clorm.Predicate]]]:
    """
    Finds the correct generated class (various predicates are templated by user-specified precision) for each predicate

    :param names: Domain predicate names
    :param predicates: Predicates available to match from
    :return:
    """
    classes = [None] * len(names)
    for predicate in predicates:
        for i, search_name in enumerate(names):
            if predicate.meta.name == names[i]:
                classes[i] = predicate
                break
    return classes


def extract_schedule(facts: clorm.FactBase):
    LegDist, LegPace = get_predicate_clases_for_names(["legDist", "legPace"], facts.predicates)
    if LegDist is None or LegPace is None:
        return {}
    runners_on_legs = {leg_num: list(runners) for leg_num, runners in
                       facts.query(Run).group_by(Run.leg_id).select(Run.runner).all()}
    leader_on_leg = {leg_num: list(runners)[0] for leg_num, runners in
                     facts.query(LeaderOn).group_by(LeaderOn.leg_id).select(LeaderOn.runner).all()}
    exchange_names = list(facts.query(ExchangeName).order_by(ExchangeName.id).select(ExchangeName.name).all())
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


def extract_assignments(facts: clorm.FactBase):
    EndDeviation, TotalDist, PreferredDistance, PreferredPace, LegPace = get_predicate_clases_for_names(["endDeviation", "totalDist", "preferredDistance", "preferredPace", "legPace"],
                                                                       facts.predicates)
    if EndDeviation is None:
        return {}
    all_exchanges = {runner: list(exchanges)
                     for runner, exchanges in facts.query(Run, Leg, ExchangeName)
                     .group_by(Run.runner)
                     .join(Run.leg_id == Leg.id, Leg.start_id == ExchangeName.id)
                     .order_by(Run.leg_id)
                     .select(ExchangeName.name).all()
                     }
    start_end_exchanges = {runner: (exchanges[0], exchanges[-1]) for runner, exchanges in all_exchanges.items()}
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
    runner_end_dev = {x.name: x.deviation for x in facts.query(EndDeviation).all()}
    runner_dist_dev_raw = {name: list(facts) for name, facts in facts.query(TotalDist, PreferredDistance)
                        .join(TotalDist.name == PreferredDistance.name)
                        .group_by(TotalDist.name)
                        .select(TotalDist.dist, PreferredDistance.distance)
                        .all()
                       }
    runner_dist_dev = {name: facts[0][0] - facts[0][1] for name, facts in runner_dist_dev_raw.items()}
    runner_names = list(sorted(legs.keys()))
    total_dist = {x.name: x.dist for x in facts.query(TotalDist).all()}
    # We're not using the TotalAscent/Descent predicates in the domain because they blow up the ground program
    # size and we don't reason about elevation.
    total_ascent = {name: sum(ascents) for name, ascents in
                    facts.query(Run, Ascent).group_by(Run.runner).join(Ascent.start_id == Run.leg_id).order_by(
                        Run.leg_id).select(Ascent.ascent).all()}
    total_descent = {name: sum(descents) for name, descents in
                     facts.query(Run, Descent).group_by(Run.runner).join(Descent.start_id == Run.leg_id).order_by(
                         Run.leg_id).select(Descent.descent).all()}

    assignments = []
    for runner in sorted(runner_names):
        details = {}
        details["runner"] = runner
        details["legs"] = legs[runner]
        details["start_exchange"] = start_end_exchanges[runner][0]
        details["end_exchange"] = start_end_exchanges[runner][1]
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
        unifier=[LegCoverage, LegPaceK(args.duration_precision), Run, LegDistK(args.distance_precision), ExchangeName, Leg, EndDeviationK(args.distance_precision),
                 LegDistK(args.distance_precision),
                 TotalDistK(args.distance_precision), LegAscent, LegDescent, Objective, LeaderOn, Ascent, Descent, PreferredDistanceK(args.distance_precision), PreferredPaceK(args.duration_precision)])
    # Makes exceptions inscrutable. Disable if you need to debug
    ctrl.configuration.solve.parallel_mode = "4,split"
    ctrl.configuration.solve.opt_mode = "optN"
    with ProgramBuilder(ctrl) as b:
        t = FloatPaceTransformer(args.distance_precision)
        # All ASP files in the year directory
        year_files = glob.glob(f"{event}/*.lp")
        if team:
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
        objective_names = list(facts.query(Objective).order_by(desc(Objective.index)).select(Objective.name).all())
        schedule, assignments = extract_schedule(facts), extract_assignments(facts)
        print(assignments_to_str(assignments))
        print(schedule_to_str(schedule))
        costs = dict((zip(objective_names, model.cost)))
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
