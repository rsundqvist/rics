from typing import Type

from rics.translation.dio import DataStructureIO
from rics.translation.dio._dict import DictIO
from rics.translation.dio._pandas import PandasIO
from rics.translation.dio._sequence import SequenceIO
from rics.translation.dio._single_value import SingleValueIO
from rics.translation.dio.exceptions import UntranslatableTypeError
from rics.translation.types import Translatable


def resolve_io(arg: Translatable) -> Type[DataStructureIO]:
    """Get an IO instance for `arg`.

    Args:
        arg: An argument to get IO for.

    Returns:
        A data structure IO instance for `arg`.

    Raises:
        UntranslatableTypeError: If not IO could be found.
    """
    for tio_class in DictIO, PandasIO, SequenceIO, SingleValueIO:
        if tio_class.handles_type(arg):
            return tio_class

    raise UntranslatableTypeError(type(arg))
