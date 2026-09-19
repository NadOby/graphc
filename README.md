# SEMIROH

**Semantics Exist Mostly in Relations of Hypergraphs**

SEMIROH is a minimalist systems programming language built around a semantic graph as the canonical representation of a program.

It is not "better C".

C is a historical influence, an interoperability target, and an important ABI boundary.

The name is incidentally reminiscent of Simurgh/Simorgh, the mythical Persian bird. This is a cultural association, not part of the technical meaning of the name.

> Graph is the program. Values are immutable. Identity is not equality. States are immutable. Transformations produce states. References are state-relative. Continuity is explicit. Runtime and semantic computation use the same function model. Capabilities describe authority. Effects describe behaviour. Constraints establish what is known. Contracts describe values. Source and machine code are representations. Tooling operates on semantics.

## 1. Canonical program representation

The semantic graph is the canonical representation of a program.

Source code, intermediate representations, machine code, documentation, debug information, and other artifacts are representations or derived products of the semantic program.

Conceptually:

    semantic program
          |
          +--> source representation
          |
          +--> semantic IR
          |
          +--> machine representation
          |
          +--> documentation
          |
          +--> debug information

A program image may contain:

- the semantic graph;
- semantic states;
- transformations and metaprograms;
- dependency information;
- optional source information;
- optional transformation history;
- cached intermediate or native representations.

Removing source text or transformation history must not change the semantic program.

History and provenance may be retained for tooling, debugging, reproducibility, and analysis, but they are not inherently part of semantic identity.

## 2. Semantic graph

SEMIROH uses a generalized hypergraph as its fundamental semantic structure.

There is no fundamental distinction between nodes and edges.

A semantic value may participate in zero or more relations.

A value with zero participating relations can therefore exist as an atomic or leaf value.

Conceptually:

    value
      |
      +--> relation
      |
      +--> relation
      |
      +--> relation

Relations may represent:

- containment;
- application;
- typing;
- dependency;
- reference;
- description;
- transformation;
- provenance;
- authority;
- constraints.

Every semantically meaningful entity has semantic identity.

The graph represents both values and relationships between values.

The graph does not necessarily expose the complete internal structure of every value.

Large, opaque, compressed, external, or computationally expensive values may remain represented without graph-expanding their internals.

Expansion is an explicit transformation.

## 3. Semantic values

Everything semantically meaningful is represented as a value.

This includes:

- ordinary data;
- types;
- functions;
- constraints;
- effects;
- capabilities;
- contracts;
- transformations;
- modules;
- semantic states;
- representations;
- resources;
- metadata.

There is no separate fundamental metaprogramming language or meta-object system.

Metaprogramming operates on the same semantic value model as ordinary programming.

A function can therefore receive a type, graph fragment, contract, program state, or transformation as an ordinary semantic value.

The distinction between "program data" and "program structure" is primarily determined by how a value is used, not by requiring unrelated semantic systems.

## 4. Identity

SEMIROH distinguishes several kinds of identity.

### Entity identity

Entity identity represents conceptual continuity.

It answers:

> Is this the same conceptual entity across semantic states?

### Semantic state identity

State identity represents the exact immutable semantic state.

It answers:

> Is this semantic state identical to that other semantic state?

State identity is independent of the history through which the state was produced.

### Runtime identity

Runtime identity identifies a runtime instance, allocation, handle, or resource incarnation.

It answers:

> Is this the same runtime object or resource?

These identities must not be conflated.

In particular:

    Entity identity != semantic equality
    State identity != provenance
    Runtime identity != semantic identity

Entity identity represents continuity, not equivalence.

Two values can be semantically equal without being the same entity.

Two versions of an entity can preserve entity identity while having different semantic values.

A runtime object can correspond to a semantic value without becoming identical to that semantic value.

## 5. Immutable states

Semantic states are immutable.

A transformation produces a new state rather than mutating the existing one.

Conceptually:

    old_state
        |
        | transform
        v
    new_state

The old state remains valid.

Producing a new state and activating that state are separate operations.

Conceptually:

    old_state
        |
        | transform
        v
    new_state
        |
        | activate
        v
    active state

Activation changes which state is selected for subsequent execution or observation.

It does not retroactively modify the previous state.

Immutable semantic states support:

