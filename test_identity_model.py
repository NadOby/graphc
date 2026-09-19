"""Tests for the SEMIROH identity and immutable-state model."""

from semiroh import (
    AmbiguousEntityMapping,
    CrossStateReference,
    EntityID,
    MissingEntityMapping,
    OwnershipError,
    State,
    StaleReference,
    Value,
    canonical_serialize,
    project_entity,
    rebind_reference,
    semantic_equal,
    same_entity,
    same_version,
    transfer_reference,
    transform,
    transform_with_mapping,
    version_id_for,
)


def test_entity_version_changes_when_content_changes() -> None:
    foo = EntityID("foo")

    first = Value.create(foo, 1)
    second = Value.create(foo, 2)

    assert first.entity == second.entity
    assert version_id_for(first) != version_id_for(second)
    assert same_entity(first, second)
    assert not same_version(first, second)


def test_identical_entity_versions_have_identical_version_ids() -> None:
    foo = EntityID("foo")

    first = Value.create(foo, 42)
    second = Value.create(foo, 42)

    assert version_id_for(first) == version_id_for(second)
    assert semantic_equal(first, second)
    assert same_entity(first, second)


def test_version_id_is_history_independent() -> None:
    foo = EntityID("foo")

    direct = Value.create(foo, 42)
    intermediate = Value.create(foo, 1)

    assert version_id_for(direct) == version_id_for(
        Value.create(foo, 42)
    )
    assert version_id_for(direct) != version_id_for(intermediate)


def test_reference_is_version_pinned() -> None:
    foo = EntityID("foo")

    state = State.create({
        foo: Value.create(foo, 1),
    })

    reference = state.reference(foo)

    assert reference.state == state.id
    assert reference.entity == foo
    assert reference.version == version_id_for(
        state.values[foo]
    )


def test_cross_state_reference_does_not_rebind() -> None:
    foo = EntityID("foo")

    first = State.create({
        foo: Value.create(foo, 1),
    })

    second = transform(first, {
        foo: 2,
    })

    try:
        second.resolve(first.reference(foo))
    except CrossStateReference:
        pass
    else:
        raise AssertionError(
            "cross-state reference silently rebound"
        )


def test_stale_reference_is_detectable() -> None:
    foo = EntityID("foo")

    state = State.create({
        foo: Value.create(foo, 1),
    })

    reference = state.reference(foo)

    stale = type(reference)(
        state=state.id,
        entity=foo,
        version=version_id_for(
            Value.create(foo, 2)
        ),
    )

    try:
        state.resolve(stale)
    except StaleReference:
        pass
    else:
        raise AssertionError(
            "stale version was accepted"
        )


def test_transfer_requires_explicit_mapping() -> None:
    foo = EntityID("foo")

    first = State.create({
        foo: Value.create(foo, 1),
    })

    second = State.create({
        foo: Value.create(foo, 2),
    })

    try:
        transfer_reference(
            first.reference(foo),
            transform_with_mapping(
                first,
                {},
                {},
            ),
        )
    except MissingEntityMapping:
        pass
    else:
        raise AssertionError(
            "transfer accepted an implicit identity continuation"
        )

    assert second.id != first.id


def test_explicit_mapping_preserves_entity_identity() -> None:
    foo = EntityID("foo")

    first = State.create({
        foo: Value.create(foo, 1),
    })

    result = transform_with_mapping(
        first,
        {foo: 2},
        {foo: foo},
    )

    source_reference = first.reference(foo)
    destination_reference = transfer_reference(
        source_reference,
        result,
    )

    assert project_entity(source_reference) == foo
    assert project_entity(destination_reference) == foo

    assert destination_reference.entity == foo
    assert destination_reference.version == version_id_for(
        result.destination.values[foo]
    )

    assert source_reference.version != destination_reference.version


def test_explicit_mapping_can_rename_entity() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    first = State.create({
        foo: Value.create(foo, 1),
    })

    result = transform_with_mapping(
        first,
        {bar: 2},
        {foo: bar},
    )

    destination_reference = transfer_reference(
        first.reference(foo),
        result,
    )

    assert destination_reference.entity == bar
    assert destination_reference.version == version_id_for(
        result.destination.values[bar]
    )

    assert result.destination.resolve(
        destination_reference
    ).content == 2


def test_rebind_is_not_transfer() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    first = State.create({
        foo: Value.create(foo, 1),
    })

    second = State.create({
        bar: Value.create(bar, 99),
    })

    source_reference = first.reference(foo)

    destination_reference = rebind_reference(
        source_reference,
        second,
        bar,
    )

    assert destination_reference.state == second.id
    assert destination_reference.entity == bar
    assert destination_reference.version == version_id_for(
        second.values[bar]
    )

    assert project_entity(destination_reference) == bar
    assert project_entity(destination_reference) != (
        project_entity(source_reference)
    )


def test_version_fast_path_for_exact_value() -> None:
    foo = EntityID("foo")

    first = State.create({
        foo: Value.create(foo, 42),
    })

    second = State.create({
        foo: Value.create(foo, 42),
    })

    source = first.reference(foo)
    destination = second.reference(foo)

    assert source.entity == destination.entity
    assert source.version == destination.version
    assert semantic_equal(
        first.resolve(source),
        second.resolve(destination),
    )


def test_same_entity_different_versions_are_not_equal() -> None:
    foo = EntityID("foo")

    first = Value.create(foo, 1)
    second = Value.create(foo, 2)

    assert same_entity(first, second)
    assert not semantic_equal(first, second)
    assert not same_version(first, second)


def test_different_entities_same_content_are_equal() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    first = Value.create(foo, 42)
    second = Value.create(bar, 42)

    assert not same_entity(first, second)
    assert semantic_equal(first, second)
    assert version_id_for(first) != version_id_for(second)


def test_state_identity_is_history_independent() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    first = State.create({
        foo: Value.create(foo, 42),
        bar: Value.create(bar, 10),
    })

    second = State.create({
        bar: Value.create(bar, 10),
        foo: Value.create(foo, 42),
    })

    assert first.id == second.id


def test_state_identity_ignores_transition_mapping() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    first = State.create({
        foo: Value.create(foo, 1),
    })

    result_a = transform_with_mapping(
        first,
        {bar: 2},
        {foo: bar},
    )

    result_b = transform_with_mapping(
        first,
        {bar: 2},
        {},
    )

    assert result_a.destination.id == result_b.destination.id
    assert result_a.destination.id != first.id


def test_state_values_are_immutable() -> None:
    foo = EntityID("foo")

    state = State.create({
        foo: Value.create(foo, 1),
    })

    try:
        state.values[foo] = Value.create(foo, 2)
    except TypeError:
        pass
    else:
        raise AssertionError(
            "semantic state values are mutable"
        )

    assert state.values[foo].content == 1


def test_state_ownership_is_immutable() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    state = State.create(
        {
            foo: Value.create(foo, 1),
            bar: Value.create(bar, 2),
        },
        {
            foo: (bar,),
        },
    )

    try:
        state.ownership[foo] = (bar,)
    except TypeError:
        pass
    else:
        raise AssertionError(
            "semantic state ownership is mutable"
        )

    assert state.ownership[foo] == (bar,)


def test_value_content_is_immutable() -> None:
    foo = EntityID("foo")

    original = [1, 2, 3]
    value = Value.create(foo, original)

    original.append(4)

    assert value.content == (
        "__type__",
        "list",
        (1, 2, 3),
    )

    try:
        value.content[2] += (4,)
    except TypeError:
        pass
    else:
        raise AssertionError(
            "canonical semantic value content is mutable"
        )


def test_direct_value_construction_is_immutable() -> None:
    foo = EntityID("foo")

    original = [1, 2, 3]
    value = Value(foo, original)

    original.append(4)

    assert value.content == (
        "__type__",
        "list",
        (1, 2, 3),
    )


def test_original_input_mapping_cannot_mutate_state() -> None:
    foo = EntityID("foo")

    values = {
        foo: Value.create(foo, 1),
    }

    state = State.create(values)

    values[foo] = Value.create(foo, 2)

    assert state.values[foo].content == 1


def test_original_ownership_mapping_cannot_mutate_state() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    ownership = {
        foo: [bar],
    }

    state = State.create(
        {
            foo: Value.create(foo, 1),
            bar: Value.create(bar, 2),
        },
        ownership,
    )

    ownership[foo].append(foo)

    assert state.ownership[foo] == (bar,)


def test_canonical_serialization_is_type_sensitive() -> None:
    assert canonical_serialize(1) != canonical_serialize(True)
    assert canonical_serialize(1) != canonical_serialize("1")
    assert canonical_serialize("1") != canonical_serialize(b"1")


def test_canonical_serialization_is_length_delimited() -> None:
    assert canonical_serialize("ab") != canonical_serialize("a")
    assert canonical_serialize("abc") != canonical_serialize("ab")


def test_canonical_serialization_handles_nested_values() -> None:
    first = {
        "numbers": [1, 2, 3],
        "nested": ("a", b"bc"),
    }

    second = {
        "nested": ("a", b"bc"),
        "numbers": [1, 2, 3],
    }

    assert canonical_serialize(first) == canonical_serialize(second)


def test_canonical_serialization_distinguishes_sequence_types() -> None:
    assert canonical_serialize([1, 2]) != canonical_serialize((1, 2))


def test_canonical_serialization_distinguishes_map_keys_by_type() -> None:
    int_key = {1: "value"}
    bool_key = {True: "value"}

    assert canonical_serialize(int_key) != canonical_serialize(bool_key)


def test_state_identity_uses_canonical_serialization() -> None:
    foo = EntityID("foo")

    first = State.create({
        foo: Value.create(foo, {
            "a": [1, 2, 3],
            "b": ("x", b"y"),
        }),
    })

    second = State.create({
        foo: Value.create(foo, {
            "b": ("x", b"y"),
            "a": [1, 2, 3],
        }),
    })

    assert first.id == second.id


def test_state_identity_is_full_sha256() -> None:
    foo = EntityID("foo")

    state = State.create({
        foo: Value.create(foo, 1),
    })

    assert len(state.id.value) == 64
    assert all(
        character in "0123456789abcdef"
        for character in state.id.value
    )


def test_state_rejects_entity_key_mismatch() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    try:
        State.create({
            foo: Value.create(bar, 42),
        })
    except ValueError:
        pass
    else:
        raise AssertionError(
            "state accepted mismatched entity key and value identity"
        )


def test_ownership_has_single_owner() -> None:
    root = EntityID("root")
    left = EntityID("left")
    right = EntityID("right")

    try:
        State.create(
            {
                root: Value.create(root, 0),
                left: Value.create(left, 1),
                right: Value.create(right, 2),
            },
            {
                root: (left,),
                right: (left,),
            },
        )
    except OwnershipError:
        pass
    else:
        raise AssertionError(
            "ownership accepted multiple owners"
        )


def test_ownership_rejects_self_cycle() -> None:
    foo = EntityID("foo")

    try:
        State.create(
            {
                foo: Value.create(foo, 1),
            },
            {
                foo: (foo,),
            },
        )
    except OwnershipError:
        pass
    else:
        raise AssertionError(
            "ownership accepted self-cycle"
        )


def test_ownership_rejects_recursive_cycle() -> None:
    a = EntityID("a")
    b = EntityID("b")
    c = EntityID("c")

    try:
        State.create(
            {
                a: Value.create(a, 1),
                b: Value.create(b, 2),
                c: Value.create(c, 3),
            },
            {
                a: (b,),
                b: (c,),
                c: (a,),
            },
        )
    except OwnershipError:
        pass
    else:
        raise AssertionError(
            "ownership accepted recursive cycle"
        )


def test_ownership_requires_existing_entities() -> None:
    owner = EntityID("owner")
    missing = EntityID("missing")

    try:
        State.create(
            {
                owner: Value.create(owner, 1),
            },
            {
                owner: (missing,),
            },
        )
    except OwnershipError:
        pass
    else:
        raise AssertionError(
            "ownership accepted an absent child"
        )


def test_owner_and_children_queries() -> None:
    root = EntityID("root")
    left = EntityID("left")
    right = EntityID("right")
    leaf = EntityID("leaf")

    state = State.create(
        {
            root: Value.create(root, 0),
            left: Value.create(left, 1),
            right: Value.create(right, 2),
            leaf: Value.create(leaf, 3),
        },
        {
            root: (left, right),
            left: (leaf,),
        },
    )

    assert state.owner_of(root) is None
    assert state.owner_of(left) == root
    assert state.owner_of(leaf) == left

    assert state.owned_children(root) == (
        left,
        right,
    )

    assert state.owned_children(left) == (
        leaf,
    )

    assert state.owned_subtree(root) == frozenset({
        left,
        right,
        leaf,
    })

    assert state.owned_subtree(left) == frozenset({
        leaf,
    })


def test_ownership_affects_state_identity() -> None:
    root = EntityID("root")
    child = EntityID("child")

    without_ownership = State.create(
        {
            root: Value.create(root, 1),
            child: Value.create(child, 2),
        },
    )

    with_ownership = State.create(
        {
            root: Value.create(root, 1),
            child: Value.create(child, 2),
        },
        {
            root: (child,),
        },
    )

    assert without_ownership.id != with_ownership.id


def test_ownership_order_does_not_affect_state_identity() -> None:
    root = EntityID("root")
    left = EntityID("left")
    right = EntityID("right")

    first = State.create(
        {
            root: Value.create(root, 0),
            left: Value.create(left, 1),
            right: Value.create(right, 2),
        },
        {
            root: (right, left),
        },
    )

    second = State.create(
        {
            root: Value.create(root, 0),
            left: Value.create(left, 1),
            right: Value.create(right, 2),
        },
        {
            root: (left, right),
        },
    )

    assert first.id == second.id


def test_destroy_removes_owned_subtree() -> None:
    root = EntityID("root")
    child = EntityID("child")
    leaf = EntityID("leaf")
    independent = EntityID("independent")

    state = State.create(
        {
            root: Value.create(root, 0),
            child: Value.create(child, 1),
            leaf: Value.create(leaf, 2),
            independent: Value.create(independent, 3),
        },
        {
            root: (child,),
            child: (leaf,),
        },
    )

    destroyed = state.destroy(root)

    assert not destroyed.contains(root)
    assert not destroyed.contains(child)
    assert not destroyed.contains(leaf)
    assert destroyed.contains(independent)
    assert destroyed.ownership == {}


def test_destroy_child_preserves_owner_and_unrelated_entities() -> None:
    root = EntityID("root")
    child = EntityID("child")
    sibling = EntityID("sibling")
    leaf = EntityID("leaf")

    state = State.create(
        {
            root: Value.create(root, 0),
            child: Value.create(child, 1),
            sibling: Value.create(sibling, 2),
            leaf: Value.create(leaf, 3),
        },
        {
            root: (child, sibling),
            child: (leaf,),
        },
    )

    destroyed = state.destroy(child)

    assert destroyed.contains(root)
    assert destroyed.contains(sibling)
    assert not destroyed.contains(child)
    assert not destroyed.contains(leaf)

    assert destroyed.ownership == {
        root: (sibling,),
    }


def test_destroy_does_not_mutate_original_state() -> None:
    root = EntityID("root")
    child = EntityID("child")

    state = State.create(
        {
            root: Value.create(root, 0),
            child: Value.create(child, 1),
        },
        {
            root: (child,),
        },
    )

    destroyed = state.destroy(root)

    assert state.contains(root)
    assert state.contains(child)
    assert state.ownership == {
        root: (child,),
    }

    assert destroyed.values == {}
    assert destroyed.ownership == {}


def test_ordinary_reference_cycles_do_not_affect_ownership() -> None:
    a = EntityID("a")
    b = EntityID("b")

    state = State.create(
        {
            a: Value.create(a, {
                "reference": b,
            }),
            b: Value.create(b, {
                "reference": a,
            }),
        },
        {
            a: (b,),
        },
    )

    assert state.owner_of(b) == a
    assert state.owner_of(a) is None


def test_transform_preserves_ownership_when_entities_are_unchanged() -> None:
    root = EntityID("root")
    child = EntityID("child")

    state = State.create(
        {
            root: Value.create(root, 1),
            child: Value.create(child, 2),
        },
        {
            root: (child,),
        },
    )

    result = transform_with_mapping(
        state,
        {
            root: 10,
            child: 20,
        },
        {
            root: root,
            child: child,
        },
    )

    assert result.destination.ownership == {
        root: (child,),
    }


def test_transform_can_explicitly_remove_ownership() -> None:
    root = EntityID("root")
    child = EntityID("child")

    state = State.create(
        {
            root: Value.create(root, 1),
            child: Value.create(child, 2),
        },
        {
            root: (child,),
        },
    )

    result = transform_with_mapping(
        state,
        {},
        {
            root: root,
            child: child,
        },
        ownership={},
    )

    assert result.destination.ownership == {}
    assert result.destination.contains(root)
    assert result.destination.contains(child)


