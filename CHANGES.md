# Development Changelog

## 2026-09

### Semantic identity model
- Established the semantic graph as the canonical program representation.
- Separated EntityID, VersionID, StateID, and runtime identity.
- Made semantic states immutable.
- Defined StateID as a function of semantic state content rather than history or provenance.
- Made references state-relative and version-pinned.
- Added explicit cross-state reference transfer through entity mappings.
- Separated transformation mappings and provenance from semantic state content.
- Established semantic equality as distinct from identity.
- Added canonical serialization as the basis for semantic identity.

### State transformations
- Added immutable transformation results.
- Supported explicit entity continuity across transformations.
- Distinguished identity continuity from semantic equality.
- Added explicit rebinding for cases where conceptual identity is not preserved.

### Development infrastructure
- Established the Python executable reference model.
- Added regression and invariant tests.
- Added GitHub Actions validation for the semantic model.
