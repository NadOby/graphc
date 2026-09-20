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

    def test_creation_does_not_require_a_source_mapping(self) -> None:
        created = EntityID("created")

        state = State.create({})

        result = transform_with_mapping(
            state,
            {
                created: 42,
            },
            {},
        )

        self.assertTrue(
            result.destination.contains(created)
        )
        self.assertEqual(
            result.mappings,
            (),
        )

    def test_created_entity_has_no_predecessor_for_reference_transfer(
        self,
    ) -> None:
        source = EntityID("source")
        created = EntityID("created")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                created: 42,
            },
            {},
        )

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                state.reference(source),
                result,
            )

        self.assertTrue(
            result.destination.contains(created)
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

    def test_explicit_disappearance_removes_source_entity(self) -> None:
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

        self.assertFalse(
            result.destination.contains(source)
        )
        self.assertEqual(
            result.mapped_entities(state.reference(source)),
            (),
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
            transform_with_mapping(
                state,
                {},
                {},
            ).mapped_entity(state.reference(source))

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

    def test_disappearance_removes_ownership_edges(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        sibling = EntityID("sibling")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
                sibling: Value.create(sibling, 3),
            },
            {
                root: (child, sibling),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: (),
            },
        )

        self.assertFalse(
            result.destination.contains(root)
        )
        self.assertTrue(
            result.destination.contains(child)
        )
        self.assertTrue(
            result.destination.contains(sibling)
        )
        self.assertEqual(
            result.destination.ownership,
            {},
        )

    def test_disappearance_removes_entity_from_parent_ownership(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        sibling = EntityID("sibling")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
                sibling: Value.create(sibling, 3),
            },
            {
                root: (child, sibling),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                child: (),
            },
        )

        self.assertFalse(
            result.destination.contains(child)
        )
        self.assertEqual(
            result.destination.ownership,
            {
                root: (sibling,),
            },
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

    def test_disappearance_does_not_provide_a_mapping_for_next_transform(
        self,
    ) -> None:
        source = EntityID("source")
        replacement = EntityID("replacement")

        initial = State.create({
            source: Value.create(source, 1),
        })

        disappeared = transform_with_mapping(
            initial,
            {},
            {
                source: (),
            },
        )

        next_result = transform_with_mapping(
            disappeared.destination,
            {
                replacement: 2,
            },
            {},
        )

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                initial.reference(source),
                disappeared,
            )

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                initial.reference(source),
                next_result,
            )

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

    def test_sequential_mapping_requires_each_intermediate_state(self) -> None:
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

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                initial.reference(first),
                second_result,
            )

        transferred = transfer_reference(
            initial.reference(first),
            first_result,
        )
        transferred = transfer_reference(
            transferred,
            second_result,
        )

        self.assertEqual(transferred.entity, third)

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

    def test_transform_result_rejects_mapping_for_wrong_source_state(
        self,
    ) -> None:
        from semiroh import EntityMapping, TransformResult

        foo = EntityID("foo")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            bar: Value.create(bar, 2),
        })

        with self.assertRaises(ValueError):
            TransformResult(
                source=first,
                destination=second,
                mappings=(
                    EntityMapping(
                        source_state=second.id,
                        source_entity=foo,
                        destination_entities=(bar,),
                    ),
                ),
            )

    def test_transform_result_rejects_missing_source_entity(self) -> None:
        from semiroh import EntityMapping, TransformResult

        foo = EntityID("foo")
        missing = EntityID("missing")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            bar: Value.create(bar, 2),
        })

        with self.assertRaises(ValueError):
            TransformResult(
                source=first,
                destination=second,
                mappings=(
                    EntityMapping(
                        source_state=first.id,
                        source_entity=missing,
                        destination_entities=(bar,),
                    ),
                ),
            )

    def test_transform_result_rejects_missing_destination_entity(
        self,
    ) -> None:
        from semiroh import EntityMapping, TransformResult

        foo = EntityID("foo")
        bar = EntityID("bar")
        missing = EntityID("missing")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            bar: Value.create(bar, 2),
        })

        with self.assertRaises(ValueError):
            TransformResult(
                source=first,
                destination=second,
                mappings=(
                    EntityMapping(
                        source_state=first.id,
                        source_entity=foo,
                        destination_entities=(missing,),
                    ),
                ),
        )
