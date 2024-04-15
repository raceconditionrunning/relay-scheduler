#!/usr/bin/env python3

"""
Pretty print a schedule from a solution JSON file.
"""

import argparse
import json

from relay_scheduler.schedule import assignments_to_str, schedule_to_str


def main(args):
    solution_path = args.solution_json
    with open(solution_path) as f:
        solution = json.load(f)
    costs = solution["costs"].items()
    schedule, assignments = solution["schedule"], solution["assignments"]
    print(assignments_to_str(assignments))
    print(schedule_to_str(schedule, exchange_overhead=args.exchange_overhead))
    print(costs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("solution_json", type=str)
    parser.add_argument("--exchange-overhead", type=int, default=2 * 60, help="Time in seconds to add at each exchange")
    args = parser.parse_args()
    main(args)
