"""Tests for transformation composition semantics."""

import unittest

from semiroh import (
    CompositionResult,
    EntityID,
    TransformationDefinition,
    compose,
)


class TransformationCompositionTests(unittest.TestCase):
    def test_chain_composes_explicit_continuity(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create(
            mappings={b: c},
        )

        result = compose(first, second)

        self.assertEqual(
            result.mappings,
            (
                first.mappings[0].__class__(
                    source_entity=a,
                    destination_entities=(c,),
                ),
            ),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset(),
        )

    def test_disappearance_composes(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create(
            mappings={b: ()},
        )

        result = compose(first, second)

        self.assertEqual(
            result.mappings[0].destination_entities,
            (),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset(),
        )

    def test_split_composes(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")
        e = EntityID("E")

        first = TransformationDefinition.create(
            mappings={a: (b, c)},
        )
        second = TransformationDefinition.create(
            mappings={
                b: d,
                c: e,
            },
        )

        result = compose(first, second)

        self.assertEqual(
            result.mappings[0].destination_entities,
            (d, e),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset(),
        )

    def test_split_merge_uses_set_semantics(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")

        first = TransformationDefinition.create(
            mappings={a: (b, c)},
        )
        second = TransformationDefinition.create(
            mappings={
                b: d,
                c: d,
            },
        )

        result = compose(first, second)

        self.assertEqual(
            result.mappings[0].destination_entities,
            (d,),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset(),
        )

    def test_missing_second_mapping_produces_unknown(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create()

        result = compose(first, second)

        self.assertEqual(
            result.mappings,
            (),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset({a}),
        )

    def test_partial_split_resolution_produces_unknown(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")

        first = TransformationDefinition.create(
            mappings={a: (b, c)},
        )
        second = TransformationDefinition.create(
            mappings={b: d},
        )

        result = compose(first, second)

        self.assertEqual(
            result.mappings,
            (),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset({a}),
        )

    def test_identity_is_neutral_for_known_continuity(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        transformation = TransformationDefinition.create(
            mappings={a: b},
        )
        identity = TransformationDefinition.create(
            mappings={b: b},
        )

        result = compose(transformation, identity)

        self.assertEqual(
            result.mappings[0].destination_entities,
            (b,),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset(),
        )

    def test_disappearance_is_not_unknown(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create(
            mappings={b: ()},
        )

        result = compose(first, second)

        self.assertNotIn(a, result.unknown_sources)
        self.assertEqual(
            result.mappings[0].destination_entities,
            (),
        )

    def test_composition_result_is_immutable(self) -> None:
        result = CompositionResult(
            mappings=(),
            unknown_sources=frozenset(),
        )

        with self.assertRaises(AttributeError):
            result.unknown_sources = frozenset()

    def test_mapping_lookup(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")

        result = compose(
            TransformationDefinition.create(
                mappings={a: b},
            ),
            TransformationDefinition.create(
                mappings={b: c},
            ),
        )

        mapping = result.mapping_for(a)

        self.assertIsNotNone(mapping)
        assert mapping is not None
        self.assertEqual(
            mapping.destination_entities,
            (c,),
        )

        self.assertIsNone(
            result.mapping_for(b),
        )

    def test_known_sources_excludes_unknown_sources(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")

        result = compose(
            TransformationDefinition.create(
                mappings={
                    a: b,
                    c: c,
                },
            ),
            TransformationDefinition.create(
                mappings={
                    c: c,
                },
            ),
        )

        self.assertEqual(
            result.known_sources,
            frozenset({c}),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset({a}),
        )
