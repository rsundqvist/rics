import logging
from collections.abc import Collection, Iterator
from inspect import Parameter, signature
from typing import Any, Generic

from rics.misc import tname
from rics.strings import ReprFormatter

from .types import DataFunc, DataType, Ts


class GeneratedData(Generic[DataType, *Ts]):
    def __init__(
        self,
        func: DataFunc[*Ts, DataType],
        case_args: Collection[tuple[*Ts]] | None,
        kwargs: dict[str, Any] | None,
        logger: logging.Logger | logging.LoggerAdapter[Any],
    ) -> None:
        if not case_args:
            raise ValueError("No case data given.")
        cases = [*case_args]
        if len(cases) != len({*cases}):
            raise ValueError("Cases are not unique.")

        self._func = func
        self._cases = cases
        self._kwargs = kwargs or {}

        if hasattr(logger, "getChild"):
            logger = logger.getChild("data")

        self._logger = logger
        self._logger_enabled = logger.isEnabledFor(logging.DEBUG)

    def derive_names(self) -> list[str]:
        case_args = self._cases
        n = len(case_args[0])
        parameters = [
            name
            for name, parameter in signature(self._func).parameters.items()
            if parameter.kind in {Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD}
        ]
        if len(parameters) < n:
            msg = (
                f"Could not derive names for test_data="
                f"{tname(self._func, prefix_classname=True)}({', '.join(parameters)}, ...)."
                f" Expected at least {n} positional parameters since {case_args[0]=}."
                f" Got {len(parameters)}: {parameters}."
            )
            raise RuntimeError(msg)
        return parameters[:n]

    def __len__(self) -> int:
        return len(self._cases)

    def __iter__(self) -> Iterator[tuple[*Ts]]:
        return iter(self._cases)

    def generate(self, case: tuple[*Ts]) -> DataType:
        """Generate the data for a single `case` on demand, without materializing the other cases.

        Used by calibration so that probing one variant keeps a single dataset in memory at a time.
        """
        return self._func(*case, **self._kwargs)

    def items(self) -> Iterator[tuple[tuple[*Ts], DataType]]:
        func = self._func

        for n, case in enumerate(self._cases, start=1):
            data = self.generate(case)

            if self._logger_enabled:
                formatter = ReprFormatter()
                items = [
                    *map(formatter.format_value, case),
                    *(f"{k}={formatter.format_value(v)}" for k, v in self._kwargs.items()),
                ]
                args = ", ".join(items)
                self._logger.debug(
                    f"Yield case {n}/{len(self._cases)}: "
                    f"{tname(func, prefix_classname=True)}({args})={tname(data, prefix_classname=True)}.",
                )

            yield case, data
