"""Tests for immutable transformation definitions."""

import unittest

from semiroh import (
    AmbiguousEntityMapping,
    EntityChange,
    EntityID,
    MissingEntityMapping,
    State,
    TransformationDefinition,
    TransformationMapping,
    Value,
)


class TransformationDefinitionTests(unittest.TestCase):
    def test_definition_is_immutable(self) -> None:
        foo = EntityID("foo")

        definition = TransformationDefinition.create(
            changes={foo: 42},
        )

        with self.assertRaises(AttributeError):
            definition.changes = ()

    def test_changes_are_canonicalized_by_entity(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = TransformationDefinition.create(
            changes={
                bar: 2,
                foo: 1,
            },
        )

        second = TransformationDefinition.create(
            changes={
                foo: 1,
                bar: 2,
            },
        )

        self.assertEqual(first, second)

        self.assertEqual(
            tuple(
                change.entity
                for change in first.changes
            ),
            tuple(sorted((foo, bar))),
        )

    def test_mappings_are_canonicalized_by_source_entity(self) -> None:
        source_a = EntityID("source-a")
        source_b = EntityID("source-b")
        destination_a = EntityID("destination-a")
        destination_b = EntityID("destination-b")

        first = TransformationDefinition.create(
            mappings={
                source_b: destination_b,
                source_a: destination_a,
            },
        )

        second = TransformationDefinition.create(
            mappings={
                source_a: destination_a,
                source_b: destination_b,
            },
        )

        self.assertEqual(first, second)

        self.assertEqual(
            tuple(
                mapping.source_entity
                for mapping in first.mappings
            ),
            tuple(sorted((source_a, source_b))),
        )

    def test_change_contains_immutable_semantic_value(self) -> None:
        foo = EntityID("foo")
        value = Value.create(foo, 42)

        change = EntityChange(
            entity=foo,
            value=value,
        )

        self.assertEqual(change.entity, foo)
        self.assertEqual(change.value, value)

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
                mappings=(),
            )

    def test_duplicate_mappings_are_rejected(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        with self.assertRaises(ValueError):
            TransformationDefinition(
                changes=(),
                mappings=(
                    TransformationMapping(
                        source_entity=foo,
                        destination_entities=(bar,),
                    ),
                    TransformationMapping(
                        source_entity=foo,
                        destination_entities=(),
                    ),
                ),
            )

    def test_mapping_destination_entities_are_canonicalized(self) -> None:
        source = EntityID("source")
        first = EntityID("destination-a")
        second = EntityID("destination-b")

        mapping = TransformationMapping(
            source_entity=source,
            destination_entities=tuple(
                sorted((second, first))
            ),
        )

        self.assertEqual(
            mapping.destination_entities,
            (first, second),
        )

    def test_mapping_rejects_duplicate_destination_entities(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        with self.assertRaises(ValueError):
            TransformationMapping(
                source_entity=source,
                destination_entities=(
                    destination,
                    destination,
                ),
            )

    def test_mapping_rejects_noncanonical_destination_order(self) -> None:
        source = EntityID("source")
        first = EntityID("destination-a")
        second = EntityID("destination-b")

        with self.assertRaises(ValueError):
            TransformationMapping(
                source_entity=source,
                destination_entities=(
                    second,
                    first,
                ),
            )

    def test_apply_replaces_existing_value(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create(
            changes={foo: 2},
            mappings={foo: foo},
        )

        result = definition.apply(state)

        self.assertEqual(
            result.destination.values[foo].content,
            2,
        )
        self.assertNotEqual(
            result.destination.id,
            state.id,
        )

        self.assertEqual(
            result.mapped_entities(state.reference(foo)),
            (foo,),
        )

    def test_apply_can_create_an_entity(self) -> None:
        foo = EntityID("foo")

        state = State.create({})

        definition = TransformationDefinition.create(
            changes={foo: 42},
        )

        result = definition.apply(state)

        self.assertTrue(
            result.destination.contains(foo),
        )
        self.assertEqual(
            result.destination.values[foo].content,
            42,
        )
        self.assertEqual(
            result.mappings,
            (),
        )

    def test_apply_can_disappear_an_entity(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create(
            mappings={foo: ()},
        )

        result = definition.apply(state)

        self.assertFalse(
            result.destination.contains(foo),
        )
        self.assertEqual(
            result.mappings[0].destination_entities,
            (),
        )

        with self.assertRaises(MissingEntityMapping):
            result.mapped_entity(state.reference(foo))

    def test_apply_can_split_an_entity(self) -> None:
        source = EntityID("source")
        first = EntityID("destination-a")
        second = EntityID("destination-b")

        state = State.create({
            source: Value.create(source, 1),
            first: Value.create(first, 2),
            second: Value.create(second, 3),
        })

        definition = TransformationDefinition.create(
            mappings={
                source: (second, first),
            },
        )

        result = definition.apply(state)

        self.assertEqual(
            result.mappings[0].destination_entities,
            (first, second),
        )

        with self.assertRaises(AmbiguousEntityMapping):
            result.mapped_entity(state.reference(source))

    def test_apply_does_not_modify_source_state(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create(
            changes={foo: 2},
            mappings={foo: foo},
        )

        result = definition.apply(state)

        self.assertEqual(
            state.values[foo].content,
            1,
        )
        self.assertEqual(
            result.destination.values[foo].content,
            2,
        )

    def test_empty_definition_produces_equivalent_state(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create()

        result = definition.apply(state)

        self.assertEqual(
            result.destination.id,
            state.id,
        )
        self.assertEqual(
            result.destination.values,
            state.values,
        )
        self.assertEqual(
            result.destination.ownership,
            state.ownership,
        )
        self.assertEqual(
            result.mappings,
            (),
        )
