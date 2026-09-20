"""Tests for explicit identity continuity mappings."""

import unittest

from semiroh import (
    AmbiguousEntityMapping,
    EntityID,
    MissingEntityMapping,
    State,
    Value,
    transfer_reference,
    transform_with_mapping,
)


class ContinuityTests(unittest.TestCase):
    def test_mapped_entities_returns_single_destination(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        result = transform_with_mapping(
            state,
            {
                bar: 2,
            },
            {
                foo: bar,
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(foo)),
            (bar,),
        )

    def test_split_mapping_returns_all_destinations(self) -> None:
        source = EntityID("source")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (right, left),
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(source)),
            (left, right),
        )

    def test_split_mapping_is_ambiguous_for_mapped_entity(self) -> None:
        source = EntityID("source")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (left, right),
            },
        )

        with self.assertRaises(AmbiguousEntityMapping):
            result.mapped_entity(state.reference(source))

    def test_split_mapping_cannot_transfer_reference(self) -> None:
        source = EntityID("source")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (left, right),
            },
        )

        with self.assertRaises(AmbiguousEntityMapping):
            transfer_reference(
                state.reference(source),
                result,
            )

    def test_explicit_disappearance_is_distinct_from_missing_mapping(
        self,
    ) -> None:
        source = EntityID("source")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {},
            {
                source: (),
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(source)),
            (),
        )

        with self.assertRaises(MissingEntityMapping):
            result.mapped_entity(state.reference(source))

    def test_disappearance_cannot_transfer_reference(self) -> None:
        source = EntityID("source")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {},
            {
                source: (),
            },
        )

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                state.reference(source),
                result,
            )

    def test_merge_maps_multiple_sources_to_one_destination(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        merged = EntityID("merged")

        state = State.create({
            first: Value.create(first, 1),
            second: Value.create(second, 2),
        })

        result = transform_with_mapping(
            state,
            {
                merged: 3,
            },
            {
                first: merged,
                second: merged,
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(first)),
            (merged,),
        )
        self.assertEqual(
            result.mapped_entities(state.reference(second)),
            (merged,),
        )

        self.assertEqual(
            result.mapped_entity(state.reference(first)),
            merged,
        )
        self.assertEqual(
            result.mapped_entity(state.reference(second)),
            merged,
        )

    def test_merge_allows_both_references_to_transfer(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        merged = EntityID("merged")

        state = State.create({
            first: Value.create(first, 1),
            second: Value.create(second, 2),
        })

        result = transform_with_mapping(
            state,
            {
                merged: 3,
            },
            {
                first: merged,
                second: merged,
            },
        )

        first_reference = transfer_reference(
            state.reference(first),
            result,
        )

        second_reference = transfer_reference(
            state.reference(second),
            result,
        )

        self.assertEqual(first_reference.entity, merged)
        self.assertEqual(second_reference.entity, merged)
        self.assertEqual(
            first_reference.state,
            result.destination.id,
        )
        self.assertEqual(
            second_reference.state,
            result.destination.id,
        )

    def test_many_to_many_mapping_returns_complete_relation(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            first: Value.create(first, 1),
            second: Value.create(second, 2),
        })

        result = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                first: (right, left),
                second: (left, right),
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(first)),
            (left, right),
        )
        self.assertEqual(
            result.mapped_entities(state.reference(second)),
            (left, right),
        )

    def test_mapping_destination_order_is_canonicalized(self) -> None:
        source = EntityID("source")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            source: Value.create(source, 1),
        })

        result_a = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (right, left),
            },
        )

        result_b = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (left, right),
            },
        )

        self.assertEqual(result_a.mappings, result_b.mappings)

    def test_mapping_source_order_is_canonicalized(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            first: Value.create(first, 1),
            second: Value.create(second, 2),
        })

        result_a = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                second: (right,),
                first: (left,),
            },
        )

        result_b = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                first: (left,),
                second: (right,),
            },
        )

        self.assertEqual(result_a.mappings, result_b.mappings)

    def test_duplicate_destinations_are_rejected(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        with self.assertRaises(ValueError):
            transform_with_mapping(
                state,
                {
                    destination: 2,
                },
                {
                    source: (
                        destination,
                        destination,
                    ),
                },
            )

    def test_missing_mapping_and_explicit_disappearance_are_distinct(
        self,
    ) -> None:
        source = EntityID("source")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {},
            {},
        )

        with self.assertRaises(MissingEntityMapping):
            result.mapped_entities(
                state.reference(source)
            )

        explicit = transform_with_mapping(
            state,
            {},
            {
                source: (),
            },
        )

        self.assertEqual(
            explicit.mapped_entities(
                state.reference(source)
            ),
            (),
        )

    def test_mapping_requires_existing_source_entity(self) -> None:
        source = EntityID("source")
        missing = EntityID("missing")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        with self.assertRaises(KeyError):
            transform_with_mapping(
                state,
                {
                    destination: 2,
                },
                {
                    missing: destination,
                },
            )

    def test_mapping_requires_existing_destination_entity(self) -> None:
        source = EntityID("source")
        missing = EntityID("missing")

        state = State.create({
            source: Value.create(source, 1),
        })

        with self.assertRaises(KeyError):
            transform_with_mapping(
                state,
                {},
                {
                    source: missing,
                },
            )

    def test_mapping_accepts_bare_entity_id_compatibility_form(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                destination: 2,
            },
            {
                source: destination,
            },
        )

        self.assertEqual(
            result.mapped_entities(
                state.reference(source)
            ),
            (destination,),
        )

    def test_transition_mapping_does_not_affect_destination_state_identity(
        self,
    ) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        mapped = transform_with_mapping(
            state,
            {
                destination: 2,
            },
            {
                source: destination,
            },
        )

        unmapped = transform_with_mapping(
            state,
            {
                destination: 2,
            },
            {},
        )

        self.assertEqual(
            mapped.destination.id,
            unmapped.destination.id,
        )

    def test_transition_mapping_does_not_modify_ownership(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")
        child = EntityID("child")

        state = State.create(
            {
                source: Value.create(source, 1),
                destination: Value.create(destination, 2),
                child: Value.create(child, 3),
            },
            {
                source: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                source: destination,
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                source: (child,),
            },
        )
