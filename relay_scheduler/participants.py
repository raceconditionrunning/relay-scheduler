import csv
import pathlib

from relay_scheduler.domain import PreferredDistanceK, PreferredPaceK, PreferredAscentK, PreferredDescentK, \
    PreferredEndExchange, WillingToLead, duration, Participant


def load_participants(participants_filename: pathlib.Path):
    participants = []
    with open(participants_filename, 'r') as f:
        preference_data = csv.DictReader(f, delimiter='\t')
        for preference in preference_data:
            runner_prefs = {"name": preference["Name"], "pace": duration(preference["Pace"], 0.0), "distance": float(preference["Distance"]), "end_exchange": preference["End Exchange"]}
            if "Ascent" in preference:
                runner_prefs["ascent"] = float(preference["Ascent"])
            if "Descent" in preference:
                runner_prefs["descent"] = float(preference["Descent"])
            if "Leader" in preference:
                runner_prefs["lead"] = preference["Leader"].lower() == "yes" or preference["Leader"].lower() == "true"
            participants.append(runner_prefs)
    return participants


def participants_to_facts(participants, exchanges, distance_precision:float, duration_precision: float):
    facts = []
    PreferredDistance = PreferredDistanceK(distance_precision)
    PreferredPace = PreferredPaceK(duration_precision)
    PreferredAscent = PreferredAscentK(duration_precision)
    PreferredDescent = PreferredDescentK(duration_precision)

    for preference in participants:
        facts.append(Participant(name=preference["name"]))
        facts.append(PreferredDistance(name=preference["name"], distance=preference["distance"]))
        facts.append(PreferredPace(name=preference["name"], pace=preference["pace"]))
        if "ascent" in preference:
            facts.append(PreferredAscent(name=preference["name"], ascent=preference["ascent"]))
        if "descent" in preference:
            facts.append(PreferredDescent(name=preference["name"], descent=preference["descent"]))
        if "end_exchange" in preference:
            if not preference["end_exchange"].lower() == "no preference" or not preference["end_exchange"]:
                if preference["end_exchange"] not in exchanges:
                    raise ValueError(f"Exchange {preference['end_exchange']} not found in exchange list")
                end_exchange_id = exchanges[preference["end_exchange"]]
                facts.append(PreferredEndExchange(name=preference["name"], exchange_id=end_exchange_id))
        if "lead" in preference and preference["lead"]:
            facts.append(WillingToLead(name=preference["name"]))
    return facts