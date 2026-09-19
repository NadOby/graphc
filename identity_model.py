"""Executable reference model for SEMIROH identity and references.

This model distinguishes:

- EntityID: conceptual identity across semantic states.
- VersionID: identity of one exact semantic version of an entity.
- StateID: identity of one exact immutable semantic state.
- Reference: a state-pinned, version-pinned reference to an entity.

This is a semantic reference model, not a compiler implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, order=True)
class EntityID:
    value: str


@dataclass(frozen=True, order=True)
class VersionID:
    value: str


@dataclass(frozen=True, order=True)
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
    """Serialize supported semantic values deterministically."""

    if value is None:
        return b"N"

    if isinstance(value, bool):
        return b"B" + (b"\x01" if value else b"\x00")

    if isinstance(value, int):
        return b"I" + _encode_bytes(
            str(value).encode("ascii")
        )

    if isinstance(value, str):
        return b"S" + _encode_text(value)

    if isinstance(value, bytes):
        return b"Y" + _encode_bytes(value)

    if isinstance(value, EntityID):
        return b"E" + _encode_text(value.value)

    if isinstance(value, VersionID):
        return b"V" + _encode_text(value.value)

    if isinstance(value, StateID):
        return b"T" + _encode_text(value.value)

    if isinstance(value, EntityMapping):
        return (
            b"R"
            + canonical_serialize(value.source_state)
            + canonical_serialize(value.source_entity)
            + canonical_serialize(value.destination_entity)
        )

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
        "unsupported value for canonical semantic serialization: "
        f"{type(value).__name__}"
    )


def canonicalize(value: Any) -> Any:
    """Convert supported semantic values to immutable deterministic data."""

    if value is None or isinstance(value, (bool, int, str)):
        return value

    if isinstance(value, bytes):
        return (
            "__type__",
            "bytes",
            value.hex(),
        )

    if isinstance(value, EntityID):
        return (
            "__type__",
            "entity_id",
            value.value,
        )

    if isinstance(value, VersionID):
        return (
            "__type__",
            "version_id",
            value.value,
        )

    if isinstance(value, StateID):
        return (
            "__type__",
            "state_id",
            value.value,
        )

    if isinstance(value, EntityMapping):
        return (
            "__type__",
            "entity_mapping",
            canonicalize(value.source_state),
            canonicalize(value.source_entity),
            canonicalize(value.destination_entity),
        )

    if isinstance(value, tuple):
        return (
            "__type__",
            "tuple",
            tuple(
                canonicalize(item)
                for item in value
            ),
        )

    if isinstance(value, list):
        return (
            "__type__",
            "list",
            tuple(
                canonicalize(item)
                for item in value
            ),
        )

    if isinstance(value, Mapping):
        items = [
            (
                canonicalize(key),
                canonicalize(item),
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
        "unsupported value for canonical semantic serialization: "
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
    def create(
        entity: EntityID,
        content: Any,
    ) -> Value:
        return Value(entity, content)


def version_id_for(value: Value) -> VersionID:
    """Derive an exact version identity from entity and semantic content."""

    encoded = (
        b"VERSION"
        + canonical_serialize(value.entity)
        + canonical_serialize(value.content)
    )

    return VersionID(
        sha256(encoded).hexdigest()
    )


class CrossStateReference(ValueError):
    pass


class StaleReference(ValueError):
    pass


class MissingEntityMapping(ValueError):
    pass


@dataclass(frozen=True)
class Reference:
    """State-pinned and version-pinned semantic reference."""

    state: StateID
    entity: EntityID
    version: VersionID


@dataclass(frozen=True)
class EntityMapping:
    """Explicit identity-continuation relation across states."""

    source_state: StateID
    source_entity: EntityID
    destination_entity: EntityID


def _state_content(
    values: Mapping[EntityID, Value],
    mappings: tuple[EntityMapping, ...],
) -> bytes:
    canonical_values = [
        (
            canonical_serialize(entity),
            canonical_serialize(values[entity].content),
        )
        for entity in sorted(values)
    ]

    canonical_values.sort(
        key=lambda item: item[0]
    )

    canonical_mappings = sorted(
        canonical_serialize(mapping)
        for mapping in mappings
    )

    return (
        b"STATE"
        + _encode_length(len(canonical_values))
        + b"".join(
            entity + content
            for entity, content in canonical_values
        )
        + b"MAPPINGS"
        + _encode_length(len(canonical_mappings))
        + b"".join(canonical_mappings)
    )


@dataclass(frozen=True)
class State:
    """Immutable semantic state with deterministic content identity."""

    id: StateID
    values: Mapping[EntityID, Value]
    mappings: tuple[EntityMapping, ...]

    @staticmethod
    def create(
        values: Mapping[EntityID, Value],
    ) -> State:
        for entity, value in values.items():
            if value.entity != entity:
                raise ValueError(
                    f"value entity {value.entity.value} does not match "
                    f"state key {entity.value}"
                )

        immutable_values = MappingProxyType(
            dict(values)
        )

        encoded = _state_content(
            immutable_values,
            (),
        )

        state_id = StateID(
            sha256(encoded).hexdigest()
        )

        return State(
            state_id,
            immutable_values,
            (),
        )

    @staticmethod
    def _from_values_and_mappings(
        values: Mapping[EntityID, Value],
        mapping_pairs: Mapping[EntityID, EntityID],
        source_state: StateID,
    ) -> State:
        immutable_values = MappingProxyType(
            dict(values)
        )

        mappings = tuple(
            EntityMapping(
                source_state=source_state,
                source_entity=source_entity,
                destination_entity=destination_entity,
            )
            for source_entity, destination_entity
            in sorted(mapping_pairs.items())
        )

        encoded = _state_content(
            immutable_values,
            mappings,
        )

        state_id = StateID(
            sha256(encoded).hexdigest()
        )

        return State(
            state_id,
            immutable_values,
            mappings,
        )

    def reference(
        self,
        entity: EntityID,
    ) -> Reference:
        if entity not in self.values:
            raise KeyError(
                f"{entity.value} is absent from {self.id.value}"
            )

        value = self.values[entity]

        return Reference(
            state=self.id,
            entity=entity,
            version=version_id_for(value),
        )

    def resolve(
        self,
        reference: Reference,
    ) -> Value:
        if reference.state != self.id:
            raise CrossStateReference(
                f"reference belongs to {reference.state.value}, "
                f"not {self.id.value}"
            )

        try:
            value = self.values[reference.entity]
        except KeyError as exc:
            raise KeyError(
                f"{reference.entity.value} is absent from "
                f"{self.id.value}"
            ) from exc

        actual_version = version_id_for(value)

        if actual_version != reference.version:
            raise StaleReference(
                f"reference expects version {reference.version.value}, "
                f"but state contains {actual_version.value}"
            )

        return value

    def mapped_entity(
        self,
        source_reference: Reference,
    ) -> EntityID:
        matches = [
            mapping.destination_entity
            for mapping in self.mappings
            if (
                mapping.source_state
                == source_reference.state
                and mapping.source_entity
                == source_reference.entity
            )
        ]

        if not matches:
            raise MissingEntityMapping(
                f"no explicit mapping from "
                f"{source_reference.entity.value}@"
                f"{source_reference.state.value} to "
                f"{self.id.value}"
            )

        if len(matches) > 1:
            raise ValueError(
                f"multiple destination entities mapped from "
                f"{source_reference.entity.value}@"
                f"{source_reference.state.value}"
            )

        return matches[0]


def transfer_reference(
    reference: Reference,
    destination: State,
) -> Reference:
    """Transfer a reference through an explicit identity mapping."""

    destination_entity = destination.mapped_entity(
        reference
    )

    if destination_entity not in destination.values:
        raise KeyError(
            f"{destination_entity.value} is absent from "
            f"{destination.id.value}"
        )

    destination_value = destination.values[
        destination_entity
    ]

    return Reference(
        state=destination.id,
        entity=destination_entity,
        version=version_id_for(destination_value),
    )


def rebind_reference(
    reference: Reference,
    destination: State,
    destination_entity: EntityID,
) -> Reference:
    """Explicitly bind to a chosen destination entity.

    Rebinding does not preserve conceptual identity.
    """

    if destination_entity not in destination.values:
        raise KeyError(
            f"{destination_entity.value} is absent from "
            f"{destination.id.value}"
        )

    destination_value = destination.values[
        destination_entity
    ]

    return Reference(
        state=destination.id,
        entity=destination_entity,
        version=version_id_for(destination_value),
    )


def project_entity(
    reference: Reference,
) -> EntityID:
    """Project a pinned reference back to conceptual entity identity."""

    return reference.entity


def transform(
    state: State,
    changes: Mapping[EntityID, Any],
) -> State:
    """Produce a new immutable state.

    Existing entities retain conceptual identity, but their versions
    change when their semantic contents change.
    """

    values = dict(state.values)

    for entity, content in changes.items():
        values[entity] = Value(
            entity,
            content,
        )

    mapping_pairs = {
        entity: entity
        for entity in state.values
        if entity in values
    }

    return State._from_values_and_mappings(
        values,
        mapping_pairs,
        state.id,
    )


def transform_with_mapping(
    state: State,
    changes: Mapping[EntityID, Any],
    entity_mappings: Mapping[EntityID, EntityID],
) -> State:
    """Produce a new state with explicit source-to-destination mappings."""

    values = dict(state.values)

    for entity, content in changes.items():
        values[entity] = Value(
            entity,
            content,
        )

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

    return State._from_values_and_mappings(
        values,
        entity_mappings,
        state.id,
    )


def semantic_equal(
    left: Value,
    right: Value,
) -> bool:
    """Semantic equality; conceptual identity is irrelevant."""

    return left.content == right.content


def same_entity(
    left: Value,
    right: Value,
) -> bool:
    """Conceptual identity comparison."""

    return left.entity == right.entity


def same_version(
    left: Value,
    right: Value,
) -> bool:
    """Exact semantic-version comparison."""

    return version_id_for(left) == version_id_for(right)


def test_entity_version_changes_when_content_changes() -> None:
    foo = EntityID("foo")

    first = Value.create(foo, 1)
    second = Value.create(foo, 2)

    assert first.entity == second.entity
    assert version_id_for(first) != version_id_for(second)
    assert same_entity(first, second)
    assert not same_version(first, second)


def test_identical_entity_versions_have_identical_version_ids() -> None:
    foo = EntityID("foo")

    first = Value.create(foo, 42)
    second = Value.create(foo, 42)

    assert version_id_for(first) == version_id_for(second)
    assert semantic_equal(first, second)
    assert same_entity(first, second)


def test_version_id_is_history_independent() -> None:
    foo = EntityID("foo")

    direct = Value.create(foo, 42)

    intermediate = Value.create(foo, 1)

    assert version_id_for(direct) == version_id_for(
        Value.create(foo, 42)
    )

    assert version_id_for(direct) != version_id_for(
        intermediate
    )


def test_reference_is_version_pinned() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    reference = s0.reference(foo)

    assert reference.state == s0.id
    assert reference.entity == foo
    assert reference.version == version_id_for(
        s0.values[foo]
    )


def test_stale_reference_cannot_resolve_after_version_change() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    s1 = transform(s0, {
        foo: 2,
    })

    stale_reference = s0.reference(foo)

    assert stale_reference.entity == foo
    assert stale_reference.version != version_id_for(
        s1.values[foo]
    )

    try:
        s1.resolve(stale_reference)
    except CrossStateReference:
        pass
    else:
        raise AssertionError(
            "reference crossed state boundary"
        )


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


def test_explicit_mapping_preserves_entity_identity() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    s1 = transform_with_mapping(
        s0,
        {foo: 2},
        {foo: foo},
    )

    source_reference = s0.reference(foo)

    destination_reference = transfer_reference(
        source_reference,
        s1,
    )

    assert project_entity(source_reference) == foo
    assert project_entity(destination_reference) == foo

    assert destination_reference.entity == foo
    assert destination_reference.version == version_id_for(
        s1.values[foo]
    )

    assert source_reference.version != destination_reference.version


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
    assert destination_reference.version == version_id_for(
        s1.values[bar]
    )

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
    assert destination_reference.version == version_id_for(
        s1.values[bar]
    )

    assert project_entity(destination_reference) == bar
    assert project_entity(destination_reference) != (
        project_entity(source_reference)
    )


def test_version_fast_path_for_exact_value() -> None:
    foo = EntityID("foo")

    s0 = State.create({
        foo: Value.create(foo, 42),
    })

    s1 = State.create({
        foo: Value.create(foo, 42),
    })

    source = s0.reference(foo)
    destination = s1.reference(foo)

    assert source.entity == destination.entity
    assert source.version == destination.version
    assert semantic_equal(
        s0.resolve(source),
        s1.resolve(destination),
    )


def test_same_entity_different_versions_are_not_equal() -> None:
    foo = EntityID("foo")

    first = Value.create(foo, 1)
    second = Value.create(foo, 2)

    assert same_entity(first, second)
    assert not semantic_equal(first, second)
    assert not same_version(first, second)


def test_different_entities_same_version_content_are_equal() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    first = Value.create(foo, 42)
    second = Value.create(bar, 42)

    assert not same_entity(first, second)
    assert semantic_equal(first, second)
    assert version_id_for(first) != version_id_for(second)


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


def test_state_identity_changes_with_semantic_mapping_metadata() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")
    baz = EntityID("baz")

    s0 = State.create({
        foo: Value.create(foo, 1),
    })

    first = transform_with_mapping(
        s0,
        {
            bar: 2,
            baz: 3,
        },
        {
            foo: bar,
        },
    )

    second = transform_with_mapping(
        s0,
        {
            bar: 2,
            baz: 3,
        },
        {
            foo: baz,
        },
    )

    assert first.id != second.id


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


def test_original_input_mapping_cannot_mutate_state() -> None:
    foo = EntityID("foo")

    values = {
        foo: Value.create(foo, 1),
    }

    state = State.create(values)

    values[foo] = Value.create(foo, 2)

    assert state.values[foo].content == 1


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


def run_all_tests() -> None:
    test_entity_version_changes_when_content_changes()
    test_identical_entity_versions_have_identical_version_ids()
    test_version_id_is_history_independent()
    test_reference_is_version_pinned()
    test_stale_reference_cannot_resolve_after_version_change()
    test_cross_state_reference_does_not_rebind()
    test_transfer_requires_explicit_mapping()
    test_explicit_mapping_preserves_entity_identity()
    test_explicit_mapping_can_rename_entity()
    test_rebind_is_not_transfer()
    test_version_fast_path_for_exact_value()
    test_same_entity_different_versions_are_not_equal()
    test_different_entities_same_version_content_are_equal()
    test_state_identity_is_history_independent()
    test_state_identity_changes_with_semantic_mapping_metadata()
    test_state_values_are_immutable()
    test_value_content_is_immutable()
    test_direct_value_construction_is_immutable()
    test_original_input_mapping_cannot_mutate_state()
    test_canonical_serialization_is_type_sensitive()
    test_canonical_serialization_is_length_delimited()
    test_canonical_serialization_handles_nested_values()
    test_canonical_serialization_distinguishes_sequence_types()
    test_canonical_serialization_distinguishes_map_keys_by_type()
    test_state_identity_uses_canonical_serialization()
    test_state_identity_is_full_sha256()
    test_state_rejects_entity_key_mismatch()


if __name__ == "__main__":
    run_all_tests()
    print("All identity/version/reference tests passed.")
    
