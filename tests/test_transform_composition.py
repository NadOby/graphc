"""Tests for explicit composition of multiple transformations."""

import unittest

from semiroh import (
    AmbiguousEntityMapping,
    EntityID,
    State,
    Value,
    transfer_reference,
    transform_with_mapping,
)


class TransformCompositionTests(unittest.TestCase):
    def test_sequential_one_to_one_mapping(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        third = EntityID("third")

        initial = State.create({
            first: Value.create(first, 1),
        })

        first_result = transform_with_mapping(
            initial,
            {
                second: 2,
            },
            {
                first: second,
            },
        )

        second_result = transform_with_mapping(
            first_result.destination,
            {
                third: 3,
            },
            {
                second: third,
            },
        )

        reference = transfer_reference(
            initial.reference(first),
            first_result,
        )
        reference = transfer_reference(
            reference,
            second_result,
        )

        self.assertEqual(reference.entity, third)
        self.assertEqual(
            reference.state,
            second_result.destination.id,
        )

    def test_sequential_split_then_merge(self) -> None:
        source = EntityID("source")
        left = EntityID("left")
        right = EntityID("right")
        merged = EntityID("merged")

        initial = State.create({
            source: Value.create(source, 1),
        })

        split = transform_with_mapping(
            initial,
            {
                left: 10,
                right: 20,
            },
            {
                source: (left, right),
            },
        )

        merge = transform_with_mapping(
            split.destination,
            {
                merged: 30,
            },
            {
                left: merged,
                right: merged,
            },
        )

        with self.assertRaises(AmbiguousEntityMapping):
            transfer_reference(
                initial.reference(source),
                split,
            )

        left_reference = transfer_reference(
            split.destination.reference(left),
            merge,
        )
        right_reference = transfer_reference(
            split.destination.reference(right),
            merge,
        )

        self.assertEqual(left_reference.entity, merged)
        self.assertEqual(right_reference.entity, merged)

    def test_sequential_merge_then_one_to_one(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        merged = EntityID("merged")
        final = EntityID("final")

        initial = State.create({
            first: Value.create(first, 1),
            second: Value.create(second, 2),
        })

        merge = transform_with_mapping(
            initial,
            {
                merged: 3,
            },
            {
                first: merged,
                second: merged,
            },
        )

        next_result = transform_with_mapping(
            merge.destination,
            {
                final: 4,
            },
            {
                merged: final,
            },
        )

        first_reference = transfer_reference(
            initial.reference(first),
            merge,
        )
        first_reference = transfer_reference(
            first_reference,
            next_result,
        )

        second_reference = transfer_reference(
            initial.reference(second),
            merge,
        )
        second_reference = transfer_reference(
            second_reference,
            next_result,
        )

        self.assertEqual(first_reference.entity, final)
        self.assertEqual(second_reference.entity, final)

    def test_intermediate_state_ids_remain_distinct(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        third = EntityID("third")

        initial = State.create({
            first: Value.create(first, 1),
        })

        first_result = transform_with_mapping(
            initial,
            {
                second: 2,
            },
            {
                first: second,
            },
        )

        second_result = transform_with_mapping(
            first_result.destination,
            {
                third: 3,
            },
            {
                second: third,
            },
        )

        self.assertNotEqual(
            initial.id,
            first_result.destination.id,
        )
        self.assertNotEqual(
            first_result.destination.id,
            second_result.destination.id,
        )
        self.assertNotEqual(
            initial.id,
            second_result.destination.id,
        )

    def test_second_transform_ownership_change_is_independent(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        new_root = EntityID("new_root")
        new_child = EntityID("new_child")
        final_root = EntityID("final_root")
        final_child = EntityID("final_child")

        initial = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
            },
            {
                root: (child,),
            },
        )

        first_result = transform_with_mapping(
            initial,
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

        second_result = transform_with_mapping(
            first_result.destination,
            {
                final_root: 20,
                final_child: 21,
            },
            {
                new_root: final_root,
                new_child: final_child,
            },
            ownership={},
        )

        self.assertEqual(
            first_result.destination.ownership,
            {
                new_root: (new_child,),
            },
        )
        self.assertEqual(
            second_result.destination.ownership,
            {},
        )

    def test_lossless_round_trip_preserves_reference_continuity(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        initial = State.create({
            foo: Value.create(foo, 42),
        })

        forward = transform_with_mapping(
            initial,
            {
                bar: 42,
            },
            {
                foo: bar,
            },
        )

        backward = transform_with_mapping(
            forward.destination,
            {
                foo: 42,
            },
            {
                bar: foo,
            },
        )

        forward_reference = transfer_reference(
            initial.reference(foo),
            forward,
        )
        round_trip_reference = transfer_reference(
            forward_reference,
            backward,
        )

        self.assertEqual(
            round_trip_reference.entity,
            foo,
        )
        self.assertEqual(
            round_trip_reference.state,
            backward.destination.id,
        )
        self.assertEqual(
            round_trip_reference.version,
            initial.reference(foo).version,
        )

    def test_lossy_round_trip_does_not_claim_exact_restoration(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        initial = State.create({
            source: Value.create(source, 123),
        })

        lossy = transform_with_mapping(
            initial,
            {
                destination: 100,
            },
            {
                source: destination,
            },
            provenance={
                "lossy": True,
                "discarded": "23",
            },
        )

        reconstructed = transform_with_mapping(
            lossy.destination,
            {
                source: 100,
            },
            {
                destination: source,
            },
            provenance={
                "lossy": True,
                "reconstructed_from": destination,
            },
        )

        self.assertNotEqual(
            reconstructed.destination.id,
            initial.id,
        )
        self.assertNotEqual(
            reconstructed.destination.values,
            initial.values,
        )