- persistence;
- rollback;
- branching;
- speculation;
- structural sharing;
- provenance;
- reproducible builds;
- caching;
- alternative program versions.

References are state-relative.

A reference belonging to one state cannot silently become a reference into another state.

Cross-state transfer is explicit.

Provenance and entity mappings belong to transformation or transition records rather than being part of the semantic identity of the resulting state.

## 6. Transformations

Transformations are central to SEMIROH.

Every transformation is a function or composition of functions operating on semantic values and producing semantic values or new semantic states.

A compiler pipeline can therefore be expressed conceptually as:

    semantic graph
          |
          v
    semantic transformations
          |
          v
    lower representation
          |
          v
    LLVM / other IR
          |
          v
    target transformations
          |
          v
    machine representation

Transformations can establish relationships such as:

    1 -> 1       preserve or replace
    1 -> many    split
    many -> 1    merge
    1 -> none    discard

A one-to-one transformation may preserve entity identity while replacing its semantic value.

A transformation can preserve semantic meaning without preserving representation.

Identity continuity is therefore distinct from semantic equivalence.

A lossless transformation should provide enough information to establish equivalence through a reverse transformation or other explicit validation mechanism.

A lossy transformation must specify the permitted differences or semantic delta.

## 7. Functions and computation

Functions are ordinary semantic values.

The same function model is intended to cover:

- runtime computation;
- compile-time computation;
- graph inspection;
- metaprogramming;
- semantic transformations;
- analysis.

There is no fundamental "meta-function" category.

The context in which a function is invoked determines what it is permitted to observe or modify.

Semantic computation operates over semantic state.

Runtime computation operates over runtime state and resources.

Transitions between these domains are explicit.

An immutable semantic value may be captured by runtime computation.

Semantic mutable execution state must not leak into another semantic domain implicitly.

A runtime-to-semantic operation produces a new semantic value or performs an explicit semantic transformation.

## 8. Explicitness

SEMIROH does not require every operation to be syntactically explicit.

The design principle is:

> Implicit behaviour is acceptable where it provides substantial practical value and has clear, predictable semantics.

Explicitness is particularly important for:

- semantic-state transitions;
- mutation;
- effects;
- evaluation;
- conversions;
- expensive operations;
- dangerous operations;
- semantic-state activation;
- cross-state references.

The purpose is not to maximize syntax.

The purpose is to prevent hidden semantic transitions from becoming difficult to reason about.

## 9. Types and constraints

Types are semantic values.

For example:

    Int : Type
    Bool : Type
    42 : Int

The type system is primarily constraint-based.

A constraint is a predicate over semantic values.

Constraints are normally evaluated at compile time when their inputs are available there.

Constraint evaluation produces three possible results:

    Satisfied
    Violated
    Unknown

`Unknown` is a first-class result.

A constraint is not required to return `Satisfied` merely because the implementation could theoretically compute the answer given unlimited resources.

Semantic computation may have explicit budgets such as:

- computation steps;
- memory;
- recursion depth;
- graph expansion;
- transformation count;
- optional wall-clock time.

Exceeding an applicable budget produces `Unknown`.

Evidence for a constraint result may include:

- structural facts;
- computed results;
- previously established constraints;
- metaprogram-generated evidence;
- certificates;
- analysis results;
- transformation references.

The exact evidence representation remains open.

## 10. Equality

Ordinary equality means semantic equality.

It does not mean identity.

Equality is potentially progressive or lazy.

The possible results are:

    Equal
    NotEqual
    Unknown

A comparison may proceed through:

1. atomic values;
2. type and shape;
3. structure;
4. explicitly permitted evaluation;
5. evaluated results.

Expensive, stateful, or potentially nonterminating evaluation must not be performed implicitly merely to establish equality.

Identity may be used as an implementation or tooling shortcut where it is already semantically valid, but identity is not the definition of equality.

For example:

    x = y

tests semantic equality.

An explicit mutation operation is separate:

    x <- value

Equality therefore cannot silently become assignment.

## 11. Mutation

Values are immutable by default.

Bindings are immutable.

For example:

    name := value

creates an immutable binding.

There is no implicit rebinding of an existing name.

Mutable state is explicitly represented and accessed.

For a mutable reference:

    reference <- value

performs an explicit write.

The language distinguishes between:

