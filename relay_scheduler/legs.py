import json
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

    # Load rich exchange metadata if exchanges.geojson exists
    exchanges_data = None
    exchanges_file = os.path.join(dir_path, "exchanges.geojson")
    if os.path.exists(exchanges_file):
        with open(exchanges_file) as f:
            exchanges_geojson = json.load(f)
            exchanges_data = {
                feature["properties"]["id"]: {
                    **feature["properties"],
                    "coordinates": feature["geometry"]["coordinates"]
                }
                for feature in exchanges_geojson["features"]
            }

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

        waypoints = gpx_data.xpath("//gpx:wpt", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
        pois = []
        for waypoint in waypoints:
            poi = {
                'lat': float(waypoint.attrib["lat"]),
                'lon': float(waypoint.attrib["lon"])
            }

            elevation_elem = waypoint.xpath("gpx:ele", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
            if elevation_elem:
                poi['elevation'] = float(elevation_elem[0].text)

            name_elem = waypoint.xpath("gpx:name", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
            if name_elem:
                poi['name'] = name_elem[0].text

            comment_elem = waypoint.xpath("gpx:cmt", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
            if comment_elem:
                poi['comment'] = comment_elem[0].text

            desc_elem = waypoint.xpath("gpx:desc", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
            if desc_elem:
                poi['description'] = desc_elem[0].text

            sym_elem = waypoint.xpath("gpx:sym", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
            if sym_elem:
                poi['symbol'] = sym_elem[0].text

            pois.append(poi)
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

        time_elem = gpx_data.xpath("//gpx:metadata/gpx:time", namespaces={"gpx": "http://www.topografix.com/GPX/1/1"})
        time = None
        if time_elem:
            time = time_elem[0].text
        leg = {'distance_mi': distance,
               'ascent_ft': ascent,
               'descent_ft': descent,
               'start_exchange': int(start_id),
                'end_exchange': int(end_id),
               'notes': description,
               'start_name': start_name,
                'end_name': end_name,
               'coordinates': coordinates,
               'attributes': attributes,
               'pois': pois,
               'time': time
               }
        legs[(int(start_id), int(end_id))] = leg

    return legs, exchanges_data


def flip_lat_long(lat_long_ele_point):
    return (lat_long_ele_point[1], lat_long_ele_point[0], lat_long_ele_point[2])


def relay_to_geojson(legs, sequences=None, exchanges_data=None, exclude_exchanges=None):
    if exclude_exchanges is None:
        exclude_exchanges = set()
    else:
        exclude_exchanges = set(exclude_exchanges)

    if sequences is None:
        # Generate default sequential sequences in lexicographic order, excluding legs with excluded exchanges
        filtered_legs = {pair: leg for pair, leg in legs.items() 
                        if pair[0] not in exclude_exchanges and pair[1] not in exclude_exchanges}
        sequences = {pair: [i] for i, pair in enumerate(reversed(sorted(filtered_legs.keys())))}

    features = []
    for leg in legs.values():
        # Skip legs that touch excluded exchanges
        if leg["start_exchange"] in exclude_exchanges or leg["end_exchange"] in exclude_exchanges:
            continue
        leg_without_coordinates = {k: v for k, v in leg.items() if k not in ["coordinates", "pois"]}
        # Float props likely have too much precision. Round them to 2 decimal places
        for k, v in leg_without_coordinates.items():
            if isinstance(v, float):
                leg_without_coordinates[k] = round(v, 2)
        exchange_pair = (leg["start_exchange"], leg["end_exchange"])
        if exchange_pair not in sequences:
            # We must not be running this leg
            continue
        leg_without_coordinates["sequence"] = sequences[exchange_pair]
        leg_feature = {"type": "Feature",
                       "properties": leg_without_coordinates,
                       "geometry": {"type": "LineString",
                                    "coordinates": list(map(flip_lat_long, leg["coordinates"]))}}
        features.append(leg_feature)

        # Add POIs for this leg
        for poi in leg.get("pois", []):
            poi_properties = poi.copy()
            poi_properties["leg_start_exchange"] = leg["start_exchange"]
            poi_properties["leg_end_exchange"] = leg["end_exchange"]
            poi_properties["leg_sequence"] = sequences[exchange_pair]
            poi_properties["feature_type"] = "poi"
            poi_properties["time"] = leg["time"]

            # Round elevation if present
            if "elevation" in poi_properties and isinstance(poi_properties["elevation"], float):
                poi_properties["elevation"] = round(poi_properties["elevation"], 2)

            poi_feature = {"type": "Feature",
                          "properties": poi_properties,
                          "geometry": {"type": "Point",
                                      "coordinates": [poi["lon"], poi["lat"]]}}
            features.append(poi_feature)
    features = sorted(features, key=lambda x: x["properties"].get("sequence", x["properties"].get("leg_sequence", [999]))[0])

    # Pull exchanges implied by the legs
    exchanges = {}
    for feature in features:
        leg = feature["properties"]
        coordinates = feature["geometry"]["coordinates"]
        # Only process LineString features (legs), not Points (POIs or exchanges)
        if feature["geometry"]["type"] == "LineString" and "start_exchange" in leg:
            start_id = leg["start_exchange"]
            end_id = leg["end_exchange"]

            # Use rich exchange data if available, otherwise use inferred data
            if exchanges_data and start_id in exchanges_data:
                exchanges[start_id] = exchanges_data[start_id].copy()
            else:
                exchanges[start_id] = {"id": start_id,
                                     "name": leg["start_name"],
                                     "coordinates": coordinates[0]}

            if exchanges_data and end_id in exchanges_data:
                exchanges[end_id] = exchanges_data[end_id].copy()
            else:
                exchanges[end_id] = {"id": end_id,
                                   "name": leg["end_name"],
                                   "coordinates": coordinates[-1]}

    # Filter out excluded exchanges
    for exchange_id in list(exchanges.keys()):
        if exchange_id in exclude_exchanges:
            del exchanges[exchange_id]

    for id, exchange in sorted(exchanges.items()):
        exchange_feature = {"type": "Feature",
                            "properties": {k: v for k, v in exchange.items() if k != "coordinates"},
                            "geometry": {"type": "Point",
                                         "coordinates": exchange["coordinates"]}}
        features.append(exchange_feature)
    # Add a unique ID to each feature, but preserve exchange IDs
    feature_id = 0
    for feature in features:
        # Don't overwrite exchange IDs - they're meaningful station codes
        if "id" not in feature["properties"]:
            feature["properties"]["id"] = feature_id
            feature_id += 1
    return {"type": "FeatureCollection",
            "features": features}


def dump_geojson_with_compact_geometry(geojson, f):
    f.write('{"type":"FeatureCollection","features":[\n')

    for i, feature in enumerate(geojson['features']):
        # Create a copy of the feature without the geometry
        feature_copy = feature.copy()
        geometry = feature_copy.pop('geometry')

        # Dump the feature without geometry
        f.write(json.dumps(feature_copy, indent=2)[:-2])  # Remove the closing `}` of the feature

        # Add the compact geometry inside the feature
        compact_geometry = json.dumps(geometry, separators=(',', ':'))
        f.write(f', "geometry":{compact_geometry}\n}}')

        # Handle commas between features
        if i < len(geojson['features']) - 1:
            f.write(',\n')
        else:
            f.write('\n')

    f.write(']}\n')


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
