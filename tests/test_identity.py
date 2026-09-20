"""Tests for semantic identity and equality."""

import unittest

from semiroh import (
    EntityID,
    Value,
    semantic_equal,
    same_entity,
    same_version,
    version_id_for,
)


class IdentityTests(unittest.TestCase):
    def test_entity_version_changes_when_content_changes(self) -> None:
        foo = EntityID("foo")

        first = Value.create(foo, 1)
        second = Value.create(foo, 2)

        self.assertEqual(first.entity, second.entity)
        self.assertNotEqual(
            version_id_for(first),
            version_id_for(second),
        )
        self.assertTrue(same_entity(first, second))
        self.assertFalse(same_version(first, second))

    def test_identical_entity_versions_have_identical_version_ids(self) -> None:
        foo = EntityID("foo")

        first = Value.create(foo, 42)
        second = Value.create(foo, 42)

        self.assertEqual(
            version_id_for(first),
            version_id_for(second),
        )
        self.assertTrue(semantic_equal(first, second))
        self.assertTrue(same_entity(first, second))

    def test_version_id_is_history_independent(self) -> None:
        foo = EntityID("foo")

        direct = Value.create(foo, 42)
        intermediate = Value.create(foo, 1)

        self.assertEqual(
            version_id_for(direct),
            version_id_for(Value.create(foo, 42)),
        )
        self.assertNotEqual(
            version_id_for(direct),
            version_id_for(intermediate),
        )

    def test_same_entity_different_versions_are_not_equal(self) -> None:
        foo = EntityID("foo")

        first = Value.create(foo, 1)
        second = Value.create(foo, 2)

        self.assertTrue(same_entity(first, second))
        self.assertFalse(semantic_equal(first, second))
        self.assertFalse(same_version(first, second))

    def test_different_entities_same_content_are_equal(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = Value.create(foo, 42)
        second = Value.create(bar, 42)

        self.assertFalse(same_entity(first, second))
        self.assertTrue(semantic_equal(first, second))
        self.assertNotEqual(
            version_id_for(first),
            version_id_for(second),
        )
