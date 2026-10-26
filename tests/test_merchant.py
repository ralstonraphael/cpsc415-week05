"""Behavior 13: the eval's merchant compare ignores case, punctuation and word order."""

from merchant import same_merchant, strict_merchant


def test_word_order_does_not_matter():
    # Receipt 5 prints "Bake Sale - CS Club"; the answer key says "CS Club Bake Sale".
    assert same_merchant("Bake Sale - CS Club", "CS Club Bake Sale")


def test_case_and_punctuation_do_not_matter():
    assert same_merchant("LONG WALK COFFEE.", "Long Walk Coffee")


def test_extra_words_do_not_match():
    """An address added to the name is a misread: the instruction asks for the name only."""
    assert not same_merchant("Mather Dining Hall, Trinity College, Hartford CT", "Mather Dining Hall")


def test_different_names_do_not_match():
    assert not same_merchant("Trinity Bookstore", "Trinity Coffee")


def test_empty_name_never_matches():
    assert not same_merchant("", "")


def test_strict_compare_is_case_insensitive_only():
    """Recorded next to the word-set result in CHECKS.md, so the spec decision is visible."""
    assert strict_merchant("trinity bookstore", "Trinity Bookstore")
    assert not strict_merchant("Bake Sale - CS Club", "CS Club Bake Sale")
