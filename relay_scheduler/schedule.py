import math

from tabulate import tabulate


def pace_to_str(pace):
    if pace >= 3600:
        return f"{pace // 3600:0.0f}:{(pace % 3600) // 60:02.0f}:{(pace % 60):02.0f}"
    return f"{pace // 60:0.0f}:{(pace % 60):02.0f}"


def assignments_to_str(assignments):
    rows = []
    for r in assignments:
        rows.append([r["runner"], r["start_exchange"], r["end_exchange"], r["distance_mi"],
                     list(map(pace_to_str, r["paces"])), r["ascent_ft"], r["loss_distance"],
                     r["loss_end"], r["loss_pace"]])
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
                     leg["leader"], leg_participants])
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
        rows.append([leg_num, leg["start_exchange_name"], leg["leader"], leg_participants, leg["distance_mi"], pace_pretty, offset_pretty])
        leg_duration = pace * leg["distance_mi"]
        start_offset += math.ceil(exchange_overhead + leg_duration)
    return rows
