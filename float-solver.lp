#script (python)

import clingo
import clingo.ast
from clingo.symbol import String, Number
from clingo.ast import ProgramBuilder, parse_files, Transformer


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



def main(prg):
    t = TermTransformer(clingo.Function("k"))

    with ProgramBuilder(prg) as b:
        parse_files(
        ["schedule.lp", "map.lp", "preferences.lp"],
        lambda stm: b.add(t.visit(stm)))
        prg.ground([("base", [])])
    prg.solve()

#end.