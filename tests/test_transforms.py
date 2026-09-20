"""Tests for semantic transformations and ownership behavior."""

import unittest

from semiroh import (
    EntityID,
    OwnershipError,
    State,
    Value,
    transform_with_mapping,
)


class TransformTests(unittest.TestCase):
    def test_state_identity_ignores_transition_mapping(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        result_a = transform_with_mapping(
            first,
            {bar: 2},
            {foo: bar},
        )

        result_b = transform_with_mapping(
            first,
            {bar: 2},
            {},
        )

        self.assertEqual(
            result_a.destination.id,
            result_b.destination.id,
        )
        self.assertNotEqual(
            result_a.destination.id,
            first.id,
        )

    def test_transform_preserves_ownership_when_entities_are_unchanged(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {
                root: 10,
                child: 20,
            },
            {
                root: root,
                child: child,
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                root: (child,),
            },
        )

    def test_transform_can_explicitly_remove_ownership(self) -> None:
        root = EntityID("root")
        child = EntityID("child")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
                child: child,
            },
            ownership={},
        )

        self.assertEqual(result.destination.ownership, {})
        self.assertTrue(result.destination.contains(root))
        self.assertTrue(result.destination.contains(child))

    def test_transform_can_explicitly_change_ownership(self) -> None:
        root = EntityID("root")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create(
            {
                root: Value.create(root, 0),
                left: Value.create(left, 1),
                right: Value.create(right, 2),
            },
            {
                root: (left,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
                left: left,
                right: right,
            },
            ownership={
                root: (right,),
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                root: (right,),
            },
        )

    def test_transform_does_not_infer_ownership_from_entity_mapping(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")
        new_root = EntityID("new_root")
        new_child = EntityID("new_child")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {
                new_root: 10,
                new_child: 11,
            },
            {
                root: new_root,
                child: new_child,
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                root: (child,),
            },
        )

        self.assertEqual(
            result.destination.owner_of(child),
            root,
        )
        self.assertIsNone(
            result.destination.owner_of(new_child)
        )

    def test_transform_can_explicitly_preserve_ownership_after_rename(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")
        new_root = EntityID("new_root")
        new_child = EntityID("new_child")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {
                new_root: 10,
                new_child: 11,
            },
            {
                root: new_root,
                child: new_child,
            },
            ownership={
                new_root: (new_child,),
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                new_root: (new_child,),
            },
        )

        self.assertEqual(
            result.destination.owner_of(new_child),
            new_root,
        )

    def test_transform_rejects_invalid_destination_ownership(self) -> None:
        root = EntityID("root")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create(
            {
                root: Value.create(root, 0),
                left: Value.create(left, 1),
                right: Value.create(right, 2),
            },
            {
                root: (left,),
            },
        )

        with self.assertRaises(OwnershipError):
            transform_with_mapping(
                state,
                {},
                {
                    root: root,
                    left: left,
                    right: right,
                },
                ownership={
                    root: (right,),
                    left: (right,),
                },
            )

    def test_transform_rejects_destination_ownership_cycle(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        leaf = EntityID("leaf")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
                leaf: Value.create(leaf, 2),
            },
        )

        with self.assertRaises(OwnershipError):
            transform_with_mapping(
                state,
                {},
                {
                    root: root,
                    child: child,
                    leaf: leaf,
                },
                ownership={
                    root: (child,),
                    child: (leaf,),
                    leaf: (root,),
                },
            )

    def test_transform_does_not_mutate_source_ownership(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        sibling = EntityID("sibling")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
                sibling: Value.create(sibling, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
                child: child,
                sibling: sibling,
            },
            ownership={
                root: (sibling,),
            },
        )

        self.assertEqual(
            state.ownership,
            {
                root: (child,),
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                root: (sibling,),
            },
        )

    def test_transform_changes_state_identity_when_ownership_changes(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
                child: child,
            },
            ownership={},
        )

        self.assertNotEqual(result.destination.id, state.id)
