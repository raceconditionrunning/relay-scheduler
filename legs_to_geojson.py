#!/usr/bin/env python3

import argparse
import os

from relay_scheduler.legs import load_from_legs_bundle, relay_to_geojson, dump_geojson_with_compact_geometry


def main():
    parser = argparse.ArgumentParser(description="Convert GPX legs directory to GeoJSON")
    parser.add_argument("legs_dir", help="Path to directory containing GPX files")
    parser.add_argument("-o", "--output", help="Output GeoJSON file (default: stdout)")
    parser.add_argument("--exclude-exchanges", nargs="+", type=int, metavar="ID", 
                       help="Exclude exchanges by ID (and any legs touching them)")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.legs_dir):
        print(f"Error: {args.legs_dir} is not a directory")
        return 1
    
    legs, exchanges_data = load_from_legs_bundle(args.legs_dir)
    geojson = relay_to_geojson(legs, exchanges_data=exchanges_data, 
                              exclude_exchanges=args.exclude_exchanges)
    
    if args.output:
        with open(args.output, 'w') as f:
            dump_geojson_with_compact_geometry(geojson, f)
        print(f"GeoJSON written to {args.output}")
    else:
        import json
        print(json.dumps(geojson, indent=2))
    
    return 0


if __name__ == "__main__":
    exit(main())