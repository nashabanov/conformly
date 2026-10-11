# Only recognize obvious universal patterns; this is not a satisfiability solver.
# Matching the empty string alone is insufficient: anchors/lookarounds can restrict it.
_UNIVERSAL_SEARCH_PATTERNS = frozenset(
    {"", ".*", ".*?", "(?s).*", "(?s).*?", "(?s:.*)", "(?s)^.*$"}
)


def is_universal_pattern(pattern: str) -> bool:
    return pattern in _UNIVERSAL_SEARCH_PATTERNS
