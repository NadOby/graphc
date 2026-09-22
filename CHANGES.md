# Development Changelog

This is a retroactive architectural development log. It records significant
semantic decisions and milestones rather than individual commits.

## 2026-09

### Semantic identity model

- Established the semantic graph as the canonical program representation.
- Defined semantic values as the fundamental meaningful units of the model.
- Separated EntityID, VersionID, StateID, and runtime identity.
- Distinguished identity from semantic equality.
- Made semantic states immutable.
- Defined StateID from exact semantic state content rather than history,
  provenance, or transformation mappings.
- Added canonical serialization as the basis for semantic identity.
- Made references state-relative and version-pinned.
- Added explicit cross-state reference transfer.
- Added explicit entity mappings for identity continuity across transformations.
- Separated transformation mappings and provenance from state identity.
- Distinguished explicit rebinding from identity-preserving reference transfer.

### Semantic transformations

- Established transformations as functions producing new immutable states.
- Allowed explicit identity mappings across transformations.
- Allowed identity continuity to represent renaming and other structural
  transformations without implying semantic equality.
- Established explicit produce-versus-activate semantics as a design direction.

### Immutability

- Made semantic values immutable through canonicalized content.
- Made state value collections immutable.
- Established immutable replacement rather than implicit mutation as the default
  state evolution mechanism.

### Testing and executable model

- Established the Python implementation as the executable semantic reference
  model.
- Added tests for identity, equality, references, state identity,
  transformations, canonical serialization, and immutability.
- Added GitHub Actions validation for the semantic model.

### Ownership

- Began separating ownership from ordinary semantic references.
- Ownership is treated as a semantic state relation.
- Ownership is directional and forms a forest.
- An entity may have at most one owner.
- Ordinary references may form arbitrary cycles independently of ownership.
- Destruction is defined as an immutable state transformation recursively
  removing an owned subtree.

## Future

Architectural decisions will be added here when they become sufficiently
stable to form part of the SEMIROH semantic model.

## 2026-09-20

### Session: Repository refactor

- Refactored the executable test suite from a monolithic test module into
  thematic `unittest` modules under `tests/`.
- Separated tests by semantic concern: identity, canonicalization, references,
  state, ownership, lifecycle, transformations, and continuity.
- Switched the test suite to standard `unittest` discovery.
- Updated GitHub Actions validation to discover tests from the `tests/` package.
- Removed the obsolete root-level test module after its tests were migrated.
- Removed the obsolete `identity_model.py` compatibility facade now that the
  package implementation is the direct semantic reference model.
- Preserved the existing semantic behavior while restructuring the executable
  test architecture.
- Established the development changelog as append-only for subsequent entries.

### Transformation model specification

- Defined transformations as explicit transitions between immutable semantic
  states.
- Defined explicit entity continuity as a zero/one/many relation supporting
  disappearance, creation, split, merge, and many-to-many mappings.
- Distinguished an absent mapping from an explicit mapping to zero
  destinations.
- Defined state-local, one-step reference transfer with validation of
  `StateID`, entity existence, and exact `VersionID`.
- Defined explicit distinction between continuity-preserving reference
  transfer and destination-state rebinding.
- Established that transformation mappings and provenance do not contribute to
  `StateID`.
- Established canonical ordering and validation requirements for transition
  mappings.
- Separated ownership transformation semantics from entity continuity.
- Documented composition and reversibility as distinct concerns rather than
  implicit properties of individual transformations.
- Added `docs/transformation_model.md` as the authoritative specification for
  the current transformation model.
- Marked unresolved transformation semantics explicitly rather than
  prematurely defining them through implementation or tests.

### 2026-09-20 – Transformation composition specification tests

Added `tests/test_transformation_composition.py`.

These tests intentionally document expected composition behavior
without introducing composition implementation.

Covered scenarios:

- continuity chain
- disappearance
- split
- split-merge normalization
- preservation vs continuity
- identity transformation
- associativity

The file acts as an executable specification anchor for future
composition implementation.
