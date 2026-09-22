# Transformation Composition API

## Purpose

This document specifies the public API and result semantics for transformation
composition.

The current composition operation derives explicit continuity information
across multiple transformations.

It does not currently compose complete semantic state changes.

It does not derive provenance history.

---

## Composition relation

The composition operation accepts either a transformation definition or a
previous composition result:

```python
TransformationRelation = TransformationDefinition | CompositionResult
```

The public operation is:

```python
compose(
    first: TransformationRelation,
    second: TransformationRelation,
) -> CompositionResult
```

A `TransformationDefinition` contributes its explicit continuity mappings.

A `CompositionResult` contributes:

- previously established continuity mappings;
- previously established unknown sources.

This permits conservative composition across more than two transformations.

---

## Result categories

Composition can establish three semantic outcomes for a source entity.

### Known continuity

Example:

```text
A → B
B → C
```

Result:

```text
A → C
```

The final destination is explicitly established.

### Known disappearance

Example:

```text
A → B
B → ()
```

Result:

```text
A → ()
```

The disappearance is explicitly established.

### Unknown

Example:

```text
A → B
B preserved without explicit mapping
```

Result:

```text
Unknown
```

The available continuity information is insufficient to establish either a
final destination or disappearance.

---

## Unknown is not disappearance

Unknown must never be normalized into:

```text
A → ()
```

Unknown means:

```text
insufficient continuity information
```

It does not mean:

```text
entity disappeared
```

The current API represents these states separately:

```python
A → ()
```

is represented by a `TransformationMapping` whose destination tuple is empty.

Unknown is represented by:

```python
A in result.unknown_sources
```

---

## Unknown is not continuity

Unknown must never be normalized into:

```text
A → A
```

or:

```text
A → B
```

No continuity relation may be inferred from preservation, equal values,
matching entity identifiers, structural similarity, or state adjacency.

---

## CompositionResult

`CompositionResult` is immutable.

Conceptually:

```python
@dataclass(frozen=True)
class CompositionResult:
    mappings: tuple[TransformationMapping, ...]
    unknown_sources: frozenset[EntityID]
```

`mappings` contains only sources for which composition established a
definitive continuity result.

`unknown_sources` contains sources for which composition could not establish a
definitive result.

A source must not appear in both collections.

Mappings are canonically ordered by source `EntityID`.

Destination entities inside each mapping are canonically ordered and unique.

---

## Known mappings

For:

```text
A → B
B → C
```

the result is:

```text
mappings:
    A → C

unknown:
    {}
```

For:

```text
A → B
B → ()
```

the result is:

```text
mappings:
    A → ()

unknown:
    {}
```

---

## Unknown continuity

For:

```text
A → B
```

followed by a transformation containing no explicit mapping for `B`, the
result is:

```text
mappings:
    {}

unknown:
    {A}
```

The absence of an explicit mapping for `B` means that its treatment is not
known from the continuity relation.

It does not establish disappearance.

---

## Split composition

For:

```text
A → (B, C)
B → D
C → E
```

the result is:

```text
A → (D, E)
```

All intermediate destinations must have definitive explicit results.

If any intermediate destination has unknown continuity, the source becomes
unknown.

For:

```text
A → (B, C)
B → D
C has no explicit mapping
```

the result is:

```text
unknown:
    {A}
```

It must not become:

```text
A → D
```

because the `C` branch remains unresolved.

---

## Split followed by disappearance

For:

```text
A → (B, C)
B → D
C → ()
```

the result is:

```text
A → D
```

The `C` branch is explicitly known to disappear, so it does not make the
overall relation unknown.

If every branch disappears:

```text
A → (B, C)
B → ()
C → ()
```

the result is:

```text
A → ()
```

---

## Split followed by merge

For:

```text
A → (B, C)
B → D
C → D
```

the result is:

```text
A → D
```

The same destination reached through multiple intermediate paths occurs only
once.

Destination endpoints therefore have set semantics.

---

## Previous unknown results

A `CompositionResult` may itself be used as the first or second composition
input.

If a source is already unknown:

```text
A → Unknown
```

later composition must not manufacture a definitive destination merely from
the absence of information.

Unknown therefore propagates conservatively.

For example:

```text
T₁:
    A → B

T₂:
    B → Unknown
```

followed by another relation cannot silently convert `A` into continuity or
disappearance.

---

## Composition of definitions and results

The following combinations are valid:

```text
TransformationDefinition + TransformationDefinition
TransformationDefinition + CompositionResult
CompositionResult + TransformationDefinition
CompositionResult + CompositionResult
```

The operation always returns:

```text
CompositionResult
```

A composition result is therefore a continuity-analysis result, not itself a
complete transformation definition.

---

## Creation

A newly created entity has no synthetic predecessor.

Conceptually:

