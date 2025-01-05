import glob
import logging
import time
from functools import cached_property

from clingo import parse_term, Model
from clingo.symbol import SymbolType, Function
from clingo.ast import ProgramBuilder, parse_files, SymbolicTerm, Location, Position
from clinguin.server.application.backends import ClingoBackend
from clinguin.utils.logger import domctl_log
from clinguin.server.data.domain_state import solve
from clorm import desc, FactBase
from clorm.clingo import Control


from relay_scheduler.domain import LegCoverage, Leg, LegDistK, DistanceK, PreferredPaceK, CommuteDistanceK, \
    PreferredEndExchange, Ascent, Descent, PreferredDistanceK, LegDescent, LegPaceK, LegAscent, Objective, LeaderOn, \
    ExchangeName, Run, make_standard_func_ctx
from relay_scheduler.transformer import FloatPaceTransformer


def build_ctrl(args):
    # Clorm's `Control` wrapper will try to parse model facts into the predicates defined in domain.py.
    ctrl = Control(
        unifier=[LegCoverage, LegPaceK(args.duration_precision), Run, LegDistK(args.distance_precision), ExchangeName,
                 Leg,
                 LegDistK(args.distance_precision), LegAscent, LegDescent, Objective, LeaderOn,
                 DistanceK(args.distance_precision), Ascent, Descent, PreferredDistanceK(args.distance_precision),
                 PreferredPaceK(args.duration_precision), PreferredEndExchange,
                 CommuteDistanceK(args.distance_precision)])
    # Makes exceptions inscrutable. Disable if you need to debug
    if args.jobs > 1:
        ctrl.configuration.solve.parallel_mode = f"{args.jobs},split"
    ctrl.configuration.solve.opt_mode = "optN"
    with ProgramBuilder(ctrl) as b:
        t = FloatPaceTransformer(args.distance_precision)
        # All ASP files in the year directory
        year_files = glob.glob(f"{args.event}/*.lp")
        parse_files(
            ["scheduling-domain.lp"] + year_files,
            lambda stm: b.add(t.visit(stm)))
    return ctrl

class WebBackend(ClingoBackend):
    def _create_ctl(self) -> None:
        self._logger.setLevel(logging.DEBUG)

        self._ctl = Control()

    def _ground(self, program="base", arguments=None):
        arguments = arguments or []
        arguments = [arguments] if not isinstance(arguments, list) else arguments
        self._logger.debug(domctl_log(f"domctl.ground([({program}, {arguments})])"))
        arguments_symbols = [parse_term(a) for a in arguments]
        self._ctl.ground([(program, arguments_symbols)], context=make_standard_func_ctx())

    def next_solution(self, opt_mode="ignore"):
        """
        Obtains the next solution. If a no browsing has been started yet, then it calls solve,
        otherwise it iterates the models in the last call. To keep the atoms shown in the solution, use :func:`~select`.

        Arguments:
            opt_mode: The clingo optimization mode, bu default is 'ignore', to browse only optimal models use 'optN'
        """
        def _on_model(model):
            self._on_model(model)

            if optimizing and len(model.cost) == 0:
                self._messages.append(
                    (
                        "Browsing Warning",
                        "No optimization provided",
                        "warning",
                    )
                )
                self._logger.warning(
                    "No optimization statement provided in encoding but optimization condition provided\
                        in 'next_solution' operation. Exiting browsing."
                )
            else:
                self._updated_model = model.symbols(shown=True, atoms=True, theory=True)

        if self._ctl.configuration.solve.opt_mode != opt_mode:
            self._logger.debug("Ended browsing since opt mode changed")
            self._outdate()

        self._clear_cache(["_ds_model"])
        optimizing = opt_mode in ["optN", "opt"]
        if self._handler is None:
            self._logger.info("Making new handler")
            self._logger.debug(
                domctl_log(f"domctl.configuration.solve.opt_mode = {opt_mode}")
            )
            self._ctl.configuration.solve.enum_mode = "auto"
            self._ctl.configuration.solve.opt_mode = opt_mode
            self._ctl.configuration.solve.models = 0

            self._prepare()
            self._logger.debug(
                domctl_log(
                    f"domctl.solve({[(str(a), b) for a, b in self._assumption_list]}, yield_=True)"
                )
            )
            self._updated_model = None
            self._handler = self._ctl.solve(self._assumption_list, on_model=_on_model, async_=True)

        elif self._updated_model is None:
            self._logger.info("No better solutions")
            # self._outdate()
            # self._messages.append(("Browsing Information", "No better solutions", "info"))
        else:
            self._model = self._updated_model

    @cached_property
    def _ds_model(self):
        """
        Computes model and adds all atoms as facts.
        When the model is being iterated by the user, the current model is returned.
        It will use as optimality the mode set in the command line as `default-opt-mode` (`ignore` by default).

        It uses a cache that is erased after an operation makes changes in the control.
        """
        if self._model is None:
            if self._handler is not None:
                self._handler.wait(1)
                if self._model is not None:
                    return " ".join([str(s) + "." for s in self._model]) + "\n"
                else:
                    self._unsat_core = self._handler.core()
                    self._logger.warning(
                        "Got an UNSAT result with the given domain encoding."
                    )
                    self._messages.append(("Warning", "The current assumptions are unsatisfiable.", "info"))
                    return (
                        self._backup_ds_cache["_ds_model"]
                        + "\n".join([str(a) + "." for a in self._atoms])
                        if "_ds_model" in self._backup_ds_cache
                        else ""
                    )

            self._logger.debug(
                domctl_log('domctl.configuration.solve.enum_mode = "auto"')
            )
            self._ctl.configuration.solve.models = 1
            self._ctl.configuration.solve.opt_mode = self._default_opt_mode
            self._ctl.configuration.solve.enum_mode = "auto"

            self._prepare()
            self._logger.debug(
                domctl_log(
                    f"domctl.solve({[(str(a),b) for a,b in self._assumption_list]}, yield_=True)"
                )
            )

            symbols, ucore = solve(self._ctl, self._assumption_list, self._on_model)
            self._unsat_core = ucore
            if symbols is None:
                self._logger.warning(
                    "Got an UNSAT result with the given domain encoding."
                )
                return (
                    self._backup_ds_cache["_ds_model"]
                    + "\n".join([str(a) + "." for a in self._atoms])
                    if "_ds_model" in self._backup_ds_cache
                    else ""
                )
            self._model = symbols

        return " ".join([str(s) + "." for s in self._model]) + "\n"

    def add_atom_transform(self, predicate):
        """
        Adds an atom, restarts the control and grounds

        Arguments:

            predicate (str): The clingo symbol to be added
        """
        t = FloatPaceTransformer()
        pos = Position('<string>', 1, 1)
        loc = Location(pos, pos)
        predicate_symbol = parse_term(predicate)
        if predicate_symbol.type == SymbolType.Function:
            arguments = []
            for argument in predicate_symbol.arguments:
                arguments.append(t.visit(SymbolicTerm(loc, argument)).symbol)
            predicate_symbol = Function(predicate_symbol.name, arguments, predicate_symbol.positive)
        if predicate_symbol not in self._atoms:
            self._add_atom(predicate_symbol)
            self._init_ctl()
            self._ground()
            self._outdate()