"""How the eval compares merchant names (spec behavior 13). Not used by the program itself."""

import re


def words(name: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", name.lower()))


def same_merchant(read: str, expected: str) -> bool:
    """Same set of words, ignoring case, punctuation and order. Extra words do not match."""
    return bool(words(expected)) and words(read) == words(expected)


def strict_merchant(read: str, expected: str) -> bool:
    """The compare we did not choose, kept so CHECKS.md can show what it would have said."""
    return read.strip().lower() == expected.strip().lower()
