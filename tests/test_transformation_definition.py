"""Tests for immutable transformation definitions."""

import unittest

from semiroh import (
    EntityChange,
    EntityID,
    State,
    TransformationDefinition,
    Value,
)


class TransformationDefinitionTests(unittest.TestCase):
    def test_definition_is_immutable(self) -> None:
        foo = EntityID("foo")

        definition = TransformationDefinition.create({
            foo: 42,
        })

        with self.assertRaises(AttributeError):
            definition.changes = ()

    def test_changes_are_canonicalized_by_entity(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = TransformationDefinition.create({
            bar: 2,
            foo: 1,
        })

        second = TransformationDefinition.create({
            foo: 1,
            bar: 2,
        })

        self.assertEqual(
            first,
            second,
        )

        self.assertEqual(
            tuple(
                change.entity
                for change in first.changes
            ),
            tuple(
                sorted(
                    (foo, bar)
                )
            ),
        )

    def test_change_contains_immutable_semantic_value(self) -> None:
        foo = EntityID("foo")
        value = Value.create(foo, 42)

        change = EntityChange(
            entity=foo,
            value=value,
        )

        self.assertEqual(
            change.entity,
            foo,
        )
        self.assertEqual(
            change.value,
            value,
        )

    def test_change_rejects_value_for_another_entity(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        with self.assertRaises(ValueError):
            EntityChange(
                entity=foo,
                value=Value.create(bar, 42),
            )

    def test_duplicate_changes_are_rejected(self) -> None:
        foo = EntityID("foo")

        with self.assertRaises(ValueError):
            TransformationDefinition(
                changes=(
                    EntityChange(
                        entity=foo,
                        value=Value.create(foo, 1),
                    ),
                    EntityChange(
                        entity=foo,
                        value=Value.create(foo, 2),
                    ),
                ),
            )

    def test_apply_replaces_existing_value(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create({
            foo: 2,
        })

        result = definition.apply(state)

        self.assertEqual(
            result.values[foo].content,
            2,
        )
        self.assertNotEqual(
            result.id,
            state.id,
        )

    def test_apply_can_create_an_entity(self) -> None:
        foo = EntityID("foo")

        state = State.create({})

        definition = TransformationDefinition.create({
            foo: 42,
        })

        result = definition.apply(state)

        self.assertTrue(
            result.contains(foo),
        )
        self.assertEqual(
            result.values[foo].content,
            42,
        )

    def test_apply_does_not_modify_source_state(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create({
            foo: 2,
        })

        result = definition.apply(state)

        self.assertEqual(
            state.values[foo].content,
            1,
        )
        self.assertEqual(
            result.values[foo].content,
            2,
        )

    def test_empty_definition_produces_equivalent_state(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create({})

        result = definition.apply(state)

        self.assertEqual(
            result.id,
            state.id,
        )
        self.assertEqual(
            result.values,
            state.values,
        )
        self.assertEqual(
            result.ownership,
            state.ownership,
        )