```text
∅ → B
```

Creation alone contributes no source mapping.

However, if an earlier transformation explicitly establishes:

```text
A → B
```

then `B` may participate in subsequent composition normally.

For example:

```text
A → B
B → C
```

produces:

```text
A → C
```

---

## Identity continuity

An explicit identity mapping:

```text
A → A
```

may participate in composition.

For example:

```text
A → A
A → B
```

produces:

```text
A → B
```

Likewise:

```text
A → B
B → B
```

produces:

```text
A → B
```

This does not mean that an ordinary preserved entity is implicitly an identity
mapping.

Only explicit mappings participate in composition.

---

## Associativity

For sequential transformations:

```text
T₁ : S₀ → S₁
T₂ : S₁ → S₂
T₃ : S₂ → S₃
```

continuity composition is intended to satisfy:

```text
compose(compose(T₁, T₂), T₃)
=
compose(T₁, compose(T₂, T₃))
```

with respect to the resulting known mappings and unknown sources.

This associativity applies to the current continuity-composition operation.

It does not establish associativity for full semantic transformation
composition.

---

## Composition and references

Composition is not required for ordinary reference transfer.

Reference transfer remains one-step:

```text
Reference(S₀)
    →
Reference(S₁)
    →
Reference(S₂)
```

A composed continuity result may be used for analysis or other semantic
operations.

It does not allow a reference bound to `S₀` to be directly transferred through
a transformation whose source is `S₁`.

---

## Composition and transformation changes

The current API composes continuity mappings only.

It does not compose `EntityChange` values.

For example:

```text
T₁:
    A → B
    A changes to value X

T₂:
    B → C
    B changes to value Y
```

composition establishes:

```text
A → C
```

but does not establish a composed semantic value change such as:

```text
A → value Y
```

and does not construct a complete destination state.

Full semantic transformation composition remains unspecified.

---

## Composition and ownership

The current composition API does not compose ownership relations.

Ownership remains part of state semantics and is handled by transformation
application.

A composed continuity relation must not be interpreted as a composed
ownership relation.

---

## Composition and contracts

The current composition API does not compose contracts or contract guarantees.

A continuity relation does not automatically establish preservation of an
arbitrary contract or constraint.

Such preservation requires separate semantic rules.

---

## Composition and constraints

The current composition API does not evaluate constraints.

It may produce continuity information that could later be used as evidence by
constraint evaluation.

Continuity itself is not a constraint result.

In particular:

```text
A → B
```

does not automatically establish that every constraint satisfied by `A` is
satisfied by `B`.

---

## Composition and provenance

The current API does not derive a transformation history graph.

Composition results contain continuity information and unknown sources, not a
complete record of the transformations through which that information was
derived.

A future provenance model may attach such information separately.

---

## Canonicalization invariants

The following invariants apply to `CompositionResult`:

1. The result is immutable.

2. Each source entity occurs at most once in `mappings`.

3. Mapping records are canonically ordered by source `EntityID`.

4. Destination entities within a mapping are unique.

5. Destination entities within a mapping are canonically ordered.

6. A source cannot occur in both `mappings` and `unknown_sources`.

7. Duplicate destination endpoints collapse under set semantics.

8. Unknown is represented separately from known disappearance.

---

## Semantic invariants

Composition must satisfy:

1. Composition never invents continuity.

2. Composition never invents disappearance.

3. Preservation is not treated as continuity.

4. Unknown is distinct from disappearance.

5. Unknown is distinct from continuity.

6. Explicit disappearance remains disappearance.

7. Explicit continuity may be followed through intermediate entities.

8. An unresolved branch makes the source unresolved.

9. Explicitly disappearing branches do not make other resolved branches
   unknown.

10. Multiple paths to the same destination collapse to one destination.

11. Creation does not acquire a synthetic predecessor.

12. Composition of continuity information does not imply composition of
    semantic state changes.

---

## Current implementation boundary

The current API provides:

- `TransformationRelation`;
- `compose`;
- `CompositionResult`;
- known continuity;
- known disappearance;
- unknown continuity;
- unknown propagation;
- one-to-many composition;
- many-to-one composition;
- many-to-many composition;
- canonical destination set semantics.

It does not provide:

- complete semantic transformation composition;
- composition of `EntityChange` values;
- composition of destination states;
- ownership composition;
- effect composition;
- contract composition;
- constraint evaluation;
- provenance composition;
- transformation identity or equality.

These mechanisms require separate semantic definitions before becoming part of
the public API.

---

## Design principle

The composition API deliberately answers a narrow question:

```text
What explicit continuity relationship can be established across these
transformation mappings?
```

It does not yet answer:

```text
What complete semantic transformation results from applying these
transformations sequentially?
```

The first is implemented by the current API.

The second remains a future semantic design problem.
