import itertools
import math

import clorm
from clorm import desc
from tabulate import tabulate

from relay_scheduler.domain import PreferredDistanceK, PreferredPaceK, LegPaceK, DistanceK, CommuteDistanceK, Run, Leg, ExchangeName, Ascent, Descent, PreferredEndExchange, LeaderOn, LegDistK


from collections import defaultdict


def find_all_paths(edges):
    graph = defaultdict(list)
    in_degrees = defaultdict(int)

    # Build the graph and count in-degrees
    for start, end in edges:
        graph[start].append(end)
        in_degrees[end] += 1

    # Find starting nodes (nodes with zero in-degrees)
    starting_nodes = [node for node in graph if in_degrees[node] == 0]

    all_paths = []

    # Traverse from each starting node to find all paths
    for start in starting_nodes:
        path = []
        while start is not None:
            path.append(start)
            next_nodes = graph.get(start, [])
            start = next_nodes[0] if next_nodes else None
        all_paths.append(path)

    return all_paths


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
        if leg_num in leader_on_leg:
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

    runner_legs = {runner: list(exchange_pairs)
                     for runner, exchange_pairs in facts.query(Run, Leg)
                     .group_by(Run.runner)
                     .join(Run.leg_id == Leg.id)
                     .order_by(Run.leg_id)
                     .select(Leg.start_id, Leg.end_id).all()
                     }
    all_exchange_visits = {runner: set(itertools.chain(*exchange_pairs)) for runner, exchange_pairs in runner_legs.items()}
    all_segments = {runner: find_all_paths(exchange_pairs) for runner, exchange_pairs in runner_legs.items()}
    start_end_exchanges = {runner: [(segment[0], segment[-1]) for segment in segments] for runner, segments in all_segments.items()}
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
    runner_end_dev = {runner: facts.query(CommuteDistance).where(CommuteDistance.start_id == start_end_exchanges[runner][-1][1], CommuteDistance.end_id == runner_pref_end[runner]).select(CommuteDistance.dist).first() for runner in runner_pref_end.keys()}
    runner_preferred_dist = dict(facts.query(PreferredDistance)
                        .select(PreferredDistance.name, PreferredDistance.distance)
                        .all())

    runner_names = list(sorted(legs.keys()))

    # We're not using the auxilliary predicates because, unless the user specified an optimization directive
    # that needs, them they won't be grounded. We recompute here in any case
    runner_dists = {name: list(dists) for name, dists in
                    facts.query(Run, Leg, Distance).group_by(Run.runner).join(Leg.id == Run.leg_id, Distance.start_id == Leg.start_id, Distance.end_id == Leg.end_id).select(Distance.dist).all()}
    runner_dist_dev = {name: sum(runner_dists.get(name, [])) - preferred_dist for name, preferred_dist in runner_preferred_dist.items()}
    runner_ascent = {name: list(ascents) for name, ascents in
                    facts.query(Run, Leg, Ascent).group_by(Run.runner).join(Leg.id == Run.leg_id, Ascent.start_id == Leg.start_id, Ascent.end_id == Leg.end_id).order_by(
                        Run.leg_id).select(Ascent.ascent).all()}
    runner_descent = {name: list(ascents) for name, ascents in
                    facts.query(Run, Leg, Descent).group_by(Run.runner).join(Leg.id == Run.leg_id, Descent.start_id == Leg.start_id, Descent.end_id == Leg.end_id).order_by(
                        Run.leg_id).select(Descent.descent).all()}

    assignments = []
    for runner in sorted(runner_names):
        details = {}
        details["runner"] = runner
        details["legs"] = legs[runner]
        details["exchanges"] = []
        for segment in all_segments[runner]:
            details["exchanges"].append([exchange_names[exchange] for exchange in segment])
        details["paces"] = leg_paces[runner]
        details["total_distance_mi"] = sum(runner_dists.get(runner, [0]))
        details["distance_mi"] = runner_dists.get(runner, [])
        details["total_ascent_ft"] = sum(runner_ascent.get(runner, []))
        details["ascent_ft"] = runner_ascent.get(runner, [])
        details["total_descent_ft"] = sum(runner_descent.get(runner, []))
        details["descent_ft"] = runner_descent.get(runner, [])
        details["loss_distance"] = runner_dist_dev[runner]
        details["loss_end"] = runner_end_dev.get(runner, 0) # If no entry, user has no preference
        details["loss_pace"] = pace_deviations[runner]
        assignments.append(details)
    return assignments


