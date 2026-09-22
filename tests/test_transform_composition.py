"""Tests for transformation composition semantics."""

import unittest

from semiroh import EntityID, TransformationDefinition, compose


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
            result.mapping_for(a).destination_entities,
            (c,),
        )
        self.assertEqual(result.unknown_sources, frozenset())

    def test_disappearance_composes(self) -> None:
        a = EntityID("A")

        first = TransformationDefinition.create(
            mappings={a: ()},
        )
        second = TransformationDefinition.create()

        result = compose(first, second)

        self.assertEqual(
            result.mapping_for(a).destination_entities,
            (),
        )
        self.assertEqual(result.unknown_sources, frozenset())

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
            result.mapping_for(a).destination_entities,
            (d, e),
        )
        self.assertEqual(result.unknown_sources, frozenset())

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
            result.mapping_for(a).destination_entities,
            (d,),
        )

    def test_missing_second_mapping_produces_unknown(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create()

        result = compose(first, second)

        self.assertIsNone(result.mapping_for(a))
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

        self.assertIsNone(result.mapping_for(a))
        self.assertEqual(
            result.unknown_sources,
            frozenset({a}),
        )

    def test_second_transformation_can_split_again(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create(
            mappings={b: (c, d)},
        )

        result = compose(first, second)

        self.assertEqual(
            result.mapping_for(a).destination_entities,
            (c, d),
        )

    def test_identity_is_neutral_for_known_continuity(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        identity = TransformationDefinition.create(
            mappings={b: b},
        )

        result = compose(first, identity)

        self.assertEqual(
            result.mapping_for(a).destination_entities,
            (b,),
        )

    def test_identity_before_transformation(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        identity = TransformationDefinition.create(
            mappings={a: a},
        )
        second = TransformationDefinition.create(
            mappings={a: b},
        )

        result = compose(identity, second)

        self.assertEqual(
            result.mapping_for(a).destination_entities,
            (b,),
        )

    def test_disappearance_is_not_unknown(self) -> None:
        a = EntityID("A")

        first = TransformationDefinition.create(
            mappings={a: ()},
        )
        second = TransformationDefinition.create()

        result = compose(first, second)

        self.assertEqual(
            result.mapping_for(a).destination_entities,
            (),
        )
        self.assertNotIn(a, result.unknown_sources)

    def test_unknown_is_distinct_from_disappearance(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create()

        result = compose(first, second)

        self.assertIsNone(result.mapping_for(a))
        self.assertIn(a, result.unknown_sources)

    def test_unknown_does_not_leak_to_independent_mapping(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")

        first = TransformationDefinition.create(
            mappings={
                a: b,
                c: d,
            },
        )
        second = TransformationDefinition.create(
            mappings={d: c},
        )

        result = compose(first, second)

        self.assertIsNone(result.mapping_for(a))
        self.assertEqual(
            result.mapping_for(c).destination_entities,
            (c,),
        )
        self.assertEqual(
            result.unknown_sources,
            frozenset({a}),
        )

    def test_composition_is_associative_for_chain(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create(
            mappings={b: c},
        )
        third = TransformationDefinition.create(
            mappings={c: d},
        )

        first_second = compose(first, second)
        second_third = compose(second, third)

        left = compose(
            TransformationDefinition.create(
                mappings={
                    a: first_second.mapping_for(a).destination_entities,
                },
            ),
            third,
        )
        right = compose(
            first,
            TransformationDefinition.create(
                mappings={
                    b: second_third.mapping_for(b).destination_entities,
                },
            ),
        )

        self.assertEqual(
            left.mapping_for(a).destination_entities,
            right.mapping_for(a).destination_entities,
        )

    def test_composition_is_associative_for_split_merge(self) -> None:
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
                c: d,
            },
        )
        third = TransformationDefinition.create(
            mappings={d: e},
        )

        first_second = compose(first, second)
        second_third = compose(second, third)

        left = compose(
            TransformationDefinition.create(
                mappings={
                    a: first_second.mapping_for(a).destination_entities,
                },
            ),
            third,
        )
        right = compose(
            first,
            TransformationDefinition.create(
                mappings={
                    b: second_third.mapping_for(b).destination_entities,
                    c: second_third.mapping_for(c).destination_entities,
                },
            ),
        )

        self.assertEqual(
            left.mapping_for(a).destination_entities,
            right.mapping_for(a).destination_entities,
        )

    def test_composition_is_associative_with_unknown(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")

        first = TransformationDefinition.create(
            mappings={a: b},
        )
        second = TransformationDefinition.create()
        third = TransformationDefinition.create(
            mappings={c: d},
        )

        left = compose(
            compose(first, second),
            third,
        )
        right = compose(
            first,
            compose(second, third),
        )

        self.assertEqual(left.mappings, right.mappings)
        self.assertEqual(
            left.unknown_sources,
            right.unknown_sources,
        )
        self.assertEqual(
            left.unknown_sources,
            frozenset({a}),
        )
