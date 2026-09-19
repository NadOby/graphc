"""Immutable semantic states."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import canonical_serialize
from .identity import EntityID, StateID
from .references import (
    CrossStateReference,
    StaleReference,
    Reference,
    make_reference,
)
from .values import Value, version_id_for


def _state_content(
    values: Mapping[EntityID, Value],
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

    return (
        b"STATE"
        + len(canonical_values).to_bytes(
            8,
            byteorder="big",
            signed=False,
        )
        + b"".join(
            entity + content
            for entity, content in canonical_values
        )
    )


@dataclass(frozen=True)
class State:
    """Immutable semantic state.

    State identity is derived only from semantic content.
    Transformation mappings and provenance are not state content.
    """

    id: StateID
    values: Mapping[EntityID, Value]

    @staticmethod
    def create(
        values: Mapping[EntityID, Value],
    ) -> "State":
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
            immutable_values
        )

        state_id = StateID(
            sha256(encoded).hexdigest()
        )

        return State(
            id=state_id,
            values=immutable_values,
        )

    def reference(
        self,
        entity: EntityID,
    ) -> Reference:
        if entity not in self.values:
            raise KeyError(
                f"{entity.value} is absent from {self.id.value}"
            )

        return make_reference(
            self.id,
            entity,
            self.values[entity],
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

    def contains(
        self,
        entity: EntityID,
    ) -> bool:
        return entity in self.values

    def with_changes(
        self,
        changes: Mapping[EntityID, Any],
    ) -> "State":
        values = dict(self.values)

        for entity, content in changes.items():
            values[entity] = Value(
                entity,
                content,
            )

        return State.create(values)
