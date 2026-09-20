# Transformation Model

This document defines the current semantic contract for transformations in
SEMIROH.

It is normative where stated. Implementation details that are not part of the
semantic contract must not be inferred from the Python reference
implementation.

## 1. Transformation definitions

A transformation definition is an immutable semantic value describing a
potential state transition.

A definition is independent of a particular source `StateID`.

Conceptually:

    TransformationDefinition
        =
        semantic changes
        +
        explicit continuity mappings

A definition may therefore be reused against multiple compatible source
states.

Application is a separate operation:

    TransformationDefinition
        +
    SourceState
        →
    TransformationResult

The definition describes what the transformation means.

The result describes what happened when that definition was applied to one
particular source state.

The current definition does not yet include contracts, constraints, effects,
capabilities, or provenance as semantic components. Those are separate
models whose interaction with transformations remains to be specified.

## 2. State transitions

A transformation takes one immutable semantic state and produces another
immutable semantic state.

Conceptually:

    S₀ → S₁

The source state remains unchanged. The destination is a distinct immutable
state.

A transformation result consists conceptually of:

    source state
    destination state
    explicit entity continuity mapping
    optional provenance

Continuity mapping and provenance are properties of the transition. They are
not properties of either state.

## 3. Transformation changes

A transformation definition may contain immutable entity changes.

Each change identifies:

    EntityID
    semantic Value

The changed value must belong to the entity identified by the change.

Changes are canonically ordered by `EntityID`.

A definition cannot contain multiple changes for the same entity.

Applying a change replaces the value associated with that entity in the
destination state.

A change does not by itself establish identity continuity.

For example:

    Entity E : value A
        →
    Entity E : value B

changes the semantic value while retaining the entity in the destination.

Whether `E` is considered continuous across the transition is determined by
the explicit continuity mapping.

## 4. Transformation mappings

A transformation definition may contain explicit continuity mappings.

A definition-level mapping is state-independent:

    source entity → destination entities

The concrete mapping produced by applying the definition is associated with
the actual source `StateID`.

Each source entity may occur at most once in the definition's mapping relation.

Destination entities are canonically ordered.

The mapping cardinality determines the continuity relationship:

    0 destinations   disappearance
    1 destination    unambiguous continuity
    >1 destinations  split / ambiguous continuity

Multiple source entities may map to the same destination entity.

Therefore the relation supports:

    one → zero
    one → one
    one → many
    many → one
    many → many

The mapping is a relation, not an assertion of semantic equality.

## 5. Applying a transformation definition

Applying a definition validates its mapping against the source and produced
destination state.

Every mapping source must identify an entity present in the source state.

Every non-empty mapping destination must identify an entity present in the
destination state.

Destination entities may be introduced by the definition's changes.

A source mapped to an empty destination tuple disappears from the destination
state.

A destination entity with no incoming mapping is a newly created destination
entity.

Creation therefore has no synthetic source entity:

    ∅ → new entity

Creation is not identity transfer from an implicit predecessor.

A transformation result contains the concrete source-state mapping produced
from the reusable definition.

## 6. Plain transformations

A transformation without an explicit continuity mapping changes semantic state
content without asserting which entities are continuous across the transition.

`transform(state, changes)` therefore establishes only:

    state content before
    →
    state content after

It does not establish identity continuity.

A caller must not infer continuity merely because the same `EntityID` appears
in both states.

## 7. References

A `Reference` is bound to:

    StateID
    EntityID
    VersionID

A reference therefore identifies a particular version of an entity in a
particular state.

A reference is valid only when all three components agree with the state.

Reference resolution against a state requires:

1. the reference's `StateID` to equal the state's `StateID`;
2. the referenced entity to exist in that state; and
3. the reference's `VersionID` to equal the current version of that entity.

## 8. Reference transfer

Reference transfer is strictly state-local and one-step.

A reference may be transferred only through a transformation whose source
state is exactly the state named by the reference.

The transfer operation therefore has the form:

    Reference(S₀, E, V)
        +
    Transformation(S₀ → S₁)
        →
    Reference(S₁, E', V')

The reference must first be valid against the transformation's source state.

The preconditions are:

1. `reference.state == transformation.source.id`;
2. the referenced entity exists in the transformation's source state; and
3. the reference's version equals the current version of that source entity.

Violations have distinct meanings:

    wrong StateID
        → CrossStateReference

    absent source EntityID
        → missing source entity error

    wrong VersionID
        → StaleReference

After these checks, the explicit transformation mapping determines whether the
reference can be transferred.

A source mapped to zero destinations cannot produce a destination reference.

A source mapped to exactly one destination produces a reference to that
destination entity.

A source mapped to multiple destinations cannot be transferred without an
explicit choice and therefore produces `AmbiguousEntityMapping`.

The resulting reference is bound to the destination state and the current
version of the mapped destination entity.

## 9. Transformation composition

Transformations are not implicitly composable for reference transfer.

Given:

    S₀ → S₁
    S₁ → S₂

