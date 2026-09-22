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


@dataclass(frozen=True)
class Constraint:
    """Immutable semantic proposition."""

    predicate: Callable[[Any], ConstraintResult]
    description: str = ""

    def evaluate(self, subject: Any) -> ConstraintResult:
        """Evaluate the constraint against a subject."""

        result = self.predicate(subject)

        if not isinstance(result, ConstraintResult):
            raise TypeError(
                "constraint predicate must return ConstraintResult"
            )

        return result
