import math

from clorm import Predicate, IntegerField, StringField, \
    ContextBuilder


def make_standard_func_ctx():
    cb = ContextBuilder()

    cb.register_name("min", IntegerField, IntegerField, IntegerField, min)
    cb.register_name("max", IntegerField, IntegerField, IntegerField, max)

    return cb.make_context()

def IntegerFieldK(precision=2.0):
    class IntegerFieldK(IntegerField):
        # Represents a number to a fixed precision, 2 decimal places by default. We want
        # conservative approximations, so always round up
        pytocl = lambda val: math.ceil(val * 10 ** precision)
        cltopy = lambda val: val / 10 ** precision

    return IntegerFieldK


def DistanceK(precision=2.0):
    class Distance(Predicate):
        start_id = IntegerField
        end_id = IntegerField
        dist = IntegerFieldK(precision=precision)

    return Distance


def CommuteDistanceK(precision=2.0):
    class CommuteDistance(Predicate):
        start_id = IntegerField
        end_id = IntegerField
        dist = IntegerFieldK(precision=precision)

    return CommuteDistance


def PreferredDistanceK(precision=2.0):
    class PreferredDistance(Predicate):
        name = StringField
        distance = IntegerFieldK(precision=precision)

    return PreferredDistance


def PreferredPaceK(precision=0.0):
    class PreferredPace(Predicate):
        name = StringField
        pace = IntegerFieldK(precision)

    return PreferredPace


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


def LegPaceK(precision):
    class LegPace(Predicate):
        leg = IntegerField
        pace = IntegerFieldK(precision)
    return LegPace


class Run(Predicate):
    runner = StringField
    leg_id = IntegerField


class LeaderOn(Predicate):
    runner = StringField
    leg_id = IntegerField


def LegDistK(precision=2.0):
    class LegDist(Predicate):
        leg = IntegerField
        dist = IntegerFieldK(precision=precision)

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
        deviation = IntegerFieldK(precision=precision)

    return EndDeviation

def TotalDistK(precision=2.0):
    class TotalDist(Predicate):
        name = StringField
        dist = IntegerFieldK(precision=precision)

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
