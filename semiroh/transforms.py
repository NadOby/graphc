"""Semantic state transformations and explicit identity mappings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .identity import EntityID, StateID
from .references import (
    AmbiguousEntityMapping,
    MissingEntityMapping,
    Reference,
)
from .state import State
from .values import Value, version_id_for


@dataclass(frozen=True)
class EntityMapping:
    """Explicit continuity relation from one source entity to zero or more destinations."""

    source_state: StateID
    source_entity: EntityID
    destination_entities: tuple[EntityID, ...]


@dataclass(frozen=True)
class TransformResult:
    """Immutable result of a state transformation.

    Mapping and provenance belong to the transition, not either state.
    """

    source: State
    destination: State
    mappings: tuple[EntityMapping, ...]
    provenance: Any = None

    def __post_init__(self) -> None:
        """Validate structural invariants of the transition mapping."""

        seen_sources: set[EntityID] = set()

        for mapping in self.mappings:
            if mapping.source_state != self.source.id:
                raise ValueError(
                    f"mapping source state {mapping.source_state.value} "
                    f"does not match source state {self.source.id.value}"
                )

            if mapping.source_entity not in self.source.values:
                raise ValueError(
                    f"mapping source entity {mapping.source_entity.value} "
                    f"is absent from source state"
                )

            if mapping.source_entity in seen_sources:
                raise ValueError(
                    f"multiple mapping records for "
                    f"{mapping.source_entity.value}"
                )

            seen_sources.add(mapping.source_entity)

            if len(mapping.destination_entities) != len(
                set(mapping.destination_entities)
            ):
                raise ValueError(
                    f"duplicate destination entities in mapping from "
                    f"{mapping.source_entity.value}"
                )

            if tuple(sorted(mapping.destination_entities)) != (
                mapping.destination_entities
            ):
                raise ValueError(
                    f"destination entities for {mapping.source_entity.value} "
                    f"are not canonically ordered"
                )

            for destination_entity in mapping.destination_entities:
                if destination_entity not in self.destination.values:
                    raise ValueError(
                        f"mapping destination entity "
                        f"{destination_entity.value} is absent from "
                        f"destination state"
                    )

        if tuple(
            sorted(
                self.mappings,
                key=lambda mapping: mapping.source_entity,
            )
        ) != self.mappings:
            raise ValueError(
                "entity mappings are not canonically ordered"
            )

    def mapped_entities(
        self,
        reference: Reference,
    ) -> tuple[EntityID, ...]:
        """Return all explicit destination entities for a reference."""

        matches = [
            mapping.destination_entities
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
                f"multiple mapping records for "
                f"{reference.entity.value}@{reference.state.value}"
            )

        return matches[0]

    def mapped_entity(
        self,
        reference: Reference,
    ) -> EntityID:
        """Return the unique destination entity.

        Raises MissingEntityMapping when the source entity disappears and
        AmbiguousEntityMapping when it maps to multiple destinations.
        """

        destinations = self.mapped_entities(reference)

        if not destinations:
            raise MissingEntityMapping(
                f"entity {reference.entity.value}@{reference.state.value} "
                f"has no destination in {self.destination.id.value}"
            )

        if len(destinations) > 1:
            raise AmbiguousEntityMapping(
                f"entity {reference.entity.value}@{reference.state.value} "
                f"maps to multiple destination entities"
            )

        return destinations[0]


def transform(
    state: State,
    changes: Mapping[EntityID, Any],
) -> State:
    """Produce a new immutable state without a transition mapping."""

    return state.with_changes(changes)


def transform_with_mapping(
    state: State,
    changes: Mapping[EntityID, Any],
    entity_mappings: Mapping[
        EntityID,
        EntityID | tuple[EntityID, ...],
    ],
    provenance: Any = None,
    ownership: Mapping[EntityID, Any] | None = None,
) -> TransformResult:
    """Produce a new state and an explicit continuity mapping.

    Each source entity may map to zero, one, or many destination entities.

    A destination entity may also be named by multiple source mappings,
    allowing many-to-one continuity.

    A source entity mapped to an empty tuple disappears from the destination
    state.

    Destination entities with no incoming mapping are newly created entities.
    Creation therefore requires no synthetic source-side entity.

    If ownership is omitted, the existing ownership relation is preserved
    except for edges involving entities that disappear.

    An explicit ownership mapping is used literally as the destination
    ownership relation. It must therefore reference only destination entities.

    Entity mappings do not implicitly modify ownership.
    """

    values = dict(state.values)

    for entity, content in changes.items():
        values[entity] = Value(
            entity,
            content,
        )

    normalized_mappings: list[EntityMapping] = []
    disappeared: set[EntityID] = set()

    for source_entity, destination_spec in entity_mappings.items():
        if source_entity not in state.values:
            raise KeyError(
                f"{source_entity.value} is absent from "
                f"{state.id.value}"
            )

        if isinstance(destination_spec, EntityID):
            destination_entities = (destination_spec,)
        else:
            destination_entities = tuple(destination_spec)

        if len(destination_entities) != len(
            set(destination_entities)
        ):
            raise ValueError(
                f"duplicate destination entities in mapping from "
                f"{source_entity.value}"
            )

        if not destination_entities:
            disappeared.add(source_entity)
        else:
            for destination_entity in destination_entities:
                if destination_entity not in values:
                    raise KeyError(
                        f"{destination_entity.value} is absent from "
                        f"destination state"
                    )

        normalized_mappings.append(
            EntityMapping(
                source_state=state.id,
                source_entity=source_entity,
                destination_entities=tuple(
                    sorted(destination_entities)
                ),
            )
        )

    for entity in disappeared:
        values.pop(entity, None)

    if ownership is None:
        destination_ownership = {
            owner: tuple(
                child
                for child in children
                if child not in disappeared
            )
            for owner, children in state.ownership.items()
            if owner not in disappeared
        }

        destination_ownership = {
            owner: children
            for owner, children in destination_ownership.items()
            if children
        }
    else:
        destination_ownership = ownership

    destination = State.create(
        values,
        destination_ownership,
    )

    mappings = tuple(
        sorted(
            normalized_mappings,
            key=lambda mapping: mapping.source_entity,
        )
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
    """Transfer a reference through a uniquely resolving mapping."""

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