def test_transform_can_explicitly_change_ownership() -> None:
    root = EntityID("root")
    left = EntityID("left")
    right = EntityID("right")

    state = State.create(
        {
            root: Value.create(root, 0),
            left: Value.create(left, 1),
            right: Value.create(right, 2),
        },
        {
            root: (left,),
        },
    )

    result = transform_with_mapping(
        state,
        {},
        {
            root: root,
            left: left,
            right: right,
        },
        ownership={
            root: (right,),
        },
    )

    assert result.destination.ownership == {
        root: (right,),
    }


def test_transform_does_not_infer_ownership_from_entity_mapping() -> None:
    root = EntityID("root")
    child = EntityID("child")
    new_root = EntityID("new_root")
    new_child = EntityID("new_child")

    state = State.create(
        {
            root: Value.create(root, 0),
            child: Value.create(child, 1),
        },
        {
            root: (child,),
        },
    )

    result = transform_with_mapping(
        state,
        {
            new_root: 10,
            new_child: 11,
        },
        {
            root: new_root,
            child: new_child,
        },
    )

    assert result.destination.ownership == {
        root: (child,),
    }

    assert result.destination.owner_of(child) == root
    assert result.destination.owner_of(new_child) is None


def test_transform_can_explicitly_preserve_ownership_after_rename() -> None:
    root = EntityID("root")
    child = EntityID("child")
    new_root = EntityID("new_root")
    new_child = EntityID("new_child")

    state = State.create(
        {
            root: Value.create(root, 0),
            child: Value.create(child, 1),
        },
        {
            root: (child,),
        },
    )

    result = transform_with_mapping(
        state,
        {
            new_root: 10,
            new_child: 11,
        },
        {
            root: new_root,
            child: new_child,
        },
        ownership={
            new_root: (new_child,),
        },
    )

    assert result.destination.ownership == {
        new_root: (new_child,),
    }

    assert result.destination.owner_of(new_child) == new_root


def test_transform_rejects_invalid_destination_ownership() -> None:
    root = EntityID("root")
    left = EntityID("left")
    right = EntityID("right")

    state = State.create(
        {
            root: Value.create(root, 0),
            left: Value.create(left, 1),
            right: Value.create(right, 2),
        },
        {
            root: (left,),
        },
    )

    try:
        transform_with_mapping(
            state,
            {},
            {
                root: root,
                left: left,
                right: right,
            },
            ownership={
                root: (right,),
                left: (right,),
            },
        )
    except OwnershipError:
        pass
    else:
        raise AssertionError(
            "transform accepted destination ownership with two owners"
        )


def test_transform_rejects_destination_ownership_cycle() -> None:
    root = EntityID("root")
    child = EntityID("child")
    leaf = EntityID("leaf")

    state = State.create(
        {
            root: Value.create(root, 0),
            child: Value.create(child, 1),
            leaf: Value.create(leaf, 2),
        },
    )

    try:
        transform_with_mapping(
            state,
            {},
            {
                root: root,
                child: child,
                leaf: leaf,
            },
            ownership={
                root: (child,),
                child: (leaf,),
                leaf: (root,),
            },
        )
    except OwnershipError:
        pass
    else:
        raise AssertionError(
            "transform accepted cyclic destination ownership"
        )


def test_transform_does_not_mutate_source_ownership() -> None:
    root = EntityID("root")
    child = EntityID("child")
    sibling = EntityID("sibling")

    state = State.create(
        {
            root: Value.create(root, 0),
            child: Value.create(child, 1),
            sibling: Value.create(sibling, 2),
        },
        {
            root: (child,),
        },
    )

    result = transform_with_mapping(
        state,
        {},
        {
            root: root,
            child: child,
            sibling: sibling,
        },
        ownership={
            root: (sibling,),
        },
    )

    assert state.ownership == {
        root: (child,),
    }

    assert result.destination.ownership == {
        root: (sibling,),
    }


def test_transform_changes_state_identity_when_ownership_changes() -> None:
    root = EntityID("root")
    child = EntityID("child")

    state = State.create(
        {
            root: Value.create(root, 1),
            child: Value.create(child, 2),
        },
        {
            root: (child,),
        },
    )

    result = transform_with_mapping(
        state,
        {},
        {
            root: root,
            child: child,
        },
        ownership={},
    )

    assert result.destination.id != state.id


