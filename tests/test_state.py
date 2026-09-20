"""Tests for immutable semantic states and values."""

import unittest

from semiroh import (
    EntityID,
    State,
    Value,
    version_id_for,
)


class StateTests(unittest.TestCase):
    def test_state_identity_is_history_independent(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 42),
            bar: Value.create(bar, 10),
        })

        second = State.create({
            bar: Value.create(bar, 10),
            foo: Value.create(foo, 42),
        })

        self.assertEqual(first.id, second.id)

    def test_state_values_are_immutable(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        with self.assertRaises(TypeError):
            state.values[foo] = Value.create(foo, 2)

        self.assertEqual(state.values[foo].content, 1)

    def test_state_ownership_is_immutable(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        state = State.create(
            {
                foo: Value.create(foo, 1),
                bar: Value.create(bar, 2),
            },
            {
                foo: (bar,),
            },
        )

        with self.assertRaises(TypeError):
            state.ownership[foo] = (bar,)

        self.assertEqual(state.ownership[foo], (bar,))

    def test_value_content_is_immutable(self) -> None:
        foo = EntityID("foo")

        original = [1, 2, 3]
        value = Value.create(foo, original)

        original.append(4)

        self.assertEqual(
            value.content,
            (
                "__type__",
                "list",
                (1, 2, 3),
            ),
        )

        with self.assertRaises(TypeError):
            value.content[2] += (4,)

    def test_direct_value_construction_is_immutable(self) -> None:
        foo = EntityID("foo")

        original = [1, 2, 3]
        value = Value(foo, original)

        original.append(4)

        self.assertEqual(
            value.content,
            (
                "__type__",
                "list",
                (1, 2, 3),
            ),
        )

    def test_original_input_mapping_cannot_mutate_state(self) -> None:
        foo = EntityID("foo")

        values = {
            foo: Value.create(foo, 1),
        }

        state = State.create(values)

        values[foo] = Value.create(foo, 2)

        self.assertEqual(state.values[foo].content, 1)

    def test_original_ownership_mapping_cannot_mutate_state(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        ownership = {
            foo: [bar],
        }

        state = State.create(
            {
                foo: Value.create(foo, 1),
                bar: Value.create(bar, 2),
            },
            ownership,
        )

        ownership[foo].append(foo)

        self.assertEqual(state.ownership[foo], (bar,))

    def test_state_identity_is_full_sha256(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        self.assertEqual(len(state.id.value), 64)
        self.assertTrue(
            all(
                character in "0123456789abcdef"
                for character in state.id.value
            )
        )

    def test_state_rejects_entity_key_mismatch(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        with self.assertRaises(ValueError):
            State.create({
                foo: Value.create(bar, 42),
            })
