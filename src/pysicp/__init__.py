"""PySICP.

Support for the Python translation of *Structure and Interpretation of
Computer Programs*.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, NoReturn

__version__ = "0.1.0"

__all__ = ["TailCall", "tail_recursive"]

_ESCAPED = (
    "a TailCall was used as if it were a value. This happens when the "
    "recursive call is not in tail position -- that is, when the procedure "
    "does something with the result before returning it. Only a call whose "
    "value is returned unchanged may be deferred with TailCall."
)


class TailCall:
    """A call to be made next, in place of the one now returning.

    Return one of these from a procedure decorated with `tail_recursive`
    instead of calling the procedure directly::

        @tail_recursive
        def fact_iter(n, product=1):
            if n == 0:
                return product
            return TailCall(fact_iter, n - 1, n * product)

    The procedure named may be the one returning it or another one, so long as
    that procedure is itself decorated.
    """

    __slots__ = ("procedure", "args", "kwargs")

    def __init__(
        self, procedure: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        # A decorated procedure is unwrapped to the procedure it decorates, so
        # that making the call does not start a second driver on top of the one
        # already running. Without this, each hand-off between two mutually
        # recursive procedures would cost a frame and the stack would grow
        # after all.
        self.procedure = getattr(procedure, "__wrapped__", procedure)
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:
        name = getattr(self.procedure, "__name__", repr(self.procedure))
        return f"<TailCall {name}>"

    # A TailCall is not a value, and saying so early is the whole point of
    # these: an escaped one would otherwise be absorbed into an answer -- added
    # to a number, put in a list, tested for truth -- and the mistake would
    # surface far from its cause, or not at all.
    def _escaped(self, *_: object, **__: object) -> NoReturn:
        raise TypeError(_ESCAPED)

    __bool__ = _escaped
    __iter__ = _escaped
    __len__ = _escaped
    __getattr__ = _escaped
    __call__ = _escaped
    __index__ = _escaped
    __int__ = _escaped
    __float__ = _escaped
    __str__ = _escaped
    __hash__ = _escaped
    __eq__ = _escaped
    __ne__ = _escaped
    __lt__ = _escaped
    __le__ = _escaped
    __gt__ = _escaped
    __ge__ = _escaped
    __add__ = __radd__ = _escaped
    __sub__ = __rsub__ = _escaped
    __mul__ = __rmul__ = _escaped
    __truediv__ = __rtruediv__ = _escaped
    __floordiv__ = __rfloordiv__ = _escaped
    __mod__ = __rmod__ = _escaped
    __pow__ = __rpow__ = _escaped
    __neg__ = __pos__ = _escaped
    __getitem__ = _escaped
    __contains__ = _escaped


def tail_recursive[**P, R](procedure: Callable[P, R]) -> Callable[P, R]:
    """Run a procedure that defers its recursive calls, in constant space.

    Python does not eliminate tail calls, so a procedure that describes an
    iterative process still consumes a frame for every step and will exhaust
    the stack. Decorate it with this, and return `TailCall(...)` where it would
    have called itself, and the process runs at a fixed depth however many
    steps it takes::

        @tail_recursive
        def sum_to(n, acc=0):
            if n == 0:
                return acc
            return TailCall(sum_to, n - 1, acc + n)

        sum_to(1_000_000)

    Only a call whose value is returned unchanged may be deferred. A procedure
    that must do something with the result -- `return n * fact(n - 1)` --
    describes a recursive process, not an iterative one, and there is nothing
    here for this to do.
    """

    @wraps(procedure)
    def run(*args: P.args, **kwargs: P.kwargs) -> R:
        result: Any = procedure(*args, **kwargs)
        while type(result) is TailCall:
            result = result.procedure(*result.args, **result.kwargs)
        return result  # type: ignore[no-any-return]

    return run
