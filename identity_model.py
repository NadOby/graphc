"""Minimal executable reference model for GraphC semantic identity/state.

This is a semantic reference model, not a compiler implementation.
Its purpose is to stress-test the distinction between conceptual entity
identity, immutable semantic state, exact references, and equality.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, order=True)
class EntityID:
    value: str


@dataclass(frozen=True)
class StateID:
    value: str


@dataclass(frozen=True)
class Entity:
    id: EntityID


def _encode_length(length: int) -> bytes:
    return length.to_bytes(8, byteorder="big", signed=False)


def _encode_bytes(value: bytes) -> bytes:
    return _encode_length(len(value)) + value


def _encode_text(value: str) -> bytes:
    return _encode_bytes(value.encode("utf-8"))


def canonical_serialize(value: Any) -> bytes:
    """Serialize a supported semantic value deterministically.

    The encoding is explicit and type-tagged. It does not depend on
    Python's object representation or JSON formatting.
    """

    if value is None:
        return b"N"

    if isinstance(value, bool):
        return b"B" + (b"\x01" if value else b"\x00")

    if isinstance(value, int):
        encoded = str(value).encode("ascii")
        return b"I" + _encode_bytes(encoded)

    if isinstance(value, str):
        return b"S" + _encode_text(value)

    if isinstance(value, bytes):
        return b"Y" + _encode_bytes(value)

    if isinstance(value, EntityID):
        return b"E" + _encode_text(value.value)

    if isinstance(value, StateID):
        return b"T" + _encode_text(value.value)

    if isinstance(value, tuple):
        encoded_items = [
            canonical_serialize(item)
            for item in value
        ]

        return (
            b"U"
            + _encode_length(len(encoded_items))
            + b"".join(encoded_items)
        )

    if isinstance(value, list):
        encoded_items = [
            canonical_serialize(item)
            for item in value
        ]

        return (
            b"L"
            + _encode_length(len(encoded_items))
            + b"".join(encoded_items)
        )

    if isinstance(value, Mapping):
        encoded_items = [
            (
                canonical_serialize(key),
                canonical_serialize(item),
            )
            for key, item in value.items()
        ]

        encoded_items.sort(key=lambda item: item[0])

        return (
            b"M"
            + _encode_length(len(encoded_items))
            + b"".join(
                key + item
                for key, item in encoded_items
            )
        )

    raise TypeError(
        f"unsupported value for canonical semantic serialization: "
        f"{type(value).__name__}"
    )


def canonicalize(value: Any) -> Any:
    """Convert supported semantic values to immutable deterministic data."""

    if value is None or isinstance(value, (bool, int, str)):
        return value

    if isinstance(value, bytes):
        return ("__type__", "bytes", value.hex())

    if isinstance(value, EntityID):
        return ("__type__", "entity_id", value.value)

    if isinstance(value, StateID):
        return ("__type__", "state_id", value.value)

    if isinstance(value, tuple):
        return (
            "__type__",
            "tuple",
            tuple(canonicalize(item) for item in value),
        )

    if isinstance(value, list):
        return (
            "__type__",
            "list",
            tuple(canonicalize(item) for item in value),
        )

    if isinstance(value, Mapping):
        items = [
            (
                canonicalize(key),
                canonicalize(item)
            )
            for key, item in value.items()
        ]

        items.sort(
            key=lambda item: canonical_serialize(item[0])
        )

        return (
            "__type__",
            "map",
            tuple(items),
        )

    raise TypeError(
        f"unsupported value for canonical semantic serialization: "
        f"{type(value).__name__}"
    )


@dataclass(frozen=True)
class Value:
    """Immutable semantic value."""

    entity: EntityID
    content: Any

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "content",
            canonicalize(self.content),
        )

    @staticmethod
    def create(entity: EntityID, content: Any) -> Value:
        return Value(entity, content)


@dataclass(frozen=True)
class Reference:
    """Exact semantic reference: entity as represented by one state."""

    state: StateID
    entity: EntityID


class CrossStateReference(ValueError):
    pass


class MissingEntityMapping(ValueError):
    pass


@dataclass(frozen=True)
class EntityMapping:
    """Explicit conceptual identity mapping between two semantic states."""

    source_state: StateID
    source_entity: EntityID
    destination_state: StateID
    destination_entity: EntityID


@dataclass(frozen=True)
class State:
    """Immutable semantic state with deterministic content-derived identity."""

    id: StateID
    values: Mapping[EntityID, Value]
    mappings: tuple[EntityMapping, ...]

    @staticmethod
    def create(
        values: Mapping[EntityID, Value],
        mappings: tuple[EntityMapping, ...] = (),
    ) -> State:
        for entity, value in values.items():
            if value.entity != entity:
                raise ValueError(
                    f"value entity {value.entity.value} does not match "
                    f"state key {entity.value}"
                )

        for mapping in mappings:
            if mapping.destination_state.value:
                raise ValueError(
                    "state mappings must be constructed before "
                    "destination StateID is known"
                )

        canonical_values = [
            (
                canonical_serialize(entity),
                canonical_serialize(values[entity].content),
            )
            for entity in sorted(values)
        ]

        canonical_values.sort(key=lambda item: item[0])

        encoded = (
            b"STATE"
            + _encode_length(len(canonical_values))
            + b"".join(
                entity + content
                for entity, content in canonical_values
            )
        )

        state_id = StateID(
            sha256(encoded).hexdigest()
        )

        immutable_values = MappingProxyType(dict(values))

        return State(
            state_id,
            immutable_values,
            tuple(mappings),
        )

    def reference(self, entity: EntityID) -> Reference:
        if entity not in self.values:
            raise KeyError(
                f"{entity.value} is absent from {self.id.value}"
            )

        return Reference(self.id, entity)

    def resolve(self, reference: Reference) -> Value:
        if reference.state != self.id:
            raise CrossStateReference(
                f"reference belongs to {reference.state.value}, "
                f"not {self.id.value}"
            )

        try:
            return self.values[reference.entity]
        except KeyError as exc:
            raise KeyError(
                f"{reference.entity.value} is absent from {self.id.value}"
            ) from exc

    def mapped_entity(
        self,
        source_reference: Reference,
    ) -> EntityID:
        for mapping in self.mappings:
            if (
                mapping.source_state == source_reference.state
                and mapping.source_entity == source_reference.entity
                and mapping.destination_state == self.id
            ):
                return mapping.destination_entity

        raise MissingEntityMapping(
            f"no explicit mapping from "
            f"{source_reference.entity.value}@"
            f"{source_reference.state.value} to "
            f"{self.id.value}"
        )


def transfer_reference(
    reference: Reference,
    destination: State,
) -> Reference:
    """Transfer a reference through an explicit identity mapping."""

    destination_entity = destination.mapped_entity(reference)

    if destination_entity not in destination.values:
        raise KeyError(
            f"{destination_entity.value} is absent from "
            f"{destination.id.value}"
        )

    return Reference(
        destination.id,
        destination_entity,
    )


def rebind_reference(
    reference: Reference,
    destination: State,
    destination_entity: EntityID,
) -> Reference:
    """Explicitly establish a reference to a chosen destination entity.

    This does not preserve conceptual identity and therefore is not a
    transfer of the original entity.
    """

    if destination_entity not in destination.values:
        raise KeyError(
            f"{destination_entity.value} is absent from "
            f"{destination.id.value}"
        )

    return Reference(
        destination.id,
        destination_entity,
    )


def transform(
    state: State,
    changes: Mapping[EntityID, Any],
) -> State:
    """Produce a new immutable state without modifying the source state.

    Existing entities retain their conceptual identity automatically.
    """

    values = dict(state.values)

    for entity, content in changes.items():
        values[entity] = Value(entity, content)

    canonical_values = [
        (
            canonical_serialize(entity),
            canonical_serialize(values[entity].content),
        )
        for entity in sorted(values)
    ]

    canonical_values.sort(key=lambda item: item[0])

    encoded = (
        b"STATE"
        + _encode_length(len(canonical_values))
        + b"".join(
            entity + content
            for entity, content in canonical_values
        )
    )

    state_id = StateID(
        sha256(encoded).hexdigest()
    )

    mappings = tuple(
        EntityMapping(
            source_state=state.id,
            source_entity=entity,
            destination_state=state_id,
            destination_entity=entity,
        )
        for entity in values
        if entity in state.values
    )

    return State(
        state_id,
        MappingProxyType(dict(values)),
        mappings,
    )


def transform_with_mapping(
    state: State,
    changes: Mapping[EntityID, Any],
    entity_mappings: Mapping[EntityID, EntityID],
) -> State:
    """Produce a new state with explicit source-to-destination mappings."""

    values = dict(state.values)

    for entity, content in changes.items():
        values[entity] = Value(entity, content)

    for source_entity, destination_entity in entity_mappings.items():
        if source_entity not in state.values:
            raise KeyError(
                f"{source_entity.value} is absent from "
                f"{state.id.value}"
            )

        if destination_entity not in values:
            raise KeyError(
                f"{destination_entity.value} is absent from "
                f"destination state"
            )

    canonical_values = [
        (
            canonical_serialize(entity),
            canonical_serialize(values[entity].content),
        )
        for entity in sorted(values)
    ]

    canonical_values.sort(key=lambda item: item[0])

    encoded = (
        b"STATE"
        + _encode_length(len(canonical_values))
        + b"".join(
            entity + content
            for entity, content in canonical_values
        )
    )

    state_id = StateID(
        sha256(encoded).hexdigest()
    )

    mappings = tuple(
        EntityMapping(
            source_state=state.id,
            source_entity=source_entity,
            destination_state=state_id,
            destination_entity=destination_entity,
        )
        for source_entity, destination_entity
        in entity_mappings.items()
    )

    return State(
        state_id,
        MappingProxyType(dict(values)),
        mappings,
    )


def semantic_equal(left: Value, right: Value) -> bool:
    """Value equality; conceptual identity is deliberately irrelevant."""

    return left.content == right.content


def same_entity(left: Value, right: Value) -> bool:
    """Conceptual identity comparison; deliberately not value equality."""

    return left.entity == right.entity


def test_evolution() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    old_reference = s0.reference(foo)

    s1 = transform(s0, {
        foo: 2,
    })

    new_reference = transfer_reference(
        old_reference,
        s1,
    )

    assert s0.resolve(old_reference).content == 1
    assert s1.resolve(new_reference).content == 2
    assert s0.id != s1.id
    assert new_reference.entity == foo


def test_branching() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    left = transform(s0, {
        foo: 2,
    })

    right = transform(s0, {
        foo: 3,
    })

    assert left.id != right.id
    assert left.values[foo].content == 2
    assert right.values[foo].content == 3

    left_reference = transfer_reference(
        s0.reference(foo),
        left,
    )

    right_reference = transfer_reference(
        s0.reference(foo),
        right,
    )

    assert left_reference.entity == foo
    assert right_reference.entity == foo
    assert left.resolve(left_reference).content == 2
    assert right.resolve(right_reference).content == 3


def test_cross_state_reference_does_not_rebind() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    s1 = transform(s0, {
        foo: 2,
    })

    try:
        s1.resolve(s0.reference(foo))
    except CrossStateReference:
        pass
    else:
        raise AssertionError(
            "cross-state reference silently rebound"
        )


def test_transfer_requires_explicit_mapping() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    s1 = State.create({
        foo: Value.create(foo, 2),
    })

    try:
        transfer_reference(
            s0.reference(foo),
            s1,
        )
    except MissingEntityMapping:
        pass
    else:
        raise AssertionError(
            "transfer accepted implicit identity continuation"
        )


def test_explicit_mapping_preserves_identity() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    s1 = transform_with_mapping(
        s0,
        {foo: 2},
        {foo: foo},
    )

    destination_reference = transfer_reference(
        s0.reference(foo),
        s1,
    )

    assert destination_reference.entity == foo
    assert s1.resolve(destination_reference).content == 2


def test_explicit_mapping_can_rename_entity() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    s1 = transform_with_mapping(
        s0,
        {bar: 2},
        {foo: bar},
    )

    destination_reference = transfer_reference(
        s0.reference(foo),
        s1,
    )

    assert destination_reference.entity == bar
    assert s1.resolve(destination_reference).content == 2


def test_rebind_is_not_transfer() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    s1 = State.create({
        bar: Value.create(bar, 99),
    })

    source_reference = s0.reference(foo)

    destination_reference = rebind_reference(
        source_reference,
        s1,
        bar,
    )

    assert destination_reference.state == s1.id
    assert destination_reference.entity == bar
    assert s1.resolve(destination_reference).content == 99
    assert destination_reference.entity != source_reference.entity


def test_identity_and_equality_are_distinct() -> None:
    foo = EntityID("foo")

    s1 = State.create({
        foo: Value.create(foo, 2),
    })

    s2 = State.create({
        foo: Value.create(foo, 3),
    })

    assert same_entity(
        s1.values[foo],
        s2.values[foo],
    )

    assert not semantic_equal(
        s1.values[foo],
        s2.values[foo],
    )

    bar = EntityID("bar")

    s3 = State.create({
        foo: Value.create(foo, 42),
        bar: Value.create(bar, 42),
    })

    assert not same_entity(
        s3.values[foo],
        s3.values[bar],
    )

    assert semantic_equal(
        s3.values[foo],
        s3.values[bar],
    )


def test_state_identity_is_history_independent() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    first = State.create({
        foo: Value.create(foo, 42),
        bar: Value.create(bar, 10),
    })

    second = State.create({
        bar: Value.create(bar, 10),
        foo: Value.create(foo, 42),
    })

    assert first.id == second.id


def test_transform_does_not_mutate_source() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    s1 = transform(s0, {
        foo: 2,
    })

    assert s0.values[foo].content == 1
    assert s1.values[foo].content == 2


def test_canonical_serialization_is_type_sensitive() -> None:
    assert canonical_serialize(1) != canonical_serialize(True)
    assert canonical_serialize(1) != canonical_serialize("1")
    assert canonical_serialize("1") != canonical_serialize(b"1")


def test_canonical_serialization_is_length_delimited() -> None:
    assert canonical_serialize("ab") != canonical_serialize("a")
    assert canonical_serialize("abc") != canonical_serialize("ab")


def test_canonical_serialization_handles_nested_values() -> None:
    first = {
        "numbers": [1, 2, 3],
        "nested": ("a", b"bc"),
    }

    second = {
        "nested": ("a", b"bc"),
        "numbers": [1, 2, 3],
    }

    assert canonical_serialize(first) == canonical_serialize(second)


def test_canonical_serialization_distinguishes_sequence_types() -> None:
    assert canonical_serialize([1, 2]) != canonical_serialize((1, 2))


def test_canonical_serialization_distinguishes_map_keys_by_type() -> None:
    int_key = {1: "value"}
    bool_key = {True: "value"}

    assert canonical_serialize(int_key) != canonical_serialize(bool_key)


def test_state_identity_uses_canonical_serialization() -> None:
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

    assert first.id == second.id


def test_state_identity_is_full_sha256() -> None:
    foo = EntityID("foo")

    state = State.create({
        foo: Value.create(foo, 1),
    })

    assert len(state.id.value) == 64
    assert all(
        character in "0123456789abcdef"
        for character in state.id.value
    )


def test_state_rejects_entity_key_mismatch() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    try:
        State.create({
            foo: Value.create(bar, 42),
        })
    except ValueError:
        pass
    else:
        raise AssertionError(
            "state accepted mismatched entity key and value identity"
        )


def test_state_accepts_matching_entity_key() -> None:
    foo = EntityID("foo")

    state = State.create({
        foo: Value.create(foo, 42),
    })

    assert state.values[foo].entity == foo


def test_state_values_are_immutable() -> None:
    foo = EntityID("foo")

    state = State.create({
        foo: Value.create(foo, 1),
    })

    try:
        state.values[foo] = Value.create(foo, 2)
    except TypeError:
        pass
    else:
        raise AssertionError(
            "semantic state values are mutable"
        )

    assert state.values[foo].content == 1


def test_original_input_mapping_cannot_mutate_state() -> None:
    foo = EntityID("foo")

    values = {
        foo: Value.create(foo, 1),
    }

    state = State.create(values)

    values[foo] = Value.create(foo, 2)

    assert state.values[foo].content == 1


def test_value_content_is_immutable() -> None:
    foo = EntityID("foo")

    original = [1, 2, 3]
    value = Value.create(foo, original)

    original.append(4)

    assert value.content == (
        "__type__",
        "list",
        (1, 2, 3),
    )

    try:
        value.content[2] += (4,)
    except TypeError:
        pass
    else:
        raise AssertionError(
            "canonical semantic value content is mutable"
        )


def test_direct_value_construction_is_immutable() -> None:
    foo = EntityID("foo")

    original = [1, 2, 3]
    value = Value(foo, original)

    original.append(4)

    assert value.content == (
        "__type__",
        "list",
        (1, 2, 3),
    )


def run_all_tests() -> None:
    test_evolution()
    test_branching()
    test_cross_state_reference_does_not_rebind()
    test_transfer_requires_explicit_mapping()
    test_explicit_mapping_preserves_identity()
    test_explicit_mapping_can_rename_entity()
    test_rebind_is_not_transfer()
    test_identity_and_equality_are_distinct()
    test_state_identity_is_history_independent()
    test_transform_does_not_mutate_source()
    test_canonical_serialization_is_type_sensitive()
    test_canonical_serialization_is_length_delimited()
    test_canonical_serialization_handles_nested_values()
    test_canonical_serialization_distinguishes_sequence_types()
    test_canonical_serialization_distinguishes_map_keys_by_type()
    test_state_identity_uses_canonical_serialization()
    test_state_identity_is_full_sha256()
    test_state_rejects_entity_key_mismatch()
    test_state_accepts_matching_entity_key()
    test_state_values_are_immutable()
    test_original_input_mapping_cannot_mutate_state()
    test_value_content_is_immutable()
    test_direct_value_construction_is_immutable()


if __name__ == "__main__":
    run_all_tests()
    print("All identity/reference tests passed.")
