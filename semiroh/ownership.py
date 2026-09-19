"""Ownership relations for immutable semantic states."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .identity import EntityID


class OwnershipError(ValueError):
    """An ownership relation violates semantic ownership rules."""


def normalize_ownership(
    ownership: Mapping[
        EntityID,
        Iterable[EntityID],
    ],
) -> dict[EntityID, tuple[EntityID, ...]]:
    """Validate and canonicalize an ownership relation."""

    normalized = {
        owner: tuple(sorted(set(children)))
        for owner, children in ownership.items()
    }

    parents: dict[EntityID, EntityID] = {}

    for owner, children in normalized.items():
        if owner in children:
            raise OwnershipError(
                f"entity {owner.value} cannot own itself"
            )

        for child in children:
            previous_owner = parents.get(child)

            if previous_owner is not None:
                raise OwnershipError(
                    f"entity {child.value} has multiple owners: "
                    f"{previous_owner.value} and {owner.value}"
                )

            parents[child] = owner

    for start in normalized:
        path: set[EntityID] = set()
        current = start

        while current in normalized:
            if current in path:
                raise OwnershipError(
                    f"ownership cycle detected at {current.value}"
                )

            path.add(current)

            children = normalized[current]

            if not children:
                break

            # A forest can have multiple children. Check each branch.
            for child in children:
                branch = set(path)
                stack = [child]

                while stack:
                    entity = stack.pop()

                    if entity in branch:
                        raise OwnershipError(
                            f"ownership cycle detected at "
                            f"{entity.value}"
                        )

                    branch.add(entity)
                    stack.extend(normalized.get(entity, ()))

            break

    return normalized


def owner_of(
    ownership: Mapping[
        EntityID,
        Iterable[EntityID],
    ],
    entity: EntityID,
) -> EntityID | None:
    """Return the unique owner of an entity, if any."""

    for owner, children in ownership.items():
        if entity in children:
            return owner

    return None


def owned_children(
    ownership: Mapping[
        EntityID,
        Iterable[EntityID],
    ],
    owner: EntityID,
) -> tuple[EntityID, ...]:
    """Return the entities directly owned by an owner."""

    return tuple(
        sorted(
            ownership.get(owner, ())
        )
    )


def owned_subtree(
    ownership: Mapping[
        EntityID,
        Iterable[EntityID],
    ],
    owner: EntityID,
) -> frozenset[EntityID]:
    """Return the complete recursively owned subtree."""

    result: set[EntityID] = set()
    stack = list(ownership.get(owner, ()))

    while stack:
        entity = stack.pop()

        if entity in result:
            continue

        result.add(entity)
        stack.extend(
            ownership.get(entity, ())
        )

    return frozenset(result)
