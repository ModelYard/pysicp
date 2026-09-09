"""Tests for the tail-recursive driver.

The property under test is a space property, so most of these are about what
does NOT happen: the stack does not grow, a hundred thousand steps do not
exhaust it, and a deferred call that escapes does not quietly become part of an
answer.
"""

import sys
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from pysicp import TailCall, tail_recursive


def stack_depth() -> int:
    """How many frames are currently on the stack."""
    depth, frame = 0, sys._getframe()
    while frame is not None:
        depth += 1
        frame = frame.f_back
    return depth


# --- correctness -----------------------------------------------------------


def test_computes_the_right_answer() -> None:
    @tail_recursive
    def fact_iter(n: int, product: int = 1) -> int:
        if n == 0:
            return product
        return TailCall(fact_iter, n - 1, n * product)

    assert fact_iter(6) == 720


def test_a_procedure_that_never_defers_behaves_ordinarily() -> None:
    @tail_recursive
    def square(x: int) -> int:
        return x * x

    assert square(7) == 49


def test_keyword_arguments_reach_the_next_step() -> None:
    @tail_recursive
    def countdown(n: int, *, acc: int = 0) -> int:
        if n == 0:
            return acc
        return TailCall(countdown, n - 1, acc=acc + n)

    assert countdown(4) == 10


# --- space, which is the reason the driver exists --------------------------


@contextmanager
def recursion_limit(headroom: int) -> Iterator[None]:
    """Allow only `headroom` further frames, whatever the ambient limit is.

    Pinning it matters: with a raised limit -- which a plugin or another test
    may well have set -- deep plain recursion simply succeeds, and a test that
    expects it to fail would fail instead, for a reason nowhere near the code
    under test.
    """
    depth, frame = 0, sys._getframe()
    while frame is not None:
        depth += 1
        frame = frame.f_back

    previous = sys.getrecursionlimit()
    sys.setrecursionlimit(depth + headroom)
    try:
        yield
    finally:
        sys.setrecursionlimit(previous)


def test_a_long_process_completes_where_plain_recursion_cannot() -> None:
    steps = 100_000

    @tail_recursive
    def sum_to(n: int, acc: int = 0) -> int:
        if n == 0:
            return acc
        return TailCall(sum_to, n - 1, acc + n)

    def plain_sum_to(n: int, acc: int = 0) -> int:
        if n == 0:
            return acc
        return plain_sum_to(n - 1, acc + n)

    # Fewer frames than the process has steps, by a wide margin: whatever the
    # driver uses, it is not one frame per step.
    with recursion_limit(50):
        assert sum_to(steps) == steps * (steps + 1) // 2

        with pytest.raises(RecursionError):
            plain_sum_to(steps)


def test_the_stack_does_not_grow() -> None:
    depths: list[int] = []

    @tail_recursive
    def walk(n: int) -> int:
        depths.append(stack_depth())
        if n == 0:
            return 0
        return TailCall(walk, n - 1)

    walk(200)

    assert depths[0] == depths[-1]


# --- mutual recursion ------------------------------------------------------


def test_mutually_recursive_procedures_complete() -> None:
    @tail_recursive
    def is_even(n: int) -> bool:
        if n == 0:
            return True
        return TailCall(is_odd, n - 1)

    @tail_recursive
    def is_odd(n: int) -> bool:
        if n == 0:
            return False
        return TailCall(is_even, n - 1)

    assert is_even(100_000) is True
    assert is_odd(100_001) is True


def test_deferring_to_a_decorated_procedure_reuses_the_running_driver() -> None:
    """A TailCall naming a decorated procedure must not start a second driver.

    If it did, mutual recursion would grow the stack by one driver per hand-off
    and the test above would only pass by being shallow enough to get away with
    it. Measuring the depth is what distinguishes the two.
    """
    depths: list[int] = []

    @tail_recursive
    def ping(n: int) -> str:
        depths.append(stack_depth())
        if n == 0:
            return "done"
        return TailCall(pong, n - 1)

    @tail_recursive
    def pong(n: int) -> str:
        depths.append(stack_depth())
        return TailCall(ping, n)

    assert ping(100) == "done"
    assert depths[0] == depths[-1]


# --- misuse: a deferred call that escaped, the recursive call not being last


def escaped() -> TailCall:
    """A TailCall of the sort that leaks when a call is not in tail position."""

    @tail_recursive
    def anything(n: int) -> int:
        return n

    return TailCall(anything, 1)


def test_arithmetic_on_an_escaped_call_is_refused() -> None:
    with pytest.raises(TypeError, match="tail position"):
        _ = 1 + escaped()  # type: ignore[operator]


def test_truth_testing_an_escaped_call_is_refused() -> None:
    with pytest.raises(TypeError, match="tail position"):
        bool(escaped())


def test_iterating_an_escaped_call_is_refused() -> None:
    with pytest.raises(TypeError, match="tail position"):
        list(escaped())  # type: ignore[call-overload]


def test_attribute_access_on_an_escaped_call_is_refused() -> None:
    with pytest.raises(TypeError, match="tail position"):
        _ = escaped().anything  # type: ignore[attr-defined]


def test_comparing_an_escaped_call_is_refused() -> None:
    with pytest.raises(TypeError, match="tail position"):
        _ = escaped() < 1  # type: ignore[operator]


# --- housekeeping ----------------------------------------------------------


def test_the_decorated_procedure_keeps_its_name_and_docstring() -> None:
    @tail_recursive
    def improve(guess: float) -> float:
        """Improve a guess."""
        return guess

    assert improve.__name__ == "improve"
    assert improve.__doc__ == "Improve a guess."


def test_an_exception_propagates_and_leaves_the_driver_usable() -> None:
    @tail_recursive
    def count_down(n: int, *, fail_at: int | None = None) -> int:
        if n == fail_at:
            raise ValueError("stopped early")
        if n == 0:
            return 0
        return TailCall(count_down, n - 1, fail_at=fail_at)

    with pytest.raises(ValueError, match="stopped early"):
        count_down(5, fail_at=3)

    # a driver abandoned part-way must leave nothing behind that spoils the next
    assert count_down(5) == 0