- creating a new immutable value;
- creating a new semantic state;
- modifying explicitly mutable runtime state;
- activating a different semantic state.

These operations are not interchangeable.

Operator syntax is ordinary function syntax where appropriate:

    a + b

is equivalent in meaning to:

    add(a, b)

Operators do not constitute a separate semantic mechanism.

Mutation syntax may be concise, but the underlying mutation operation remains explicit and semantically defined.

## 12. Effects

An effect describes observable behaviour or dependency.

A capability describes authority.

These are separate concepts.

A capability may exist without being used.

An effect describes what an operation does or depends on, while a capability describes what the operation is authorized to do.

The initial core effect set is intentionally small:

- no effects;
- `Mutation`;
- `ProgramModify`.

Other effects such as I/O, time, randomness, concurrency, foreign calls, logging, and device access may be provided by libraries or added to the core where justified.

Effects compose.

Internal effects may be consumed, transformed, or hidden by higher-level abstractions where the resulting behaviour is explicitly defined.

Allocation and destruction are currently treated as object-lifecycle operations rather than core effects.

Program modification requires particular care.

A program transformation produces a new immutable semantic state.

Activation of that state is a separate operation.

## 13. Capabilities

A capability is a semantic value representing authority or access.

Capabilities may be:

- passed;
- restricted;
- transferred;
- stored;
- derived;
- consumed by operations.

Capabilities describe authority at the semantic level.

The actual runtime resource may be separate from the semantic capability:

    semantic capability
          |
          v
    runtime resource
          |
          v
    OS / hardware resource

A semantic graph can therefore describe authority without containing the physical resource itself.

Capability hierarchy and revocation are not yet fully specified.

Capability types may require generative identity or nominal branding where structural typing would otherwise allow an authority value to be forged.

## 14. Contracts

Contracts are independent semantic values.

A contract can describe a value:

    Contract -> describes -> Value

A contract can also contain requirements and guarantees:

    Contract -> requires -> Constraint
    Contract -> guarantees -> Constraint

Requirements and guarantees are ordinary constraints distinguished by their relationship to the contract.

Contracts may describe:

- callable values;
- modules;
- transformations;
- types;
- data;
- resources;
- representations.

A value may have multiple contracts.

A contract may describe multiple values.

A contract is not intrinsically a type identity or an equality relation.

Contract checking may be static or runtime, but the checking operation is explicit.

Static checking produces the same three-valued result used by constraints:

    Satisfied
    Violated
    Unknown

Executable contract validation should reuse the constraint and metaprogramming machinery rather than introduce a separate validation subsystem.

## 15. Ownership and references

SEMIROH does not use garbage collection as its fundamental lifetime model.

Ownership forms a tree.

References may form an arbitrary graph.

Each owned object has one owner.

Destroying an owner destroys its ownership subtree.

A reference cycle therefore does not keep an object alive.

Ownership transfer preserves semantic object identity.

The basic distinction is:

    ownership = lifetime authority
    reference = access relationship

A safe semantic reference may be represented as:

    Ref<T>

A raw or unsafe pointer may be represented as:

    Ptr<T>

The exact pointer/reference rules, borrowing model, alias analysis, and lifetime analysis remain areas requiring further specification.

## 16. Ownership transfer and movement

Ownership transfer and physical movement are distinct operations.

Reparenting an object may change its owner without moving its storage.

Moving an object may relocate its representation and therefore require stronger exclusivity guarantees.

The language must eventually distinguish these cases explicitly.

For example, conceptually:

    reparent(object, new_owner)

changes ownership.

A separate move operation may change physical representation:

    move(object)

The exact semantics of moves, references into moved objects, pinning, and exclusive access remain unresolved.

Borrowing and alias analysis must integrate with the immutable semantic-state model and explicit mutation model rather than becoming an unrelated type-system subsystem.

## 17. Collections and representations

SEMIROH aims for a small primitive semantic core.

Higher-level abstractions should normally be derived from general primitives when doing so remains simple and natural.

An abstraction should become primitive when deriving it would introduce substantial complexity, awkwardness, performance problems, or semantic ambiguity.

`Array` is a likely primitive boundary because ordered contiguous storage has important representation, layout, and allocation semantics:

    Array<T>

Other structures can generally be built above it:

