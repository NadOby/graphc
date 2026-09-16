"""Minimal executable reference model for GraphC semantic identity/state.

This is a semantic reference model, not a compiler implementation.
Its purpose is to stress-test the distinction between conceptual entity
identity, immutable semantic state, exact references, and equality.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
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


@dataclass(frozen=True)
class Value:
    """Immutable semantic value."""

    entity: EntityID
    content: Any

    @staticmethod
    def create(entity: EntityID, content: Any) -> Value:
        return Value(entity, canonicalize(content))


@dataclass(frozen=True)
class Reference:
    """Exact semantic reference: entity as represented by one state."""

    state: StateID
    entity: EntityID


class CrossStateReference(ValueError):
    pass


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
                canonicalize(item),
            )
            for key, item in value.items()
        ]

        items.sort(
            key=lambda item: json.dumps(
                item[0],
                sort_keys=True,
                separators=(",", ":"),
            )
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
class State:
    """Immutable semantic state with deterministic content-derived identity."""

    id: StateID
    values: Mapping[EntityID, Value]

    @staticmethod
    def create(values: Mapping[EntityID, Value]) -> State:
        normalized = {
            entity.value: values[entity].content
            for entity in sorted(values)
        }

        encoded = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
        )

        state_id = StateID(
            sha256(encoded.encode("utf-8")).hexdigest()[:16]
        )

        immutable_values = MappingProxyType(dict(values))

        return State(state_id, immutable_values)

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


def transform(
    state: State,
    changes: Mapping[EntityID, Any],
) -> State:
    """Produce a new immutable state without modifying the source state."""

    values = dict(state.values)

    for entity, content in changes.items():
        values[entity] = Value.create(entity, content)

    return State.create(values)


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

    assert s0.resolve(old_reference).content == 1
    assert s1.resolve(s1.reference(foo)).content == 2
    assert s0.id != s1.id


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
        foo:
