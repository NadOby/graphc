# Transformation Composition API

## Purpose

This document specifies the public API and result semantics for
transformation composition.

The composition operation derives continuity information across
multiple transformations.

It does not derive provenance history.

---

## Result Categories

Composition can produce three outcomes.

### Known Continuity

Example:

```text
A → B
B → C
```

Result:

```text
A → C
```

### Known Disappearance

Example:

```text
A → B
B → ()
```

Result:

```text
A → ()
```

### Unknown

Example:

```text
A → B
B preserved
```

Result:

```text
Unknown
```

Composition cannot establish continuity.

Composition cannot establish disappearance.

---

## Unknown Is Not Disappearance

Unknown must never be normalized into:

```text
A → ()
```

Unknown means:

```text
insufficient continuity information
```

not:

```text
entity disappeared
```

---

## Unknown Is Not Continuity

Unknown must never be normalized into:

```text
A → A
```

or

```text
A → B
```

No continuity relation may be inferred.

---

## API Shape

Initial implementation should expose:

```python
compose(
    first: TransformationDefinition,
    second: TransformationDefinition,
) -> CompositionResult
```

---

## CompositionResult

CompositionResult contains:

- composed mappings
- unknown sources

Conceptually:

```python
class CompositionResult:
    mappings: tuple[TransformationMapping, ...]
    unknown_sources: frozenset[EntityID]
```

---

## Examples

### Explicit chain

```text
A → B
B → C
```

Result:

```text
mappings:
    A → C

unknown:
    {}
```

### Explicit disappearance

```text
A → B
B → ()
```

Result:

```text
mappings:
    A → ()

unknown:
    {}
```

### Unknown continuity

```text
A → B
B preserved
```

Result:

```text
mappings:
    {}

unknown:
    {A}
```

### Split

```text
A → (B,C)
B → D
C → E
```

Result:

```text
A → (D,E)
```

### Split merge

```text
A → (B,C)
B → D
C → D
```

Result:

```text
A → (D)
```

---

## Invariants

1. Composition never invents continuity.

2. Composition never invents disappearance.

3. Unknown is preserved.

4. Unknown is distinct from disappearance.

5. Unknown is distinct from continuity.

6. Duplicate destinations collapse under set semantics.

7. Composition remains associative for known mappings.
