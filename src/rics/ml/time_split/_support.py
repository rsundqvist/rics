from typing import Protocol, TypeVar, runtime_checkable

T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class _Computable(Protocol[T_co]):
    def compute(self) -> T_co:
        """Compute results of a delayed Dask object."""


def handle_dask(arg: T_co | _Computable[T_co]) -> T_co:
    """Run Dask compute function on a delayed object."""
    return arg.compute() if isinstance(arg, _Computable) else arg
