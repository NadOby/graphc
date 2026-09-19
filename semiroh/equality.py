"""Semantic and identity comparisons."""

from __future__ import annotations

from .values import Value, version_id_for


def semantic_equal(
    left: Value,
    right: Value,
) -> bool:
    """Compare semantic content, independently of entity identity."""

    return left.content == right.content


def same_entity(
    left: Value,
    right: Value,
) -> bool:
    """Compare conceptual entity identity."""

    return left.entity == right.entity


def same_version(
    left: Value,
    right: Value,
) -> bool:
    """Compare exact semantic versions."""

    return version_id_for(left) == version_id_for(right)
