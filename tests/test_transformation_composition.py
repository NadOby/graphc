"""Tests for transformation composition semantics."""

import unittest

from semiroh import (
    EntityID,
    TransformationDefinition,
)


class TransformationCompositionSpecificationTests(unittest.TestCase):
    """
    Specification tests.

    These tests describe expected composition semantics before
    composition implementation exists.
    """

    def test_chain_continuity_example(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")

        t1 = TransformationDefinition.create(
            mappings={
                a: b,
            },
        )

        t2 = TransformationDefinition.create(
            mappings={
                b: c,
            },
        )

        self.assertEqual(
            t1.mappings[0].source_entity,
            a,
        )
        self.assertEqual(
            t2.mappings[0].source_entity,
            b,
        )

        #
        # Expected composition:
        #
        # A → B
        # B → C
        #
        # =>
        #
        # A → C
        #

    def test_disappearance_example(self) -> None:
        a = EntityID("A")

        t1 = TransformationDefinition.create(
            mappings={
                a: (),
            },
        )

        self.assertEqual(
            t1.mappings[0].destination_entities,
            (),
        )

        #
        # Expected composition:
        #
        # A → ()
        #
        # =>
        #
        # A → ()
        #

    def test_split_example(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")
        e = EntityID("E")

        t1 = TransformationDefinition.create(
            mappings={
                a: (b, c),
            },
        )

        t2 = TransformationDefinition.create(
            mappings={
                b: d,
                c: e,
            },
        )

        self.assertEqual(
            t1.mappings[0].destination_entities,
            (b, c),
        )

        #
        # Expected composition:
        #
        # A → (B,C)
        #
        # B → D
        # C → E
        #
        # =>
        #
        # A → (D,E)
        #

    def test_split_merge_example(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")

        t1 = TransformationDefinition.create(
            mappings={
                a: (b, c),
            },
        )

        t2 = TransformationDefinition.create(
            mappings={
                b: d,
                c: d,
            },
        )

        self.assertEqual(
            t1.mappings[0].destination_entities,
            (b, c),
        )

        #
        # Expected composition:
        #
        # A → (B,C)
        #
        # B → D
        # C → D
        #
        # raw:
        #
        # A → (D,D)
        #
        # normalized:
        #
        # A → (D)
        #

    def test_preservation_does_not_create_continuity(self) -> None:
        a = EntityID("A")
        b = EntityID("B")

        t1 = TransformationDefinition.create(
            mappings={
                a: b,
            },
        )

        t2 = TransformationDefinition.create()

        self.assertEqual(
            len(t2.mappings),
            0,
        )

        #
        # Expected composition:
        #
        # A → B
        #
        # B preserved
        #
        # =>
        #
        # no composed continuity mapping
        #

    def test_identity_transformation_is_neutral(self) -> None:
        a = EntityID("A")

        identity = TransformationDefinition.create(
            mappings={
                a: a,
            },
        )

        self.assertEqual(
            identity.mappings[0].source_entity,
            a,
        )
        self.assertEqual(
            identity.mappings[0].destination_entities,
            (a,),
        )

        #
        # Expected:
        #
        # Identity ∘ T = T
        # T ∘ Identity = T
        #

    def test_associativity_requirement(self) -> None:
        a = EntityID("A")
        b = EntityID("B")
        c = EntityID("C")
        d = EntityID("D")

        t1 = TransformationDefinition.create(
            mappings={
                a: b,
            },
        )

        t2 = TransformationDefinition.create(
            mappings={
                b: c,
            },
        )

        t3 = TransformationDefinition.create(
            mappings={
                c: d,
            },
        )

        self.assertEqual(
            len(t1.mappings),
            1,
        )
        self.assertEqual(
            len(t2.mappings),
            1,
        )
        self.assertEqual(
            len(t3.mappings),
            1,
        )

        #
        # Expected:
        #
        # (T1 ∘ T2) ∘ T3
        #
        # ==
        #
        # T1 ∘ (T2 ∘ T3)
        #
        # ==
        #
        # A → D
        #
