# Transformation Composition

## Purpose

Transformation composition defines how multiple transformations combine into a single semantic transformation.

Given:

```text
State A
   │
   │ T₁
   ▼
State B
   │
   │ T₂
   ▼
State C
```

composition produces:

```text
T₃ = T₁ ∘ T₂
```

such that applying `T₃` to State A produces the same semantic result as applying `T₁` followed by `T₂`.

Composition concerns only semantic continuity mappings.

Composition does not preserve intermediate history, execution details, or provenance paths.

Those belong to provenance and lineage systems.

## Explicit Continuity Requirement

Composition operates only on explicit continuity mappings.

Preservation is not continuity.

Example:

```text
T₁:
A → B

T₂:
B preserved
```

Result:

```text
No composed continuity mapping exists.
```

Likewise:

```text
T₁:
A preserved

T₂:
A → B
```

Result:

```text
No composed continuity mapping exists.
```

Composition never invents continuity.

## Relation Semantics

Mappings are interpreted as a relation:

```text
source_entity → destination_entity
```

A split:

```text
A → (B, C)
```

is interpreted as:

```text
(A,B)
(A,C)
```

Composition uses ordinary relation composition.

Example:

```text
A → B
B → C
```

becomes:

```text
A → C
```

## Set Semantics

Destination entities are treated as a set.

Duplicate destinations are removed.

Example:

```text
A → (B, C)

B → D
C → D
```

Raw composition:

```text
A → (D, D)
```

Normalized result:

```text
A → (D)
```

The existence of multiple paths is not preserved.

Path history belongs to provenance, not continuity mappings.

## Disappearance

Disappearance composes.

Example:

```text
A → ()
```

Result:

```text
A → ()
```

Further composition cannot restore continuity.

Example:

```text
A → ()
```

followed by any transformation:

```text
A → ()
```

## Split

Example:

```text
A → (B, C)

B → D
C → E
```

Result:

```text
A → (D, E)
```

## Merge

Example:

```text
A → B
C → B
```

Multiple source entities may compose to the same destination entity.

The resulting relation remains:

```text
A → B
C → B
```

## Split-Merge

Example:

```text
A → (B, C)

B → D
C → D
```

Result:

```text
A → D
```

Duplicate destinations are removed by normalization.

## Creation

Creation does not require a source mapping.

Example:

```text
T₁:
create B
```

No continuity mapping exists.

Creation participates in composition only after explicit continuity has been established.

Example:

```text
T₁:
A → B
(B created)

T₂:
B → C
```

Result:

```text
A → C
```

## Preservation vs Continuity

Preservation means an entity remains present in a state.

Continuity means a transformation explicitly establishes semantic identity.

Example:

```text
A preserved
```

does not imply:

```text
A → A
```

Explicit continuity must be declared.

Example:

```text
A → A
```

represents explicit continuity.

## Reference Transfer

Reference transfer follows explicit continuity only.

Composition does not convert preservation into transferability.

If no explicit continuity chain exists across all composed transformations:

```text
reference transfer is impossible
```

## Identity Transformation

An identity transformation is defined as:

```text
A → A
```

for every participating entity.

Identity transformation acts as the neutral element of composition.

Example:

```text
Identity ∘ T = T
T ∘ Identity = T
```

## Associativity

Composition is associative.

Example:

```text
(T₁ ∘ T₂) ∘ T₃
=
T₁ ∘ (T₂ ∘ T₃)
```

This property follows from relation composition and destination normalization.

## Invariants

Composition must satisfy:

1. Composition never invents continuity.
2. Composition never converts preservation into continuity.
3. Composition preserves disappearance.
4. Duplicate destination entities are removed.
5. Destination entities are canonically ordered.
6. Composition is associative.
7. Identity transformation is the neutral element.
8. Composition operates only on explicit continuity mappings.
9. Provenance history is not encoded in continuity mappings.
10. Continuity mappings represent semantic identity, not execution history.
