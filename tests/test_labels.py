from hypothesis import given
from hypothesis import strategies as st

from quorum import PUBLIC, Conf, Integ, Label, restricted, untrusted

ids = st.frozensets(st.sampled_from(["a", "b", "c", "d"]))
labels = st.builds(Label, ids, ids)


@given(labels, labels, labels)
def test_join_is_associative(a, b, c):
    assert a.join(b).join(c) == a.join(b.join(c)) == a.join(b, c)


@given(labels, labels)
def test_join_is_commutative(a, b):
    assert a | b == b | a


@given(labels)
def test_join_is_idempotent_and_public_is_the_identity(a):
    assert a | a == a and a | PUBLIC == a and PUBLIC.flows_to(a)


@given(labels, labels, labels)
def test_join_is_the_least_upper_bound(a, b, c):
    assert a.flows_to(a | b) and b.flows_to(a | b)
    if a.flows_to(c) and b.flows_to(c):
        assert (a | b).flows_to(c)


@given(labels, labels, labels)
def test_flows_to_is_a_partial_order(a, b, c):
    assert a.flows_to(a)
    if a.flows_to(b) and b.flows_to(a):
        assert a == b
    if a.flows_to(b) and b.flows_to(c):
        assert a.flows_to(c)


@given(labels, labels)
def test_join_never_lowers_confidentiality_nor_raises_integrity(a, b):
    assert (a | b).conf >= max(a.conf, b.conf) and (a | b).integ <= min(a.integ, b.integ)


@given(labels)
def test_dict_round_trip(a):
    assert Label.from_dict(a.to_dict()) == a


def test_levels():
    assert restricted("x").conf is Conf.RESTRICTED and restricted("x").integ is Integ.TRUSTED
    assert untrusted("y").integ is Integ.UNTRUSTED and untrusted("y").conf is Conf.PUBLIC
    assert (restricted("x") | untrusted("y")).sources == {"x", "y"}