- sequences;
- maps;
- sets;
- iterators;
- slices;
- tuples;
- records;
- enums;
- options;
- results;
- strings.

Their physical representation is target-dependent unless explicitly constrained by a contract or ABI.

## 18. Numeric types

The initial numeric family is expected to include:

    u8   i8
    u16  i16
    u32  i32
    u64  i64
    f32  f64

Additional types such as `u128` and `i128` may be provided where justified.

Numeric literals are context-resolved.

Conversions that may lose information or violate constraints are explicit.

A safe implicit conversion should be justified by a value-preservation rule that holds for every permitted input, rather than merely being common in conventional languages.

## 19. Byte and string representations

Byte-oriented data is distinct from text.

A provisional model is:

    Byte
    ByteString
    UTF8String

UTF-8 strings are values representing valid UTF-8 text.

Byte strings represent arbitrary byte sequences.

Conversion between them is explicit when validity is not guaranteed.

The exact string model, Unicode semantics, normalization behaviour, and indexing rules remain open.

## 20. Errors and control flow

SEMIROH does not use exceptions as the fundamental error mechanism.

Errors are explicit values.

A result can therefore be represented conceptually as:

    Result<T, E>

where `T` is the successful value and `E` is the error value.

Result types should be derived from ordinary value composition rather than requiring a special exception mechanism.

The semantic model distinguishes:

    Value
    Error
    Unknown

These are not interchangeable.

Explicit abort, panic, and trap operations may exist for unrecoverable conditions.

Control flow still requires explicit semantic definitions for:

- branching;
- loops;
- exhaustive selection;
- returns;
- labeled exits;
- asynchronous suspension.

## 21. Concurrency

The core language should express concurrency without forcing one implementation strategy.

A possible primitive model is:

    Task<T>
    spawn(f)
    await(task)

A `Task<T>` represents an asynchronous computation but does not necessarily imply a thread.

Possible implementations include:

- operating-system threads;
- processes;
- asynchronous I/O;
- event loops;
- work stealing;
- GPU execution;
- other runtime scheduling strategies.

Locks, channels, actors, schedulers, and similar mechanisms may be libraries or runtime facilities.

The safety of spawning depends on ownership, lifetime, and alias analysis.

Task lifetime and dropping semantics therefore require explicit definition.

The simplest initial `await` semantics may block the current execution context.

Suspension and resumable execution can later be implemented through explicit transformations or runtime machinery rather than requiring a special semantic category of resumable functions.

## 22. Modules and semantic values

Modules are semantic values.

A module is not a copied namespace that is merged into another module.

Changing a module produces a new immutable module value or semantic state.

Dependents do not silently change as a consequence.

Version selection and activation must therefore be explicit enough to prevent an entry point from accidentally combining incompatible module versions.

Explicit aliases may select different versions where required.

A module can contain or expose:

- values;
- functions;
- types;
- contracts;
- transformations;
- capabilities;
- other semantic entities.

## 23. Entry points

Entry points are ordinary semantic values with execution significance.

A program may contain multiple entry points.

Possible entry-point forms include:

- executable programs;
- event loops;
- library entry points;
- services;
- tools;
- other explicitly invocable program roots.

`main` is therefore a common convention rather than necessarily a unique semantic primitive.

Entry-point resolution should eventually produce explicit references to the selected semantic entities so that the resulting program state is internally coherent and reproducible.

## 24. Names and name resolution

Names are immutable semantic bindings.

A binding associates a name with a semantic value or semantic entity without implying a particular physical allocation.

Namespaces are not required as a fundamental semantic primitive.

Name visibility is represented through graph relations and scope structure.

Resolution begins at the relevant lexical or semantic scope and proceeds outward.

At each scope level, all applicable candidates at that level are considered before searching farther outward.

A successful nearer match therefore shadows farther matches.

If multiple applicable candidates remain at the same resolution level and the language cannot establish a unique result, resolution is ambiguous rather than arbitrarily selecting one.

Conceptually:

    local scope
        |
        v
    enclosing scope
        |
        v
    module scope
        |
        v
    external scope

The exact scope graph and visibility rules remain subject to refinement.

The immutable binding operation is:

    name := value

This creates or establishes a binding.

It does not mean that the value has been physically allocated at that point.

