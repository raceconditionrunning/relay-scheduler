import math
from functools import cache

from clorm import Predicate, IntegerField, StringField, \
    ContextBuilder


def kPrecision(val, precision):
    return math.ceil(val * 10 ** float(precision))


def duration(val, precision):
    return kPrecision(sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(val.split(":")))), precision)


def make_standard_func_ctx():
    """
    Functions that are callable using `@` from ASP files.
    """
    cb = ContextBuilder()

    cb.register_name("min", IntegerField, IntegerField, IntegerField, min)
    cb.register_name("max", IntegerField, IntegerField, IntegerField, max)
    cb.register_name("k", IntegerField, StringField, IntegerField, kPrecision)
    cb.register_name("duration", StringField, StringField, IntegerField, kPrecision)

    return cb.make_context()


@cache
def IntegerFieldK(precision=2.0):
    class IntegerFieldK(IntegerField):
        # Represents a number to a fixed precision, 2 decimal places by default. We want
        # conservative approximations, so always round up
        pytocl = lambda val: kPrecision(val, precision)
        cltopy = lambda val: val / 10 ** precision

    return IntegerFieldK


@cache
def DistanceK(precision=2.0):
    class Distance(Predicate):
        start_id = IntegerField
        end_id = IntegerField
        dist = IntegerFieldK(precision=precision)

    return Distance


@cache
def CommuteDistanceK(precision=2.0):
    class CommuteDistance(Predicate):
        start_id = IntegerField
        end_id = IntegerField
        dist = IntegerFieldK(precision=precision)

    return CommuteDistance


class Participant(Predicate):
    name = StringField

@cache
def PreferredDistanceK(precision=2.0):
    class PreferredDistance(Predicate):
        name = StringField
        distance = IntegerFieldK(precision=precision)

    return PreferredDistance


@cache
def PreferredPaceK(precision=0.0):
    class PreferredPace(Predicate):
        name = StringField
        pace = IntegerFieldK(precision)

    return PreferredPace

@cache
def PreferredAscentK(precision=0.0):
    class PreferredAscent(Predicate):
        name = StringField
        ascent = IntegerFieldK(precision)

    return PreferredAscent

@cache
def PreferredDescentK(precision=0.0):
    class PreferredDescent(Predicate):
        name = StringField
        descent = IntegerFieldK(precision)

    return PreferredDescent


class PreferredEndExchange(Predicate):
    name = StringField
    exchange_id = IntegerField


class WillingToLead(Predicate):
    name = StringField


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


@cache
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


@cache
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


class LegAscent(Predicate):
    leg = IntegerField
    ascent = IntegerField


class LegDescent(Predicate):
    leg = IntegerField
    descent = IntegerField


class Objective(Predicate):
    index = IntegerField
    name = StringField


class DistancePrecision(Predicate):
    """
    Solver adds this to the domain so that facts from files can be written to use solve-time precision.
    """
    precision = StringField


class DurationPrecision(Predicate):
    """
    Solver adds this to the domain so that facts from files can be written to use solve-time precision.
    """
    precision = StringField

