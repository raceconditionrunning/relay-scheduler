import math

from clorm import Predicate, IntegerField, StringField, \
    ContextBuilder


def make_standard_func_ctx():
    cb = ContextBuilder()

    cb.register_name("min", IntegerField, IntegerField, IntegerField, min)
    cb.register_name("max", IntegerField, IntegerField, IntegerField, max)

    return cb.make_context()

def DistanceFieldK(precision=2.0):
    class DistanceField(IntegerField):
        # We represent distances with a fixed precision, 2 decimal places by default. We want
        # conservative approximations of time, so always round up
        pytocl = lambda miles: math.ceil(miles * 10 ** precision)
        cltopy = lambda miles: miles / 10 ** precision

    return DistanceField


def DistanceK(precision=2.0):
    class Distance(Predicate):
        start_id = IntegerField
        end_id = IntegerField
        dist = DistanceFieldK(precision=precision)

    return Distance


def CommuteDistanceK(precision=2.0):
    class CommuteDistance(Predicate):
        start_id = IntegerField
        end_id = IntegerField
        dist = DistanceFieldK(precision=precision)

    return CommuteDistance


def PreferredDistanceK(precision=2.0):
    class PreferredDistance(Predicate):
        name = StringField
        distance = DistanceFieldK(precision=precision)

    return PreferredDistance


class PreferredPace(Predicate):
    name = StringField
    pace = IntegerField


class Ascent(Predicate):
    start_id = IntegerField
    end_id = IntegerField
    ascent = IntegerField


class Descent(Predicate):
    start_id = IntegerField
    end_id = IntegerField
    descent = IntegerField


class LegCoverage(Predicate):
    leg = IntegerField
    coverage = IntegerField


class LegPace(Predicate):
    leg = IntegerField
    pace = IntegerField


class Run(Predicate):
    runner = StringField
    leg_id = IntegerField


class LeaderOn(Predicate):
    runner = StringField
    leg_id = IntegerField


def LegDistK(precision=2.0):
    class LegDist(Predicate):
        leg = IntegerField
        dist = DistanceFieldK(precision=precision)

    return LegDist


class ExchangeName(Predicate):
    id = IntegerField
    name = StringField


class Leg(Predicate):
    id = IntegerField
    start_id = IntegerField
    end_id = IntegerField


def EndDeviationK(precision=2.0):
    class EndDeviation(Predicate):
        name = StringField
        deviation = DistanceFieldK(precision=precision)

    return EndDeviation

def TotalDistK(precision=2.0):
    class TotalDist(Predicate):
        name = StringField
        dist = DistanceFieldK(precision=precision)

    return TotalDist


class TotalAscent(Predicate):
    name = StringField
    ascent = IntegerField


class TotalDescent(Predicate):
    name = StringField
    descent = IntegerField


class LegAscent(Predicate):
    leg = IntegerField
    ascent = IntegerField


class LegDescent(Predicate):
    leg = IntegerField
    descent = IntegerField


class Objective(Predicate):
    index = IntegerField
    name = StringField