The mutation operator:

    reference <- value

is distinct from binding a name.

Module roots are expected to establish a definition scope.

Entry points are ordinary semantic values resolved from that scope rather than a separate namespace mechanism.

For reproducibility, construction or activation of an executable program should resolve the selected names into explicit semantic references rather than depending on future ambient name lookup.

## 25. Foreign integration

Foreign integration is treated as semantic derivation rather than requiring SEMIROH to parse every foreign language.

Conceptually:

    foreign artifact
          |
          v
    derivation / import
          |
          v
    SEMIROH semantic values

A foreign integration tool may derive:

- declarations;
- types;
- calling conventions;
- ABI information;
- effects;
- capabilities;
- contracts;
- ownership information;
- representation constraints.

The derivation must carry provenance and, where relevant, evidence for claims made about the foreign artifact.

A foreign declaration by itself does not establish properties that are not encoded or derivable from the foreign interface.

For example, an imported function declaration does not automatically prove:

- ownership behaviour;
- nullability;
- thread safety;
- absence of mutation;
- absence of global state;
- absence of I/O;
- preconditions;
- lifetime guarantees.

Such properties must come from explicit contracts, annotations, external specifications, analysis, or trusted derivation rules.

C ABI interoperability is therefore primarily a semantic integration problem.

A foreign callable should be represented as a SEMIROH value with an explicit contract describing the ABI and relevant semantic assumptions.

Foreign exports may similarly require an explicit link model.

A possible conceptual form is:

    exports(symbol, callable, abi)

An exported callable may need restrictions such as:

- monomorphic ABI;
- stable representation;
- no captured semantic state that cannot cross the ABI;
- explicit ownership transfer;
- explicit error representation;
- defined visibility;
- symbol/version handling.

The exact export mechanism remains open.

## 26. Opaque and external values

Not every semantic value needs to be expanded into the semantic graph.

SEMIROH distinguishes at least three useful cases:

    inline semantic value
    opaque represented value
    external resource

An opaque value is semantically meaningful but its internal representation is intentionally not expanded.

Examples include:

- compressed data;
- memory-mapped data;
- GPU buffers;
- database-backed objects;
- large binary objects;
- external indexes;
- compiled foreign libraries.

The representation may itself be a semantic value without exposing all of its internal structure.

Conceptually:

    semantic value
          |
          v
    representation
          |
          v
    runtime resource
          |
          v
    physical object

Not every level needs to exist for every value.

Expansion of an opaque representation is an explicit transformation.

For example, an image may be represented as an opaque pixel store while a separate transformation exposes selected pixels or metadata.

A database schema may be represented semantically without treating every table row and storage page as graph elements.

An external BLAS implementation may be represented as a callable semantic value whose implementation remains outside the semantic graph.

This allows the semantic model to remain inspectable without requiring every physical resource to become a graph-sized object.

## 27. Compiler and semantic tooling

The compiler is primarily a transformation layer operating on the semantic graph.

A conceptual pipeline is:

    semantic graph
          |
          v
    semantic transformations
          |
          v
    lower representation
          |
          v
    LLVM / other IR
          |
          v
    target transformations
          |
          v
    machine representation

Machine code is therefore a derived representation and may be cached.

The compiler should not be conceptually separate from the semantic transformation machinery.

The same transformation model is intended to support:

- compilation;
- optimization;
- refactoring;
- metaprogramming;
- program generation;
- verification;
- analysis;
- representation conversion.

Tooling should operate on semantic entities rather than requiring source-text reconstruction wherever possible.

Important tooling capabilities include:

- semantic navigation;
- graph inspection;
- graph visualization;
- semantic search;
- refactoring;
- transformation inspection;
- provenance inspection;
- effect inspection;
- contract inspection;
- constraint inspection;
- dependency analysis;
- incremental compilation;
- debugging;
- documentation generation;
- verification.

Source code is one representation of a semantic program.

Machine code is another.

Neither is the canonical program representation.

## 28. Reference semantic model

The language specification should be accompanied by a structured executable reference model.

The initial model is implemented in Python because the goal is to make semantic behaviour easy to inspect, modify, test, and compare before introducing a formal proof system.

The reference model should represent at least:

