#!/usr/bin/env python3

"""
Pretty print a schedule from a solution JSON file or raw Clingo output.
"""

import argparse
import json
import pathlib
import re

from clorm import clingo

from relay_scheduler.domain import LegCoverage, Leg, LegDistK, DistanceK, PreferredPaceK, CommuteDistanceK, LegAscent, \
    Ascent, PreferredEndExchange, Descent, LegDescent, PreferredDistanceK, Objective, LeaderOn, ExchangeName, Run, \
    LegPaceK
from relay_scheduler.schedule import assignments_to_str, schedule_to_str, extract_schedule, extract_assignments


def split_solve_output(solve_output: pathlib.Path):
    with open(solve_output) as f:
        answers = []
        costs = []
        lines = f.readlines()
        i = 3
        while i < len(lines):
            line = lines[i]
            if line.startswith("Answer"):
                answers.append(lines[i + 1])
                numbers = lines[i + 2].split(":")[1].strip().split(" ")
                costs.append(list(map(int, numbers)))
                i += 3
                continue
            i += 1
    return answers, costs


def extract_schedule_from_answer_set(answer_set):

    # pull distancePrecsion(<float>) and durationPrecision(<float>) from answer_set
    distance_precision = re.search(r'distancePrecision\(\"(\d+\.\d+)\"\)', answer_set)
    duration_precision = re.search(r'durationPrecision\(\"(\d+\.\d+)\"\)', answer_set)
    if not distance_precision:
        distance_precision = 2.0
    else:
        distance_precision = float(distance_precision.group(1))
    if not duration_precision:
        duration_precision = 0.0
    else:
        duration_precision = float(duration_precision.group(1))
    clingo_control = clingo.Control(
        unifier=[LegCoverage, LegPaceK(duration_precision), Run, LegDistK(distance_precision), ExchangeName,
                 Leg,
                 LegDistK(distance_precision), LegAscent, LegDescent, Objective, LeaderOn,
                 DistanceK(distance_precision), Ascent, Descent, PreferredDistanceK(distance_precision),
                 PreferredPaceK(duration_precision), PreferredEndExchange,
                 CommuteDistanceK(distance_precision)])
    clingo_control.add(answer_set)
    clingo_control.ground([("base", [])])
    facts = clingo_control.unifier.unify([symbol.symbol for symbol in clingo_control.symbolic_atoms])
    return extract_schedule(facts, distance_precision, duration_precision), extract_assignments(facts,  distance_precision, duration_precision)


def main(args):
    if args.solution_path.suffix == ".txt":
        answer_sets, costs = split_solve_output(args.solution_path)
        for answer_set, cost in zip(answer_sets, costs):
            schedule, assignments = extract_schedule_from_answer_set(answer_set)
            print(assignments_to_str(assignments))
            print(schedule_to_str(schedule, exchange_overhead=args.exchange_overhead, climbing_adjustment=args.climbing_adjustment))

    elif args.solution_path.suffix == ".json":
        with open(args.solution_path) as f:
            solution = json.load(f)
        costs = solution["costs"].items()
        schedule, assignments = solution["schedule"], solution["assignments"]
        print(assignments_to_str(assignments))
        print(schedule_to_str(schedule, exchange_overhead=args.exchange_overhead, ascent_factor=args.ascent_factor))
        print(costs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("solution_path", type=pathlib.Path)
    parser.add_argument("--exchange-overhead", type=int, default=60, help="Time in seconds to add at each exchange")
    parser.add_argument("--ascent-factor", type=int, default=10, help="Seconds per mile added for each 100ft of elevation gain on a leg")
    args = parser.parse_args()
    main(args)