def test_mapped_entities_returns_single_destination() -> None:
    foo = EntityID("foo")
    bar = EntityID("bar")

    state = State.create({
        foo: Value.create(foo, 1),
    })

    result = transform_with_mapping(
        state,
        {
            bar: 2,
        },
        {
            foo: bar,
        },
    )

    assert result.mapped_entities(
        state.reference(foo)
    ) == (bar,)


def test_split_mapping_returns_all_destinations() -> None:
    source = EntityID("source")
    left = EntityID("left")
    right = EntityID("right")

    state = State.create({
        source: Value.create(source, 1),
    })

    result = transform_with_mapping(
        state,
        {
            left: 10,
            right: 20,
        },
        {
            source: (right, left),
        },
    )

    assert result.mapped_entities(
        state.reference(source)
    ) == (
        left,
        right,
    )


def test_split_mapping_is_ambiguous_for_mapped_entity() -> None:
    source = EntityID("source")
    left = EntityID("left")
    right = EntityID("right")

    state = State.create({
        source: Value.create(source, 1),
    })

    result = transform_with_mapping(
        state,
        {
            left: 10,
            right: 20,
        },
        {
            source: (left, right),
        },
    )

    try:
        result.mapped_entity(
            state.reference(source)
        )
    except AmbiguousEntityMapping:
        pass
    else:
        raise AssertionError(
            "mapped_entity silently selected one branch of a split"
        )


def test_split_mapping_cannot_transfer_reference() -> None:
    source = EntityID("source")
    left = EntityID("left")
    right = EntityID("right")

    state = State.create({
        source: Value.create(source, 1),
    })

    result = transform_with_mapping(
        state,
        {
            left: 10,
            right: 20,
        },
        {
            source: (left, right),
        },
    )

    try:
        transfer_reference(
            state.reference(source),
            result,
        )
    except AmbiguousEntityMapping:
        pass
    else:
        raise AssertionError(
            "reference transfer silently selected one split destination"
        )


def test_explicit_disappearance_is_distinct_from_missing_mapping() -> None:
    source = EntityID("source")

    state = State.create({
        source: Value.create(source, 1),
    })

    result = transform_with_mapping(
        state,
        {},
        {
            source: (),
        },
    )

    assert result.mapped_entities(
        state.reference(source)
    ) == ()

    try:
        result.mapped_entity(
            state.reference(source)
        )
    except MissingEntityMapping:
        pass
    else:
        raise AssertionError(
            "explicit disappearance was not rejected as missing destination"
        )


def test_disappearance_cannot_transfer_reference() -> None:
    source = EntityID("source")

    state = State.create({
        source: Value.create(source, 1),
    })

    result = transform_with_mapping(
        state,
        {},
        {
            source: (),
        },
    )

    try:
        transfer_reference(
            state.reference(source),
            result,
        )
    except MissingEntityMapping:
        pass
    else:
        raise AssertionError(
            "reference to a disappeared entity was transferred"
        )


def test_merge_maps_multiple_sources_to_one_destination() -> None:
    first = EntityID("first")
    second = EntityID("second")
    merged = EntityID("merged")

    state = State.create({
        first: Value.create(first, 1),
        second: Value.create(second, 2),
    })

    result = transform_with_mapping(
        state,
        {
            merged: 3,
        },
        {
            first: merged,
            second: merged,
        },
    )

    assert result.mapped_entities(
        state.reference(first)
    ) == (merged,)

    assert result.mapped_entities(
        state.reference(second)
    ) == (merged,)

    assert result.mapped_entity(
        state.reference(first)
    ) == merged

    assert result.mapped_entity(
        state.reference(second)
    ) == merged


def test_merge_allows_both_references_to_transfer() -> None:
    first = EntityID("first")
    second = EntityID("second")
    merged = EntityID("merged")

    state = State.create({
        first: Value.create(first, 1),
        second: Value.create(second, 2),
    })

    result = transform_with_mapping(
        state,
        {
            merged: 3,
        },
        {
            first: merged,
            second: merged,
        },
    )

    first_reference = transfer_reference(
        state.reference(first),
        result,
    )

    second_reference = transfer_reference(
        state.reference(second),
        result,
    )

    assert first_reference.entity == merged
    assert second_reference.entity == merged
    assert first_reference.state == result.destination.id
    assert second_reference.state == result.destination.id