- `SemanticId`;
- `Value`;
- `Type`;
- `Constraint`;
- `Effect`;
- `Capability`;
- `Contract`;
- `Transform`;
- `SemanticDomain`;
- `State`;
- `Reference`.

The Python model is not the language implementation.

It is an executable specification of the semantic rules sufficiently precise to expose contradictions and test architectural assumptions.

The model should favour explicit data structures over hidden behaviour.

Where the language specification leaves behaviour unresolved, the model should represent the uncertainty rather than silently selecting an arbitrary interpretation.

## 29. Semantic test corpus

The reference model is accompanied by a semantic test corpus.

The corpus is intended to test both positive behaviour and architectural invariants.

Test categories include:

- ordinary semantic behaviour;
- invariant tests;
- negative cases;
- transformations;
- identity;
- state evolution;
- cross-state references;
- equality;
- provenance;
- caching;
- regression cases;
- metamorphic properties.

Property-based testing should be used where it can expose counterexamples that are difficult to construct manually.

The corpus should test relationships between semantic operations rather than only individual functions.

For example, a transformation can be checked against its inverse where the transformation claims to be lossless.

A lossy transformation can be checked against its explicitly declared permitted difference.

State transformations can be checked to ensure that the source state remains unchanged.

Cross-state reference operations can be checked to ensure that they do not silently change the referenced entity.

The corpus is a living part of the specification.

Conceptually:

    language specification
            |
            v
    Python semantic model
            |
            v
    verification tests
            |
            v
    SEMIROH program corpus

Changes to one layer should expose inconsistencies with the others.

## 30. Formal verification

Formal verification is a later layer rather than a prerequisite for initial language development.

Rocq/Coq is a candidate for proving selected semantic invariants.

K is a candidate for executable operational semantics once the operational model is sufficiently mature.

Formalization should follow demonstrated semantic stability rather than freezing an immature design.

The first targets for formal proof should be high-value invariants whose failure would invalidate large parts of the architecture.

Potential targets include:

- state immutability;
- identity/equality separation;
- reference state-relative behaviour;
- explicit cross-state transfer;
- transformation preservation properties;
- capability authority boundaries;
- constraint result soundness.

The Python model remains useful even after formal models exist because it provides a faster exploratory and regression-testing environment.

## 31. High-value invariants

The following invariants are architectural constraints rather than implementation preferences.

1. The semantic graph is the canonical program representation.
2. Semantic values are immutable.
3. Semantic states are immutable.
4. Identity is not equality.
5. Entity identity represents conceptual continuity, not semantic equivalence.
6. State identity represents the exact semantic state, independent of its history.
7. References are state-relative.
8. Cross-state references require explicit transfer or rebinding.
9. Producing a new semantic state and activating that state are separate operations.
10. Transformations produce new states rather than silently mutating existing semantic states.
11. Runtime execution cannot mutate semantic inputs through aliasing.
12. Immutable semantic values may be captured by runtime computation.
13. Semantic mutable execution state cannot cross semantic boundaries implicitly.
14. Capabilities describe authority; effects describe behaviour.
15. Constraints produce `Satisfied`, `Violated`, or `Unknown`.
16. Contracts are independent semantic values.
17. Source code and machine code are representations of semantic state.
18. Opaque values do not need to be graph-expanded.
19. Foreign integration is based on explicit semantic derivation.
20. Implicit behaviour is permitted only where its semantics are clear, predictable, and practically justified.

## 32. State identity and provenance

State identity must describe semantic content, not the path by which that state was produced.

A state reached through two different transformations can therefore have the same semantic state identity if its semantic contents are identical.

Conceptually:

    State A
      | \
      |  \
      v   v
    Transform 1
      |       Transform 2
      v         |
    State B <---+

If `State B` and the state produced by `Transform 2` contain the same semantic state, they are the same state for semantic identity purposes even if their provenance differs.

Provenance therefore belongs to the transition or transformation record, not to the semantic state itself.

Conceptually:

    State A
       |
       | transform
       v
    State B

and separately:

    TransformResult
        |
        +-- source state
        +-- destination state
        +-- entity mappings
        +-- transformation
        +-- provenance
        +-- evidence

This separation prevents `StateID` from becoming history-dependent.

It also permits caching, deduplication, rollback, branching, and provenance tracking without making provenance part of semantic equality or state identity.

## 33. Cross-state references

