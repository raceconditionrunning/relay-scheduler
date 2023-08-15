#!/usr/bin/env python3

import argparse
import csv
import datetime
import glob
import json
import math
import os
import pathlib

import clingo
import clingo.ast as ast
import clorm
from clingo.ast import ProgramBuilder, parse_files, Transformer
from clingo.symbol import Number
from clorm import desc, FactBase
from clorm.clingo import Control

from relay_scheduler.domain import LegCoverage, LegPace, Run, ExchangeName, Leg, DistDiffK, EndDeviationK, PaceSlack, \
    LegDistK, TotalDistK, LegAscent, Objective, LegDescent, LeaderOn, Ascent, Descent
from relay_scheduler.legs import load_from_legs_bundle, legs_to_geojson, legs_to_facts
from relay_scheduler.schedule import assignments_to_str, schedule_to_str, schedule_to_rows


class FloatPaceTransformer(Transformer):
    """
    Transforms terms of the form k("1.5") into k(150), and k("1:30") into k(90).
    """

    def __init__(self, distance_precision=2.0, duration_precision=0.0):
        self.distance_precision = distance_precision
        self.duration_precision = duration_precision

    def visit_Function(self, node):
        new_args = []
        for arg in node.arguments:
            if arg.ast_type == ast.ASTType.SymbolicTerm and arg.symbol.type == clingo.SymbolType.String:
                if ":" in arg.symbol.string:
                    # Parse duration (e.g. 8:00 or 12:30)
                    seconds = sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(arg.symbol.string.split(":"))))
                    seconds = math.ceil(seconds * 10 ** self.duration_precision)
                    new_args.append(ast.SymbolicTerm(node.location, Number(seconds)))
                    continue
                try:
                    as_float = float(arg.symbol.string)
                    as_int = math.ceil(as_float * 10 ** self.distance_precision)
                    new_args.append(ast.SymbolicTerm(node.location, Number(as_int)))
                except ValueError:
                    new_args.append(arg)
            else:
                new_args.append(arg)
        return node.update(arguments=new_args)


def get_predicate_clases_for_names(names, predicates):
    classes = [None] * len(names)
    for predicate in predicates:
        for i, search_name in enumerate(names):
            if predicate.meta.name == names[i]:
                classes[i] = predicate
    return classes


def extract_schedule(facts):
    LegDist = get_predicate_clases_for_names(["legDist"], facts.predicates)[0]

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


def extract_assignments(facts):
    EndDeviation, DistDiff, TotalDist = get_predicate_clases_for_names(["endDeviation", "distDiff", "totalDist"],
                                                                       facts.predicates)
    all_exchanges = {runner: list(exchanges)
                     for runner, exchanges in facts.query(Run, Leg, ExchangeName)
                     .group_by(Run.runner)
                     .join(Run.leg_id == Leg.id, Leg.start_id == ExchangeName.id)
                     .order_by(Run.leg_id)
                     .select(ExchangeName.name).all()
                     }
    start_end_exchanges = {runner: (exchanges[0], exchanges[-1]) for runner, exchanges in all_exchanges.items()}
    legs = {x[0]: list(x[1])
            for x in
            facts.query(Run)
            .group_by(Run.runner)
            .order_by(Run.leg_id)
            .select(Run.leg_id).all()
            }
    leg_paces = {x[0]: list(x[1])
                 for x in
                 facts.query(Run, LegPace)
                 .group_by(Run.runner)
                 .join(Run.leg_id == LegPace.leg)
                 .order_by(desc(Run.leg_id))
                 .select(LegPace.pace).all()
                 }
    runner_pace_dev = {x[0]: sum(x[1]) for x in
                       facts.query(PaceSlack).group_by(PaceSlack.name).select(PaceSlack.deviation).all()}
    runner_end_dev = {x.name: x.deviation for x in facts.query(EndDeviation).all()}
    runner_dist_dev = {x.name: x.deviation for x in facts.query(DistDiff).all()}
    runner_names = list(facts.query(DistDiff).order_by(DistDiff.name).select(DistDiff.name).distinct().all())
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
        details["loss_end"] = runner_end_dev[runner]
        details["loss_pace"] = runner_pace_dev[runner]
        assignments.append(details)
    return assignments


def save_solution(passthrough_args, start_time, event_name="", file_name="solution"):
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


def main(args):
    event = args.event
    save_ground_model = args.save_ground_program
    save_all_models = args.save_all_models
    # Clorm's Control wrapper will try to parse model facts into the predicates defined in domain.py.
    ctrl = Control(
        unifier=[LegCoverage, LegPace, Run, LegDistK(args.distance_precision), ExchangeName, Leg,
                 DistDiffK(args.distance_precision), EndDeviationK(args.distance_precision), PaceSlack,
                 LegDistK(args.distance_precision),
                 TotalDistK(args.distance_precision), LegAscent, LegDescent, Objective, LeaderOn, Ascent, Descent])
    with ProgramBuilder(ctrl) as b:
        t = FloatPaceTransformer(args.distance_precision)
        # All ASP files in the year directory
        year_files = glob.glob(f"{event}/*.lp")
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
    ctrl.ground([("base", [])])
    if save_ground_model:
        with open("program.lp", 'w') as f:
            for atom in ctrl.symbolic_atoms:
                f.write(f"{atom.symbol}.\n")
    solve_start_time = datetime.datetime.now()
    print("Starting solve at", solve_start_time)
    model_id = 0

    def on_model(model):
        nonlocal model_id
        facts = model.facts(atoms=True)
        objective_names = list(facts.query(Objective).order_by(desc(Objective.index)).select(Objective.name).all())
        schedule, assignments = extract_schedule(facts), extract_assignments(facts)
        print(assignments_to_str(assignments))
        print(schedule_to_str(schedule))
        costs = dict((zip(objective_names, model.cost)))
        print(costs)
        file_name = "solution"
        if save_all_models:
            file_name = f"{model_id}"
        save_solution({
            "costs": costs,
            "distance_precision": args.distance_precision,
            "duration_precision": args.duration_precision,
            "elevation_precision": args.elevation_precision,
            "optimal": model.optimality_proven,
            "schedule": schedule,
            "assignments": assignments,
        },
            solve_start_time, event, file_name)

        model_id += 1

    ctrl.solve(on_model=on_model)
    print("Finished solve at", datetime.datetime.now())
    print("Elapsed time:", datetime.datetime.now() - solve_start_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    asp_subdir_paths = glob.glob("*/*.lp")
    subdirs = set([str(pathlib.Path(p).parent) for p in asp_subdir_paths])
    parser.add_argument("event", choices=subdirs)
    parser.add_argument("--save-all-models", action="store_true")
    parser.add_argument("--save-ground-program", action="store_true")
    parser.add_argument("--distance-precision", default=2.0, type=float)
    parser.add_argument("--elevation-precision", default=0.0, type=float)
    parser.add_argument("--duration-precision", default=0.0, type=float)
    args = parser.parse_args()
    main(args)