def test_many_to_many_mapping_returns_complete_relation() -> None:
    first = EntityID("first")
    second = EntityID("second")
    left = EntityID("left")
    right = EntityID("right")

    state = State.create({
        first: Value.create(first, 1),
        second: Value.create(second, 2),
    })

    result = transform_with_mapping(
        state,
        {
            left: 10,
            right: 20,
        },
        {
            first: (right, left),
            second: (left, right),
        },
    )

    assert result.mapped_entities(
        state.reference(first)
    ) == (
        left,
        right,
    )

    assert result.mapped_entities(
        state.reference(second)
    ) == (
        left,
        right,
    )


def test_mapping_destination_order_is_canonicalized() -> None:
    source = EntityID("source")
    left = EntityID("left")
    right = EntityID("right")

    state = State.create({
        source: Value.create(source, 1),
    })

    result_a = transform_with_mapping(
        state,
        {
            left: 10,
            right: 20,
        },
        {
            source: (right, left),
        },
    )

    result_b = transform_with_mapping(
        state,
        {
            left: 10,
            right: 20,
        },
        {
            source: (left, right),
        },
    )

    assert result_a.mappings == result_b.mappings


def test_mapping_source_order_is_canonicalized() -> None:
    first = EntityID("first")
    second = EntityID("second")
    left = EntityID("left")
    right = EntityID("right")

    state = State.create({
        first: Value.create(first, 1),
        second: Value.create(second, 2),
    })

    result_a = transform_with_mapping(
        state,
        {
            left: 10,
            right: 20,
        },
        {
            second: (right,),
            first: (left,),
        },
    )

    result_b = transform_with_mapping(
        state,
        {
            left: 10,
            right: 20,
        },
        {
            first: (left,),
            second: (right,),
        },
    )

    assert result_a.mappings == result_b.mappings


def test_duplicate_destinations_are_rejected() -> None:
    source = EntityID("source")
    destination = EntityID("destination")

    state = State.create({
        source: Value.create(source, 1),
    })

    try:
        transform_with_mapping(
            state,
            {
                destination: 2,
            },
            {
                source: (
                    destination,
                    destination,
                ),
            },
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "mapping accepted duplicate destination entities"
        )


def test_missing_mapping_and_explicit_disappearance_are_distinct() -> None:
    source = EntityID("source")

    state = State.create({
        source: Value.create(source, 1),
    })

    result = transform_with_mapping(
        state,
        {},
        {},
    )

    try:
        result.mapped_entities(
            state.reference(source)
        )
    except MissingEntityMapping:
        pass
    else:
        raise AssertionError(
            "missing mapping was confused with explicit disappearance"
        )

    explicit = transform_with_mapping(
        state,
        {},
        {
            source: (),
        },
    )

    assert explicit.mapped_entities(
        state.reference(source)
    ) == ()


def test_mapping_requires_existing_source_entity() -> None:
    source = EntityID("source")
    missing = EntityID("missing")
    destination = EntityID("destination")

    state = State.create({
        source: Value.create(source, 1),
    })

    try:
        transform_with_mapping(
            state,
            {
                destination: 2,
            },
            {
                missing: destination,
            },
        )
    except KeyError:
        pass
    else:
        raise AssertionError(
            "mapping accepted an absent source entity"
        )


def test_mapping_requires_existing_destination_entity() -> None:
    source = EntityID("source")
    missing = EntityID("missing")

    state = State.create({
        source: Value.create(source, 1),
    })

    try:
        transform_with_mapping(
            state,
            {},
            {
                source: missing,
            },
        )
    except KeyError:
        pass
    else:
        raise AssertionError(
            "mapping accepted an absent destination entity"
        )


def test_mapping_accepts_bare_entity_id_compatibility_form() -> None:
    source = EntityID("source")
    destination = EntityID("destination")

    state = State.create({
        source: Value.create(source, 1),
    })

    result = transform_with_mapping(
        state,
        {
            destination: 2,
        },
        {
            source: destination,
        },
    )

    assert result.mapped_entities(
        state.reference(source)
    ) == (destination,)


def test_transition_mapping_does_not_affect_destination_state_identity() -> None:
    source = EntityID("source")
    destination = EntityID("destination")

    state = State.create({
        source: Value.create(source, 1),
    })

    mapped = transform_with_mapping(
        state,
        {
            destination: 2,
        },
        {
            source: destination,
        },
    )

    unmapped = transform_with_mapping(
        state,
        {
            destination: 2,
        },
        {},
    )

    assert mapped.destination.id == unmapped.destination.id