A reference is meaningful relative to a semantic state.

A reference therefore cannot automatically be reused in an unrelated state merely because an entity with the same conceptual identity exists there.

Cross-state transfer is explicit.

A transfer operation may use an immutable mapping between entities:

    source state
         |
         | mapping
         v
    destination state

The mapping describes how an entity from one state corresponds to an entity in another.

The mapping is not itself part of either state's semantic identity.

A transfer can fail when no valid correspondence exists.

A successful transfer establishes a new reference in the destination state.

This makes state boundaries explicit while still allowing semantic continuity to be preserved across transformations.

## 34. Entity identity across transformations

Entity identity represents conceptual continuity across semantic states.

A transformation may therefore preserve an entity identity while replacing its semantic value.

Possible transformation relationships include:

    one entity -> one entity
    one entity -> many entities
    many entities -> one entity
    one entity -> no entity

These relationships do not imply equality.

For example, replacing a function with an optimized implementation may preserve entity identity while changing its representation.

Splitting one entity into several entities may preserve continuity through an explicit transformation mapping.

Merging several entities into one may likewise preserve provenance without claiming that the original entities were equal.

When continuity cannot be established, the transformation should create new entity identities.

Entity identity is therefore a continuity mechanism, not an equivalence relation.

## 35. Caching and semantic identity

Semantic identity enables caching without making cache state part of semantic state.

Caches may be keyed by:

- semantic state identity;
- entity identity;
- transformation identity;
- representation identity;
- explicit constraint context.

A cache hit is an implementation optimisation.

It must not change semantic equality or observable program meaning.

If a transformation produces a state already present in the cache, the implementation may reuse the existing representation.

The resulting semantic state remains the same regardless of whether computation was performed again or retrieved from cache.

Cache invalidation should therefore be driven by semantic dependencies rather than by arbitrary implementation history.

## 36. Incremental computation

Immutable states naturally support incremental computation.

A transformation can identify the semantic entities it depends on and recompute only affected derived values.

Conceptually:

    old state
       |
       +-- unchanged region
       |
       +-- changed region
                |
                v
          recompute affected
          transformations

Structural sharing may allow unchanged portions of the semantic graph to be reused.

Incremental computation must remain semantically equivalent to recomputing the transformation from the complete source state.

Optimisation metadata, dependency indexes, and cached intermediate representations are therefore derived implementation data rather than semantic state.

## 37. Program modification

Program modification is a transformation over semantic program state.

A program-modification operation does not mutate the currently active program state.

Instead:

    current state
         |
         | ProgramModify
         v
    new state

The new state may then be:

- inspected;
- validated;
- transformed further;
- compared;
- stored;
- activated.

Activation is a separate operation.

This distinction permits tooling and metaprograms to construct alternative program states without changing the running or currently selected program.

It also allows program modification to participate in ordinary transformation provenance and constraint checking.

## 38. Metaprogramming

Metaprogramming is performed through ordinary semantic functions.

There is no separate macro language or fundamentally different metaprogramming object model.

A metaprogram receives semantic values and produces semantic values or semantic transformations.

For example:

    generate(specification) -> semantic value

A program transformation may operate as:

    transform(program_state, specification) -> new_state

Metaprograms therefore use the same value, identity, state, capability, constraint, contract, and transformation machinery as ordinary programs.

Access to program structure is controlled by the capabilities and contracts available to the metaprogram.

This avoids making source text the privileged representation of program structure.

## 39. Metaprogram termination and resource limits

Metaprogramming may perform arbitrary computation, which creates termination and resource-consumption concerns.

SEMIROH does not currently require all semantic computation to be statically proven terminating.

Instead, potentially expensive semantic computation may be subject to explicit budgets.

Possible budgets include:

- computation steps;
- memory;
- recursion depth;
- graph expansion;
- transformation count;
- optional wall-clock limits.

Exceeding a semantic computation budget produces `Unknown` where the requested result is a constraint or other three-valued semantic query.

A computation that produces an ordinary value may instead fail according to its explicit error contract.

The exact budget model remains open.

## 40. Representation independence

Semantic values should not depend on one particular physical representation unless a contract explicitly requires it.

The same semantic value may therefore have multiple representations:

    semantic value
       |
       +--> source representation
       |
       +--> semantic IR
       |
       +--> LLVM IR
       |
       +--> machine code
       |
       +--> serialized form