def pace_to_str(pace):
    if pace >= 3600:
        return f"{pace // 3600:0.0f}:{(pace % 3600) // 60:02.0f}:{(pace % 60):02.0f}"
    return f"{pace // 60:0.0f}:{(pace % 60):02.0f}"


def assignments_to_str(assignments):
    rows = []
    for r in assignments:
        exchange_summary = f"{len(r['exchanges'])} segments"
        if len(r["exchanges"]) == 1:
            exchange_summary = f"{r['exchanges'][0][0]} to {r['exchanges'][0][-1]}"
        rows.append([r["runner"], exchange_summary, "", r["total_distance_mi"],
                     list(map(pace_to_str, r["paces"])), r["total_ascent_ft"], r["loss_distance"],
                     r["loss_end"], r["loss_pace"]])
        if len(r["exchanges"]) > 1:
            leg_offset = 0
            for segment in r["exchanges"]:
                rows.append(["", segment[0], segment[-1], sum(r["distance_mi"][leg_offset:leg_offset + len(segment) - 1]), "", sum(r["ascent_ft"][leg_offset:leg_offset + len(segment) - 1]), "", "", ""])
                leg_offset += len(segment) - 1

    rows.append(
        ["Total", "", "", "", "", "", sum(x["loss_distance"] for x in assignments), sum(x["loss_end"] for x in assignments), sum(sum(x["loss_pace"]) for x in assignments)])
    return tabulate(rows, headers=["Runner", "Start", "End", "Distance", "Paces", "Ascent", "Loss Distance", "Loss Commute", "Loss Pace"])


def schedule_to_str(schedule, exchange_overhead=2 * 60):
    start_offset = 0
    rows = []
    for leg in schedule:
        leg_num = leg["leg"]
        pace = leg["pace_mi"]
        pace_pretty = pace_to_str(pace)
        offset_pretty = pace_to_str(start_offset)
        leg_participants = ', '.join(sorted(leg["runners"]))
        rows.append([leg_num, offset_pretty, leg["start_exchange_name"], leg["distance_mi"], pace_pretty, leg["ascent_ft"],
                     leg.get("leader", None), leg_participants])
        leg_duration = pace * leg["distance_mi"]
        start_offset += math.ceil(exchange_overhead + leg_duration)
    offset_pretty = pace_to_str(start_offset)
    rows.append(
        ["Total", offset_pretty, "", sum(x["distance_mi"] for x in schedule), "", sum(x["ascent_ft"] for x in schedule), "", ""])
    return tabulate(rows, headers=["Leg", "Offset", "Start", "Distance", "Pace", "Ascent", "Leader", "Runners"])


def schedule_to_rows(schedule, exchange_overhead=2 * 60):
    start_offset = 0
    rows = [["Leg", "Start Station", "Leader", "Runners", "Distance (mi)", "Pace /mi", "Scheduled Start"]]
    for leg in schedule:
        leg_num = leg["leg"]
        pace = leg["pace_mi"]
        pace_pretty = pace_to_str(pace)
        offset_pretty = pace_to_str(start_offset)
        leg_participants = ', '.join(sorted(leg["runners"]))
        rows.append([leg_num, leg["start_exchange_name"], leg.get("leader", None), leg_participants, leg["distance_mi"], pace_pretty, offset_pretty])
        leg_duration = pace * leg["distance_mi"]
        start_offset += math.ceil(exchange_overhead + leg_duration)
    return rows