def test_transition_mapping_does_not_modify_ownership() -> None:
    source = EntityID("source")
    destination = EntityID("destination")
    child = EntityID("child")

    state = State.create(
        {
            source: Value.create(source, 1),
            destination: Value.create(destination, 2),
            child: Value.create(child, 3),
        },
        {
            source: (child,),
        },
    )

    result = transform_with_mapping(
        state,
        {},
        {
            source: destination,
        },
    )

    assert result.destination.ownership == {
        source: (child,),
    }


def run_all_tests() -> None:
    tests = [
        test_entity_version_changes_when_content_changes,
        test_identical_entity_versions_have_identical_version_ids,
        test_version_id_is_history_independent,
        test_reference_is_version_pinned,
        test_cross_state_reference_does_not_rebind,
        test_stale_reference_is_detectable,
        test_transfer_requires_explicit_mapping,
        test_explicit_mapping_preserves_entity_identity,
        test_explicit_mapping_can_rename_entity,
        test_rebind_is_not_transfer,
        test_version_fast_path_for_exact_value,
        test_same_entity_different_versions_are_not_equal,
        test_different_entities_same_content_are_equal,
        test_state_identity_is_history_independent,
        test_state_identity_ignores_transition_mapping,
        test_state_values_are_immutable,
        test_state_ownership_is_immutable,
        test_value_content_is_immutable,
        test_direct_value_construction_is_immutable,
        test_original_input_mapping_cannot_mutate_state,
        test_original_ownership_mapping_cannot_mutate_state,
        test_canonical_serialization_is_type_sensitive,
        test_canonical_serialization_is_length_delimited,
        test_canonical_serialization_handles_nested_values,
        test_canonical_serialization_distinguishes_sequence_types,
        test_canonical_serialization_distinguishes_map_keys_by_type,
        test_state_identity_uses_canonical_serialization,
        test_state_identity_is_full_sha256,
        test_state_rejects_entity_key_mismatch,
        test_ownership_has_single_owner,
        test_ownership_rejects_self_cycle,
        test_ownership_rejects_recursive_cycle,
        test_ownership_requires_existing_entities,
        test_owner_and_children_queries,
        test_ownership_affects_state_identity,
        test_ownership_order_does_not_affect_state_identity,
        test_destroy_removes_owned_subtree,
        test_destroy_child_preserves_owner_and_unrelated_entities,
        test_destroy_does_not_mutate_original_state,
        test_ordinary_reference_cycles_do_not_affect_ownership,
        test_transform_preserves_ownership_when_entities_are_unchanged,
        test_transform_can_explicitly_remove_ownership,
        test_transform_can_explicitly_change_ownership,
        test_transform_does_not_infer_ownership_from_entity_mapping,
        test_transform_can_explicitly_preserve_ownership_after_rename,
        test_transform_rejects_invalid_destination_ownership,
        test_transform_rejects_destination_ownership_cycle,
        test_transform_does_not_mutate_source_ownership,
        test_transform_changes_state_identity_when_ownership_changes,
        test_mapped_entities_returns_single_destination,
        test_split_mapping_returns_all_destinations,
        test_split_mapping_is_ambiguous_for_mapped_entity,
        test_split_mapping_cannot_transfer_reference,
        test_explicit_disappearance_is_distinct_from_missing_mapping,
        test_disappearance_cannot_transfer_reference,
        test_merge_maps_multiple_sources_to_one_destination,
        test_merge_allows_both_references_to_transfer,
        test_many_to_many_mapping_returns_complete_relation,
        test_mapping_destination_order_is_canonicalized,
        test_mapping_source_order_is_canonicalized,
        test_duplicate_destinations_are_rejected,
        test_missing_mapping_and_explicit_disappearance_are_distinct,
        test_mapping_requires_existing_source_entity,
        test_mapping_requires_existing_destination_entity,
        test_mapping_accepts_bare_entity_id_compatibility_form,
        test_transition_mapping_does_not_affect_destination_state_identity,
        test_transition_mapping_does_not_modify_ownership,
    ]

    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all_tests()
    print("All identity/version/reference/ownership tests passed.")
