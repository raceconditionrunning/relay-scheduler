#script (python)

import clingo
import clingo.ast
from clingo.symbol import String, Number
from clingo.ast import ProgramBuilder, parse_files, Transformer
from collections import defaultdict
import math

class TermTransformer(Transformer):
    def __init__(self, parameter):
        self.parameter = parameter

    def visit_Function(self, node):
        new_args = []
        for arg in node.arguments:
            if arg.ast_type == clingo.ast.ASTType.SymbolicTerm and arg.symbol.type == clingo.SymbolType.String:
                try:
                    as_float = float(arg.symbol.string)
                    as_int = int(as_float * 100.0)
                    new_args.append(clingo.ast.SymbolicTerm(node.location, Number(as_int)))
                except ValueError:
                    new_args.append(arg)
            else:
                new_args.append(arg)

        return node.update(arguments=new_args)


def print_model(model):
    # TODO(nickswalker): Use clorm to make this nicer
    leg_start = {}
    leg_end = {}
    assignments = {}
    leg_paces = {}
    leg_coverages = {}
    on_leg = defaultdict(list)
    station_names = {}
    individual_dist_dev = {}
    individual_pace_dev = defaultdict(list)
    individual_end_dev = {}
    leg_dist = {}
    total_dist = {}
    for symbol in model.symbols(atoms=True):
        if symbol.name == "leg_coverage":
            leg_num, coverage = symbol.arguments
            leg_num = leg_num.number
            coverage = coverage.number
            leg_coverages[leg_num] = coverage
        elif symbol.name == "leg_pace":
            leg_num, pace = symbol.arguments
            leg_num = leg_num.number
            pace = pace.number / 100.0
            #pace = f"{pace // 1:0.0f}:{(pace % 1.0) * 60:02.0f}"
            leg_paces[leg_num] = pace
        elif symbol.name == "assignment":
            runner, start, end = symbol.arguments
            runner = runner.string
            start = start.string
            end = end.string
            assignments[runner] = (start, end)
        elif symbol.name == "run":
            person, leg = symbol.arguments
            person = person.string
            leg = leg.number
            on_leg[leg].append(person)
        elif symbol.name == "s_name":
            number, name = symbol.arguments
            number = number.number
            name = name.string
            station_names[number] = name
        elif symbol.name == "leg":
            number, start, end = symbol.arguments
            leg_start[number.number] = start.number
            leg_end[number.number] = end.number
        elif symbol.name == "dist_diff":
            name, deviation = symbol.arguments
            name = name.string
            deviation = deviation.number / 100.0
            individual_dist_dev[name] = deviation
        elif symbol.name == "end_deviation":
            name, deviation = symbol.arguments
            name = name.string
            individual_end_dev[name] = deviation.number
        elif symbol.name == "pace_slack":
            name, leg, deviation = symbol.arguments
            name = name.string
            deviation = deviation.number / 100.0
            formatted = f"{deviation // 1:0.0f}:{(deviation % 1.0) * 60:02.0f}"
            individual_pace_dev[name].append(formatted)
        elif symbol.name == "leg_dist":
            leg, dist = symbol.arguments
            leg_dist[leg.number] = dist.number / 100.0
        elif symbol.name == "total_dist":
            name, dist = symbol.arguments
            total_dist[name.string] = dist.number / 100.0

    runner_names = sorted(assignments.keys())
    for runner in runner_names:
        start, end = assignments[runner]

        print(f"{runner}: {start} -> {end} - {total_dist[runner]} mi")


    for runner in runner_names:
        pace_dev = individual_pace_dev[runner]

        print(f"{runner}: {individual_dist_dev[runner]} mi, {pace_dev}, {individual_end_dev[runner]} stations")


    leg_keys = sorted(leg_paces.keys())
    start_offset = 0.0
    exchange_overhead = 3.5
    for leg_num in leg_keys:
        station_start, station_end = leg_start[leg_num], leg_end[leg_num]
        start_name = station_names[station_start]
        end_name = station_names[station_end]
        pace = leg_paces[leg_num]
        pace_pretty = f"{pace // 1:0.0f}:{(pace % 1.0) * 60:02.0f}"
        offset_pretty = f"{(start_offset / 60) // 1:0.0f}:{(start_offset % 60) // 1:02.0f}:{(start_offset % 1.0) * 60:02.0f}"
        dist = leg_dist[leg_num]
        print(f"{leg_num} T+{offset_pretty} {start_name} -> {end_name}: {dist}mi@{pace_pretty} {sorted(on_leg[leg_num])}")
        leg_duration = pace * dist

        start_offset += math.ceil(exchange_overhead + leg_duration)
        # print(pace, dist, leg_duration, start_offset)
    offset_pretty = f"{(start_offset / 60) // 1:0.0f}:{(start_offset % 60) // 1:02.0f}:{(start_offset % 1.0) * 60:02.0f}"
    print(f"END T+{offset_pretty}")

def main(prg):
    t = TermTransformer(clingo.Function("k"))

    with ProgramBuilder(prg) as b:
        parse_files(
        ["scheduling-domain.lp", "lrr-2021.lp", "link-1-line.lp", "pin-legs.lp"],
        lambda stm: b.add(t.visit(stm)))
        prg.ground([("base", [])])
    prg.solve(on_model=print_model)

#end.
