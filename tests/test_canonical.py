"""Tests for canonical semantic serialization."""

import unittest

from semiroh import (
    EntityID,
    State,
    Value,
    canonical_serialize,
)


class CanonicalTests(unittest.TestCase):
    def test_canonical_serialization_is_type_sensitive(self) -> None:
        self.assertNotEqual(
            canonical_serialize(1),
            canonical_serialize(True),
        )
        self.assertNotEqual(
            canonical_serialize(1),
            canonical_serialize("1"),
        )
        self.assertNotEqual(
            canonical_serialize("1"),
            canonical_serialize(b"1"),
        )

    def test_canonical_serialization_is_length_delimited(self) -> None:
        self.assertNotEqual(
            canonical_serialize("ab"),
            canonical_serialize("a"),
        )
        self.assertNotEqual(
            canonical_serialize("abc"),
            canonical_serialize("ab"),
        )

    def test_canonical_serialization_handles_nested_values(self) -> None:
        first = {
            "numbers": [1, 2, 3],
            "nested": ("a", b"bc"),
        }

        second = {
            "nested": ("a", b"bc"),
            "numbers": [1, 2, 3],
        }

        self.assertEqual(
            canonical_serialize(first),
            canonical_serialize(second),
        )

    def test_canonical_serialization_distinguishes_sequence_types(self) -> None:
        self.assertNotEqual(
            canonical_serialize([1, 2]),
            canonical_serialize((1, 2)),
        )

    def test_canonical_serialization_distinguishes_map_keys_by_type(self) -> None:
        int_key = {1: "value"}
        bool_key = {True: "value"}

        self.assertNotEqual(
            canonical_serialize(int_key),
            canonical_serialize(bool_key),
        )

    def test_state_identity_uses_canonical_serialization(self) -> None:
        foo = EntityID("foo")

        first = State.create({
            foo: Value.create(foo, {
                "a": [1, 2, 3],
                "b": ("x", b"y"),
            }),
        })

        second = State.create({
            foo: Value.create(foo, {
                "b": ("x", b"y"),
                "a": [1, 2, 3],
            }),
        })

        self.assertEqual(first.id, second.id)
