"""Semantic values and version identity."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .canonical import canonical_serialize, canonicalize
from .identity import EntityID, VersionID


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
    ) -> "Value":
        return Value(entity, content)

    @property
    def version_id(self) -> VersionID:
        """Return the exact semantic version identity of this value."""

        return version_id_for(self)


def version_id_for(value: Value) -> VersionID:
    """Derive exact version identity from entity and semantic content."""

    encoded = (
        b"VERSION"
        + canonical_serialize(value.entity)
        + canonical_serialize(value.content)
    )

    return VersionID(
        sha256(encoded).hexdigest()
    )
