from difflib import SequenceMatcher
from typing import List, TypeVar, Callable, Tuple

from constants import REGION_ABBREVS, KNOWN_REGION_NAMES

T = TypeVar('T')


def fuzzy_score(query: str, target: str) -> float:
    """Similarity ratio between query and target, 0–1."""
    return SequenceMatcher(None, query.lower(), target.lower()).ratio()


def fuzzy_filter(
    query: str,
    items: List[T],
    key_fn: Callable[[T], str],
    threshold: float = 0.5,
) -> List[T]:
    """
    Filter and re-rank items by fuzzy similarity of key_fn(item) to query.
    Items below threshold are dropped; remainder sorted best-first.
    """
    scored = [
        (fuzzy_score(query, key_fn(item)), item)
        for item in items
    ]
    return [
        item for _, item in
        sorted(
            ((s, i) for s, i in scored if s >= threshold),
            key=lambda x: x[0],
            reverse=True,
        )
    ]


def get_search_prefix(term: str) -> str:
    """
    Return a shortened prefix for broader API searches.
    Trims the last 2 chars on terms longer than 4 chars so a single
    end-of-word typo still hits the right prefix bucket.
    e.g. "housten" → "houst", "seatle" → "seat", "plano" → "pla"
    """
    if len(term) <= 4:
        return term
    return term[:max(3, len(term) - 2)]


def parse_location_query(query: str) -> Tuple[str, str]:
    """
    Parse a freeform location query into (city_search_term, region_filter).

    Handles:
      "plano"            → ("plano", "")
      "plano, texas"     → ("plano", "texas")
      "plano, tx"        → ("plano", "tx")
      "plano texas"      → ("plano", "texas")
      "plano tx"         → ("plano", "tx")
      "new york"         → ("new york", "")
      "new york, ny"     → ("new york", "ny")
      "north carolina"   → ("north carolina", "")
    """
    query = query.strip()

    if ',' in query:
        parts = [p.strip() for p in query.split(',', 1)]
        return parts[0], parts[1]

    words = query.split()
    if len(words) <= 1:
        return query, ''

    last = words[-1].lower()

    if last in REGION_ABBREVS:
        return ' '.join(words[:-1]), last

    if last in KNOWN_REGION_NAMES:
        return ' '.join(words[:-1]), last

    if len(words) >= 3:
        last_two = ' '.join(words[-2:]).lower()
        if last_two in KNOWN_REGION_NAMES:
            return ' '.join(words[:-2]), last_two

    # Fallback: first word is city, rest treated as region filter
    return words[0], ' '.join(words[1:])


def matches_region(result_name: str, region_filter: str) -> bool:
    """Check if a formatted city result matches the region filter."""
    if not region_filter:
        return True

    result_lower = result_name.lower()
    filter_lower = region_filter.lower().strip()

    if filter_lower in result_lower:
        return True

    expanded = REGION_ABBREVS.get(filter_lower, '')
    if expanded and expanded in result_lower:
        return True

    return all(
        word in result_lower or REGION_ABBREVS.get(word, '') in result_lower
        for word in filter_lower.split()
    )
