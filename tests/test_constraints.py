"""Tests for semantic constraints."""

import unittest

from semiroh.constraints import Constraint, ConstraintResult


class ConstraintTests(unittest.TestCase):
    def test_satisfied_constraint(self) -> None:
        constraint = Constraint(
            predicate=lambda value: (
                ConstraintResult.SATISFIED
                if value > 0
                else ConstraintResult.VIOLATED
            )
        )

        self.assertEqual(
            constraint.evaluate(1),
            ConstraintResult.SATISFIED,
        )

    def test_violated_constraint(self) -> None:
        constraint = Constraint(
            predicate=lambda value: (
                ConstraintResult.SATISFIED
                if value > 0
                else ConstraintResult.VIOLATED
            )
        )

        self.assertEqual(
            constraint.evaluate(-1),
            ConstraintResult.VIOLATED,
        )

    def test_unknown_constraint(self) -> None:
        constraint = Constraint(
            predicate=lambda _: ConstraintResult.UNKNOWN
        )

        self.assertEqual(
            constraint.evaluate(object()),
            ConstraintResult.UNKNOWN,
        )

    def test_invalid_predicate_result_is_rejected(self) -> None:
        constraint = Constraint(
            predicate=lambda _: True,  # type: ignore[return-value]
        )

        with self.assertRaises(TypeError):
            constraint.evaluate(object())

    def test_description_is_preserved(self) -> None:
        constraint = Constraint(
            predicate=lambda _: ConstraintResult.UNKNOWN,
            description="value is known",
        )

        self.assertEqual(
            constraint.description,
            "value is known",
        )

    def test_constraint_is_immutable(self) -> None:
        constraint = Constraint(
            predicate=lambda _: ConstraintResult.UNKNOWN,
        )

        with self.assertRaises(AttributeError):
            constraint.description = "changed"  # type: ignore[misc]