a reference in `S₀` must be transferred through the first transformation before
it can be transferred through the second:

    Reference(S₀)
        →
    Reference(S₁)
        →
    Reference(S₂)

The second transformation cannot directly consume the `S₀` reference.

This prevents a transformation mapping from becoming an implicit global
provenance/history graph.

Composition of transformations may be introduced as a separate semantic
operation, but it is not implied merely by having transformations whose states
form a chain.

## 10. Rebinding

Rebinding is distinct from reference transfer.

Reference transfer preserves an explicitly asserted continuity relation.

Rebinding explicitly chooses an entity in a destination state without claiming
that the chosen entity is the continuation of the original reference.

Conceptually:

    transfer
        = follow declared continuity

    rebind
        = explicitly choose a new state-local target

Rebinding therefore does not preserve conceptual identity.

## 11. Ownership

Ownership is part of semantic state content.

Transformation mappings do not implicitly modify ownership.

When no destination ownership relation is explicitly supplied, the
transformation preserves the existing ownership relation subject to removal
of entities that disappear.

An entity disappearing from the destination removes ownership edges involving
that entity.

This does not imply recursive deletion of its owned descendants.

Recursive subtree destruction is a separate state operation.

When explicit destination ownership is supplied, it defines the destination
ownership relation directly and must refer only to destination entities.

Ownership and ordinary entity continuity are therefore separate relations.

## 12. State identity

State identity is derived from semantic state content.

Transformation mappings do not contribute to `StateID`.

Transformation provenance does not contribute to `StateID`.

Therefore two transformations may produce semantically identical destination
states while carrying different mappings or provenance, without producing
different state identities for that reason.

Conversely, changing semantic state content or ownership changes the state
identity when the resulting semantic content differs.

## 13. Canonicalization and determinism

The representation of transformation mappings is canonical.

For a mapping:

    source → (destination₁, destination₂, ...)

destination entities are stored in canonical `EntityID` order.

Mapping records are likewise stored in canonical source-entity order.

Equivalent mappings expressed in different input orders therefore produce the
same canonical mapping representation.

This ordering is semantic determinism, not an assertion that the ordering
itself represents an additional relationship between entities.

## 14. Mapping validation

A valid transformation mapping must satisfy:

- every mapping belongs to the transformation's source state;
- every mapping source exists in the source state;
- each source entity occurs at most once in the mapping relation;
- destination entities are unique within each mapping;
- mapped destination entities exist in the destination state;
- destination entity lists are canonically ordered;
- mapping records are canonically ordered.

Invalid transition mappings must be rejected rather than silently normalized
into a different semantic relation, except where canonical ordering is an
explicitly supported normalization.

## 15. Provenance

Provenance is metadata associated with a transformation.

It is not semantic state content and does not affect `StateID`.

The current model does not require provenance to form a globally traversable
history graph.

A future provenance model may define richer historical relationships, but such
relationships must not be inferred from ordinary entity mappings.

## 16. Reversibility

A transformation mapping describes forward continuity.

A forward mapping does not imply that the transformation is reversible.

In particular:

    one → many
    many → one
    one → zero

may lose information required to uniquely reconstruct the source.

A transformation may be lossless, lossy, or otherwise constrained by additional
semantics that have yet to be specified.

Exact state restoration, including restoration of a historical `StateID`, is
not implied merely by applying an apparent inverse transformation.

A future reversible-transformation model must specify its own requirements for
invertibility and information preservation.

## 17. Semantic versus implementation concerns

The following are semantic requirements:

- immutable source and destination states;
- explicit continuity mappings;
- zero/one/many mapping cardinality;
- explicit creation and disappearance;
- state-local, version-aware reference transfer;
- distinction between transfer and rebinding;
- separation of ownership from continuity;
- state identity independence from mappings and provenance;
- deterministic canonical mapping representation.

The following are implementation choices unless separately specified:

- Python class structure;
- exception inheritance hierarchy beyond the semantic distinctions required
  above;
- internal container types;
- serialization implementation;
- hashing implementation;
- helper-function decomposition.

Tests must target the semantic contract rather than incidental implementation
details.

## 18. Current unresolved areas

The following are intentionally not fully specified yet:

- the complete semantics of unspecified source entities in a transformation;
- whether a transformation is itself a first-class semantic value;
- transformation identity and equality;
- formal composition of transformations and composed continuity mappings;
- formal distinction between lossless and lossy transformations;
- transformation deltas and distance measures;
- richer provenance/history semantics;
- interaction with the eventual generalized graph/hypergraph model;
- whether transformation definitions should have their own persistent semantic
  representation.

These questions must be resolved before they are treated as stable semantics.

## 19. Design principle

A transformation is an explicit semantic transition between immutable states.

An entity's continuity across that transition exists only where the transition
explicitly declares it.

A reference follows one such declaration at a time.

Neither `EntityID` reuse, structural similarity, state adjacency, nor historical
provenance is sufficient to manufacture continuity that the transformation
did not declare.