A representation transformation may preserve semantic identity while changing representation.

Representation equality is therefore distinct from semantic equality.

A representation may also be opaque.

The semantic graph should expose only the information required by the corresponding contract or semantic operation.

## 41. Serialization and persistence

Semantic states should be persistable independently of source text where practical.

A serialized state may contain:

- semantic graph data;
- semantic identities;
- type information;
- contracts;
- constraints;
- transformation references;
- dependency information;
- required capability declarations.

Runtime resources should not automatically be serialized as though they were ordinary semantic values.

External resources require explicit reconstruction or rebinding.

Persistence should preserve semantic state identity when the serialized and reconstructed states are semantically identical.

Serialization metadata and storage layout are implementation details unless constrained by a contract or interchange specification.

## 42. Reproducibility

A reproducible program state requires more than identical source text.

Reproducibility depends on the semantic state and the explicitly selected dependencies, representations, transformations, and relevant external assumptions.

A reproducible build should therefore identify the semantic inputs that determine its result.

External dependencies whose behaviour affects semantic output require explicit contracts or provenance.

Uncontrolled environmental dependencies should not silently become part of the semantic program.

Where exact reproducibility is impossible, the system should expose the relevant uncertainty or external dependency rather than implying deterministic equivalence.

## 43. Dependency representation

Dependencies are semantic relationships.

A dependency may connect:

    consumer -> depends_on -> dependency

Dependencies may be attached to:

- semantic entities;
- transformations;
- representations;
- contracts;
- external resources.

A dependency does not necessarily imply ownership.

A module may depend on another module without owning its semantic state.

Dependency resolution should produce an explicit coherent state rather than relying on ambient mutable environments.

This allows dependency graphs to be inspected, transformed, cached, and reproduced using the same semantic machinery as the rest of the program.

## 44. Design philosophy

SEMIROH is not minimal for the sake of having few primitives.

The objective is to identify a small set of general semantic mechanisms from which useful language features can be composed.

A feature should normally be derived from existing primitives when the derivation is simple, natural, and semantically clear.

A feature should become primitive when deriving it would introduce substantial:

- complexity;
- awkwardness;
- performance cost;
- semantic ambiguity;
- implementation fragility.

The language therefore avoids both extremes:

    everything is primitive

and:

    everything must be derived regardless of cost

The intended balance is pragmatic.

Values, transformations, authority, state transitions, and potentially expensive computation should be explicit where implicit behaviour would make programs difficult to understand or reason about.

At the same time, concise syntax and useful defaults are acceptable when their semantics remain predictable.

## 45. Non-goals

SEMIROH does not aim to:

- reproduce C syntax;
- eliminate every runtime cost through language semantics;
- make every feature a primitive;
- require formal proofs for every program;
- make every semantic value fully graph-expanded;
- provide unrestricted implicit conversions;
- hide mutation behind ordinary value syntax;
- make source code the canonical representation;
- make machine code the canonical representation;
- require garbage collection;
- provide exceptions as the primary error mechanism;
- force one concurrency implementation strategy;
- solve every systems-programming problem inside the language core.

The design should remain small enough to understand while being expressive enough to support systems programming and aggressive tooling.

## 46. Open design areas

The architecture intentionally leaves several areas unresolved until the semantic model provides enough evidence to choose among alternatives.

Important open areas include:

- exact scope and name-resolution graph;
- module root semantics;
- module version activation;
- pointer and reference rules;
- borrowing;
- alias analysis;
- lifetime analysis;
- ownership transfer;
- object movement and pinning;
- exact string and Unicode semantics;
- collection primitives;
- numeric promotion rules;
- control-flow semantics;
- asynchronous suspension;
- task lifetime;
- concurrency memory model;
- capability revocation;
- capability branding;
- effect inference;
- effect hiding;
- contract composition;
- metaprogram resource budgets;
- exact provenance representation;
- transformation mapping semantics;
- serialization format;
- foreign export ABI model;
- representation-level guarantees;
- formal operational semantics.

These are not assumed to be solved merely because a plausible syntax exists.

They should be resolved by consistency with the core semantic model, implementation evidence, test-corpus behaviour, and practical systems requirements.
