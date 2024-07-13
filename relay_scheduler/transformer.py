#!/usr/bin/env python3

import math

import clingo
import clingo.ast as ast

from clingo.ast import Transformer
from clingo.symbol import Number

from relay_scheduler.domain import duration, kPrecision


class FloatPaceTransformer(Transformer):
    """
    Transforms terms of the form term("1.5") into term(150), and term("1:30") into term(90).
    See also the `kPrecision` and `duration` functions in `relay_scheduler/domain.py`, which
    back the @-functions for manually applying these transforms within ASP files.
    """

    def __init__(self, distance_precision=2.0, duration_precision=0.0):
        self.distance_precision = distance_precision
        self.duration_precision = duration_precision

    def visit_SymbolicTerm(self, node):
        if node.symbol.type == clingo.SymbolType.String:
            if ":" in node.symbol.string:
                # Parse duration (e.g. 8:00 or 12:30)
                seconds = duration(node.symbol.string, self.duration_precision)
                return ast.SymbolicTerm(node.location, Number(seconds))
            try:
                as_float = float(node.symbol.string)
                as_int = kPrecision(as_float, self.distance_precision)
                return ast.SymbolicTerm(node.location, Number(as_int))
            except ValueError:
                return node
        return node