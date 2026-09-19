"""Semantic state transformations and explicit identity mappings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .identity import EntityID, StateID
from .references import (
    MissingEntityMapping,
    Reference,
)
from .state import State
from .values import version_id_for


@dataclass(frozen=True)
class EntityMapping:
    """One explicit identity-continuation relation across states."""

    source_state: StateID
    source_entity: EntityID
    destination_entity: EntityID


@dataclass(frozen=True)
class TransformResult:
    """Immutable result of a state transformation.

    Mapping and provenance belong to the transition, not either state.
    """

    source: State
    destination: State
    mappings: tuple[EntityMapping, ...]
    provenance: Any = None

    def mapped_entity(
        self,
        reference: Reference,
    ) -> EntityID:
        matches = [
            mapping.destination_entity
            for mapping in self.mappings
            if (
                mapping.source_state == reference.state
                and mapping.source_entity == reference.entity
            )
        ]

        if not matches:
            raise MissingEntityMapping(
                f"no explicit mapping from "
                f"{reference.entity.value}@{reference.state.value} "
                f"to {self.destination.id.value}"
            )

        if len(matches) > 1:
            raise ValueError(
                f"multiple destination entities mapped from "
                f"{reference.entity.value}@{reference.state.value}"
            )

        return matches[0]


def transform(
    state: State,
    changes: Mapping[EntityID, Any],
) -> State:
    """Produce a new immutable state without a transition mapping."""

    return state.with_changes(changes)


def transform_with_mapping(
    state: State,
    changes: Mapping[EntityID, Any],
    entity_mappings: Mapping[EntityID, EntityID],
    provenance: Any = None,
) -> TransformResult:
    """Produce a new state and an explicit transition mapping."""

    values = dict(state.values)

    for entity, content in changes.items():
        values[entity] = state.values[entity].__class__(
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

    destination = State.create(values)

    mappings = tuple(
        EntityMapping(
            source_state=state.id,
            source_entity=source_entity,
            destination_entity=destination_entity,
        )
        for source_entity, destination_entity
        in sorted(entity_mappings.items())
    )

    return TransformResult(
        source=state,
        destination=destination,
        mappings=mappings,
        provenance=provenance,
    )


def transfer_reference(
    reference: Reference,
    result: TransformResult,
) -> Reference:
    """Transfer a reference through an explicit transformation mapping."""

    destination_entity = result.mapped_entity(reference)

    destination = result.destination

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
