"""Constraint results and immutable semantic constraints."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class ConstraintResult(Enum):
    """Three-valued result of constraint evaluation."""

    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNKNOWN = "unknown"


ConstraintPredicate = Callable[[Any], ConstraintResult]


@dataclass(frozen=True)
class Constraint:
    """Immutable semantic proposition.

    The predicate is the executable evaluation mechanism. Its semantic
    representation and canonical identity remain separate concerns and are
    intentionally not inferred from Python callable identity.
    """

    predicate: ConstraintPredicate
    description: str = ""

    def __post_init__(self) -> None:
        if not callable(self.predicate):
            raise TypeError(
                "constraint predicate must be callable"
            )

        if not isinstance(self.description, str):
            raise TypeError(
                "constraint description must be a string"
            )

    def evaluate(self, subject: Any) -> ConstraintResult:
        """Evaluate the constraint against a subject."""

        result = self.predicate(subject)

        if not isinstance(result, ConstraintResult):
            raise TypeError(
                "constraint predicate must return ConstraintResult"
            )

        return result
