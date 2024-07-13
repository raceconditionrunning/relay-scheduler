from glob import glob

import clingo
import clorm
import lxml
from lxml import etree
import os
import haversine

from relay_scheduler.domain import DistanceK, Ascent, ExchangeName, CommuteDistanceK, Descent


def load_from_legs_bundle(dir_path):
    legs = {}

    for gpx_filename in glob(os.path.join(dir_path, "*.gpx")):
        # Filenames are assumed to be of the form "<start_id>-<end_id>.gpx"
        start_id, end_id = os.path.splitext(os.path.basename(gpx_filename))[0].split("-")
        with open(gpx_filename) as f:
            gpx_data = lxml.etree.parse(f)
        points = gpx_data.xpath("//gpx:trkpt", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
        coordinates = []
        for point in points:

            elevation = point.xpath("gpx:ele", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})[0].text
            coordinates.append((float(point.attrib["lat"]), float(point.attrib["lon"]), float(elevation)))
        title = gpx_data.xpath("//gpx:name", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})[0].text
        keywords_tag = gpx_data.xpath("//gpx:keywords", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
        attributes = []
        if keywords_tag:
            attributes = keywords_tag[0].text.split(",")
        start_name, end_name = title.split(" to ")
        ascent = sum(max(0, c2[2] - c1[2]) for c1, c2 in zip(coordinates[:-1], coordinates[1:])) * 3.28084
        descent = sum(max(0, c1[2] - c2[2]) for c1, c2 in zip(coordinates[:-1], coordinates[1:])) * 3.28084
        distance = sum(haversine.haversine(c1[:2], c2[:2], unit=haversine.Unit.MILES) for c1, c2 in zip(coordinates[:-1], coordinates[1:]))
        description = gpx_data.xpath("//gpx:desc", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
        if description:
            description = description[0].text
        else:
            description = ""
        leg = {'distance_mi': distance,
               'ascent_ft': ascent,
               'descent_ft': descent,
               'start_exchange': int(start_id),
                'end_exchange': int(end_id),
               'notes': description,
               'start_name': start_name,
                'end_name': end_name,
               'coordinates': coordinates,
               'attributes': attributes
               }
        legs[(int(start_id), int(end_id))] = leg
    return legs


def flip_lat_long(lat_long_ele_point):
    return (lat_long_ele_point[1], lat_long_ele_point[0], lat_long_ele_point[2])


def legs_to_geojson(legs):
    features = []
    for leg in sorted(legs.values(), key=lambda x: x["start_exchange"]):
        leg_without_coordinates = {k: v for k, v in leg.items() if k != "coordinates"}
        leg_feature = {"type": "Feature",
                       "properties": leg_without_coordinates,
                       "geometry": {"type": "LineString",
                                    "coordinates": list(map(flip_lat_long, leg["coordinates"]))}}
        features.append(leg_feature)
    exchanges = {}
    for leg in sorted(legs.values(), key=lambda x: x["start_exchange"]):
        exchanges[leg["start_exchange"]] = (leg["start_exchange"],
                                         leg["start_name"],
                                         leg["coordinates"][0])
        exchanges[leg["end_exchange"]] = (leg["end_exchange"],
                                       leg["end_name"],
                                       leg["coordinates"][-1])
    for id, exchange in sorted(exchanges.items()):
        exchange_feature = {"type": "Feature",
                            "properties": {"id": exchange[0],
                                           "name": exchange[1]},
                            "geometry": {"type": "Point",
                                         "coordinates": flip_lat_long(exchange[2])}}
        features.append(exchange_feature)
    return {"type": "FeatureCollection",
            "features": features}


def legs_to_facts(legs, distance_precision, duration_precision):
    facts = []
    Distance = DistanceK(distance_precision)
    for id, leg in legs.items():
        # For now we're assuming that routes apply in either direction
        facts.append(Distance(start_id=leg["start_exchange"], end_id=leg["end_exchange"], dist=leg["distance_mi"]))
        facts.append(Distance(start_id=leg["end_exchange"], end_id=leg["start_exchange"], dist=leg["distance_mi"]))
        facts.append(Ascent(start_id=leg["start_exchange"], end_id=leg["end_exchange"], ascent=round(leg["ascent_ft"])))
        facts.append(Descent(start_id=leg["start_exchange"], end_id=leg["end_exchange"], descent=round(leg["descent_ft"])))
        for attribute_name in leg["attributes"]:
            # Any special aspects of the leg which you may want to reason about can be shoved into attributes
            attribute_type = clorm.simple_predicate(attribute_name, 2)
            facts.append(attribute_type(clingo.Number(leg["start_exchange"]), clingo.Number(leg["end_exchange"])))
            facts.append(attribute_type(clingo.Number(leg["end_exchange"]), clingo.Number(leg["start_exchange"])))
    exchanges = set()
    exchange_coords = []
    for leg in legs.values():
        exchanges.add((leg["start_exchange"], leg["start_name"]))
        exchanges.add((leg["end_exchange"], leg["end_name"]))
        exchange_coords.append((leg["start_exchange"], leg["coordinates"][0]))
        exchange_coords.append((leg["end_exchange"], leg["coordinates"][-1]))

    # Remove duplicates
    exchange_coords_set = set()
    unique_tracker = set()
    for id, coord in exchange_coords:
        if id not in unique_tracker:
            unique_tracker.add(id)
            exchange_coords_set.add((id, coord))

    for id, exchange in exchanges:
        facts.append(ExchangeName(id=id, name=exchange))

    CommuteDistance = CommuteDistanceK(distance_precision)
    pairwise_distances = []
    for id1, coord1 in exchange_coords_set:
        for id2, coord2 in exchange_coords_set:
            if id1 < id2:
                pairwise_distances.append((id1, id2, haversine.haversine(coord1[:2], coord2[:2], unit=haversine.Unit.MILES)))
                facts.append(CommuteDistance(start_id=id1, end_id=id2, dist=pairwise_distances[-1][2]))
                facts.append(CommuteDistance(start_id=id2, end_id=id1, dist=pairwise_distances[-1][2]))
            if id1 == id2:
                facts.append(CommuteDistance(start_id=id1, end_id=id2, dist=0))
                facts.append(CommuteDistance(start_id=id2, end_id=id1, dist=0))
    return facts
