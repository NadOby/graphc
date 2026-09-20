# Constraint Model

This document describes the current architectural model for constraints in
SEMIROH.

The constraint system is not yet fully implemented. This document records the
current design rather than claiming a completed implementation.

## 1. Constraints as semantic values

A constraint is a semantic value representing a predicate over semantic
values.

Conceptually:

    Constraint(value) -> result

Types are also semantic values and may participate in constraint-based
reasoning.

## 2. Three-valued evaluation

Constraint evaluation has three semantic outcomes:

    Satisfied
    Violated
    Unknown

`Unknown` is a first-class result.

It does not mean that the constraint is false.

It means that the system has not established satisfaction or violation under
the applicable evaluation conditions.

## 3. Why Unknown exists

Semantic computation may be expensive, incomplete, externally dependent, or
subject to explicit resource limits.

The system must therefore distinguish:

    proven satisfied
    proven violated
    not established

Treating the third case as either success or failure would lose information
about the limits of available knowledge.

## 4. Evaluation budgets

Potentially expensive semantic computation may be subject to explicit budgets.

Possible dimensions include:

- computation steps;
- memory;
- recursion depth;
- graph expansion;
- transformation count;
- optional wall-clock time.

The exact budget mechanism is not yet specified.

Where an applicable budget prevents a constraint result from being established,
the result is `Unknown`.

## 5. Evidence

Constraint evaluation may rely on evidence such as:

- structural facts;
- computed results;
- previously established constraints;
- metaprogram-generated evidence;
- certificates;
- analysis results;
- transformation references.

The exact representation of evidence remains unresolved.

Evidence should be distinguishable from the truth value it supports.

## 6. Constraints and types

Types are semantic values.

A type relationship may therefore be expressed through constraints rather than
requiring every type-system rule to be an unrelated primitive mechanism.

Conceptually:

    value
      |
      v
    constraint
      |
      v
    Satisfied / Violated / Unknown

The final type and constraint language remains under development.

## 7. Constraints and contracts

Contracts may contain requirements and guarantees.

Conceptually:

    Contract
       |
       +--> requires  -> Constraint
       |
       +--> guarantees -> Constraint

Contract checking may therefore reuse the constraint machinery.

The distinction between a requirement and a guarantee is semantic context, not
a requirement for two unrelated predicate systems.

## 8. Constraints and transformations

Transformations may provide information relevant to constraints.

For example, a transformation may establish structural relationships between
entities that a later analysis can use as evidence.

Transformation mappings are not themselves automatically truth values.

The semantic meaning of such evidence must be explicitly defined by the
relevant constraint.

## 9. Resource limits and ordinary computation

Not every semantic computation necessarily produces a three-valued result.

A computation producing an ordinary semantic value may instead use its own
explicit error contract.

The three-valued model is primarily relevant where the semantic question is
whether a proposition has been established.

## 10. Soundness principle

A system must not report `Satisfied` or `Violated` merely because an answer
could theoretically be obtained with unlimited computation.

A result must be supported by the evaluation rules and available evidence.

## 11. Current implementation status

The current Python reference model establishes the broader semantic architecture
but does not yet constitute a complete constraint implementation.

The exact constraint representation, evaluator, evidence model, and resource
budget mechanism remain future work.

## 12. Unresolved areas

Open questions include:

- constraint representation;
- evidence representation;
- constraint composition;
- implication and dependency;
- incremental constraint evaluation;
- constraint caching;
- resource-budget semantics;
- interaction with equality;
- interaction with contracts;
- interaction with effects and capabilities;
- formal soundness rules.

## 13. Design principle

The constraint system represents knowledge explicitly.

In particular:

    Unknown != Violated
    Unknown != Satisfied

The language should preserve this distinction rather than silently converting
lack of knowledge into a definitive semantic result.
