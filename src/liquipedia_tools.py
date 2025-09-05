# -*- coding: utf-8 -*-

import json
import re
import requests
import time

from typing import List, Dict, Tuple, Any, Optional

"""File Information
@file_name: startgg_tools.py
@author: Dylan "dyl-m" Monfret
Collection of "Liquipedia tools" and useful functions
"""

# Global Variables

# Liquipedia Rocket League API URL
LIQUIPEDIA_RL_API = "https://liquipedia.net/rocketleague/api.php"

# Provide a clear and contactable User-Agent per Liquipedia rules.
DEFAULT_USER_AGENT = "MyRLApp/1.0 (contact: youremail@example.com)"


# Class

class LiquipediaAPIError(Exception):
    """Raised when Liquipedia API returns an error or unexpected payload."""


# Public Methods

def format_team_card_from_entry(entry: Dict[str, Any], remove_empty_optional: bool = False) -> str:
    """
    Format a team entry (provided JSON structure) into the Liquipedia Rocket League TeamCard template.

    Rules:
    - |team| = team name
    - |p1|, |p2|, |p3| = first 3 members (starters)
    - |s4| = 4th member if present (substitute)
      - if remove_empty_optional=True and no substitute -> line omitted
      - else -> line present, possibly empty
    - |c| and |cflag| = coach, always empty by default
      - if remove_empty_optional=True -> line omitted
      - else -> line present (empty)

    Args:
        entry: Team dictionary with keys like "team_name" and "members".
        remove_empty_optional: If True, omit optional s4/c lines when they would be empty.

    Returns:
        A string representing a Liquipedia TeamCard template.
    """
    team_name = _safe_str(entry.get("team_name"))
    members: List[Dict[str, Any]] = entry.get("members", [])

    starters = members[:3]
    subs = members[3:]

    def tag(i: int) -> str:
        return _safe_str(starters[i].get("player_tag")) if i < len(starters) else ""

    def flag(i: int) -> str:
        return _normalize_flag(starters[i].get("player_country")) if i < len(starters) else ""

    s4_tag = _safe_str(subs[0].get("player_tag")) if len(subs) >= 1 else ""
    s4_flag = _normalize_flag(subs[0].get("player_country")) if len(subs) >= 1 else ""

    lines = [
        "{{TeamCard",
        f"|team={team_name}",
        f"|p1={tag(0)}|p1flag={flag(0)}",
        f"|p2={tag(1)}|p2flag={flag(1)}",
        f"|p3={tag(2)}|p3flag={flag(2)}",
    ]

    # s4 (remplaçant)
    has_sub = bool(s4_tag or s4_flag)
    if has_sub or not remove_empty_optional:
        lines.append(f"|s4={s4_tag}|s4flag={s4_flag}")

    # c (coach) toujours vide côté données
    if not remove_empty_optional:
        lines.append(f"|c=|cflag=")

    lines.append("}}")
    return "\n".join(lines)


def generate_team_cards_from_json(json_path: str, include_box_wrappers: bool = True) -> str:
    """
    Load a JSON file (list of teams) and return a text block
    containing the Liquipedia TeamCards for each team.

    List formatting:
    - starts with: {{box|start|padding=2em}}
    - each team separated by: {{box|break|padding=2em}}
    - ends with: {{box|end}}

    Args:
        json_path: Path to the input JSON file (e.g., data/3v3-sam-champions-road-2025.json).
        include_box_wrappers: Whether to wrap the cards between start/end box templates.

    Returns:
        A string with all generated TeamCards, optionally wrapped in box templates.

    Raises:
        ValueError: If the JSON root is not a list of teams.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Le JSON attendu doit être une liste d'équipes.")

    cards = [format_team_card_from_entry(entry) for entry in data]

    if not include_box_wrappers:
        return "\n\n".join(cards)

    return _join_cards_with_boxes(cards)


def save_team_cards_from_json(json_path: str, out_path: str, include_box_wrappers: bool = True,
                              remove_empty_optional: bool = False) -> None:
    """
    Génère et enregistre les TeamCards Liquipedia à partir d'un JSON d'équipes.
    """
    content = generate_team_cards_from_json(
        json_path,
        include_box_wrappers=include_box_wrappers,
        remove_empty_optional=remove_empty_optional,
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_team_cards_tabs_from_json(json_path: str, segments: List[int], remove_empty_optional: bool = False) -> str:
    """
    Generate a full block with dynamic tabs and boxed sections by ranking segments.

    Structure:
    {{Tabs dynamic
    |name1=...
    |name2=...
    ...
    |content1=
    {{box|start|padding=2em}}
    ... TeamCards [...]
    {{box|end}}
    |content2=
    {{box|start|padding=2em}}
    ... TeamCards [...]
    {{box|end}}}}

    Args:
        json_path: Path to the input teams JSON file.
        segments: Sorted list of upper placement bounds used to create tabs (e.g., [12, 32]).
        remove_empty_optional: If True, omit optional s4/c lines when they would be empty.

    Returns:
        A string containing a Tabs dynamic block with one content section per segment,
        each section containing boxed TeamCards.

    Raises:
        ValueError: If the JSON root is not a list of teams.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Le JSON attendu doit être une liste d'équipes.")

    header = _build_tabs_header(segments)
    buckets = _split_entries_by_segments(data, segments)

    # Construit les contenus
    content_blocks: List[str] = [header]

    for idx, bucket in enumerate(buckets, start=1):
        cards = [format_team_card_from_entry(entry, remove_empty_optional=remove_empty_optional) for entry in bucket]
        # Section contentX
        content_blocks.append(f"|content{idx}=")
        # Bloc box pour ce segment
        box_block = _join_cards_with_boxes(cards)
        content_blocks.append(box_block)

    # Fermeture finale des Tabs
    content_blocks.append("}}\n{{Team card columns end}}")

    return "\n".join(content_blocks)


def get_rocket_league_player_info(player_name: str, user_agent: Optional[str] = None) -> \
        (dict[str, None] | dict[str, str | None] | None | dict[Any, Any]):
    """
    Given a Rocket League player name (query), returns:
    - canonical_name: The page title chosen by Liquipedia editors (top-of-page title).
    - current_team: The current team, unless the player is marked as 'Inactive' (or 'Retired') in the infobox.

    This function does not require authentication and follows Liquipedia etiquette:
    - Descriptive User-Agent.
    - Uses maxlag and modest retries.

    Args:
        player_name: User-provided player name or handle.
        user_agent: Optional custom User-Agent; if omitted, a default is used.

    Returns:
        Dict with keys: canonical_name (str|None), current_team (str|None), status (str|None).

    Raises:
        LiquipediaAPIError on network/API problems.
    """
    # Step 1: Find a likely page title for the player
    candidate_title = _search_player_page(player_name, user_agent=user_agent)
    if not candidate_title:
        return {"canonical_name": None, "current_team": None, "status": None}

    # Step 2: Resolve to canonical title (follows redirects/normalization)
    canonical_title = _resolve_canonical_title(candidate_title, user_agent=user_agent)
    if not canonical_title:
        return {"canonical_name": None, "current_team": None, "status": None}

    # Step 3: Fetch wikitext and extract infobox
    wikitext = _get_page_wikitext(canonical_title, user_agent=user_agent)
    if not wikitext:
        return {"canonical_name": canonical_title, "current_team": None, "status": None}

    infobox = _extract_infobox_block(wikitext)
    # Empty Infobox means there is nothing to parse
    if not infobox:
        return None

    # Step 4: Parse infobox and derive team and status
    params = _parse_infobox_params(infobox)
    team, status = _derive_team_from_infobox(params)

    return {
        "canonical_name": canonical_title,
        "current_team": team,
        "status": status,
    }


# > Internal Functions

def _normalize_flag(country: Optional[str]) -> str:
    """
    Normalize a country code (e.g., 'BR') into a string acceptable for Liquipedia.

    Args:
        country: Country ISO-2 code or None.

    Returns:
        A lowercased ISO-2 code string if provided, otherwise an empty string.
    """
    return country.lower() or ""


def _safe_str(value: Optional[str]) -> str:
    """
    Avoid 'None' in text fields.

    Args:
        value: Input string or None.

    Returns:
        The original string or an empty string if "value" is not set.
    """
    return value or ""


def _join_cards_with_boxes(cards: List[str]) -> str:
    """
    Build a boxed block with the provided TeamCards.

    Start: {{box|start|padding=2em}}
    Separator: {{box|break|padding=2em}}
    End: {{box|end}}

    Args:
        cards: List of TeamCard strings.

    Returns:
        A single boxed string containing all TeamCards separated by box breaks.
    """
    start = "{{box|start|padding=2em}}"
    sep = "\n{{box|break|padding=2em}}\n"
    end = "{{box|end}}"

    if not cards:
        # Bloc vide, mais structure respectée
        return "\n".join([start, end])

    return "\n".join([start, sep.join(cards), end])


def _build_tabs_header(segments: List[int]) -> str:
    """
    Build the Tabs dynamic header, without the final closing '}}'.

    Example for [12, 32, 48, 64]:
    {{TeamCardToggleButton}}
    {{Team card columns start|cols=4}}
    {{Tabs dynamic
    |name1=Top 12
    |name2=Places 13-32
    |name3=Places 33-48
    |name4=Places 49-64

    Args:
        segments: Sorted list of upper bounds for each tab (e.g., [12, 32]).

    Returns:
        The header lines for a Tabs dynamic block with |nameX= entries.
    """
    if not segments:
        # Un seul onglet sans borne -> "All"
        return "{{Tabs dynamic\n|name1=All"

    lines = ["{{TeamCardToggleButton}}\n{{Team card columns start|cols=4}}\n{{Tabs dynamic"]
    prev_end = 0
    for idx, end in enumerate(segments, start=1):
        if idx == 1:
            lines.append(f"|name{idx}=Top {end}")
        else:
            start = prev_end + 1
            lines.append(f"|name{idx}=Places {start}-{end}")
        prev_end = end
    return "\n".join(lines)


def _split_entries_by_segments(entries: List[Dict[str, Any]], segments: List[int]) -> List[List[Dict[str, Any]]]:
    """
    Split teams by segments according to 'placement'.

    - Segment "i" covers (prev_end+1) ... segments[i].
    - Entries beyond the last segment are ignored (strict behavior).
    NOTE: Preserve input order; do not sort the entries here.

    Args:
        entries: List of team entries, each expected to have a numeric 'placement'.
        segments: Sorted list of upper bounds defining the placement ranges.

    Returns:
        A list of buckets (lists of entries), one per segment. If segments is empty,
        returns a single bucket containing all entries.
    """
    # Preserve input order: no sorting here; just bucket by placement
    entries_iter = entries

    buckets: List[List[Dict[str, Any]]] = [[] for _ in segments] if segments else [entries_iter[:]]

    if not segments:
        return buckets

    for e in entries_iter:
        placement = e.get("placement")
        if not isinstance(placement, int):
            continue  # ignore malformed entries
        # Find the first segment whose upper bound >= placement
        for i, end in enumerate(segments):
            start = segments[i - 1] + 1 if i > 0 else 1
            if start <= placement <= end:
                buckets[i].append(e)
                break
        # else: placement > last bound -> ignored (strict)
    return buckets


def _lp_get(params: Dict[str, str], user_agent: Optional[str] = None, retries: int = 3, backoff: float = 1.0) -> dict:
    """
    Perform a GET request to Liquipedia MediaWiki API with sensible defaults.

    - Adds 'format=json' & 'formatversion=2'.
    - Sends maxlag to avoid stressing the cluster.
    - Retries on transient errors and maxlag responses.

    Args:
        params: Query parameters for the API.
        user_agent: Custom User-Agent; must be descriptive with contact.
        retries: Number of retries for transient errors.
        backoff: Base backoff (in seconds) used for exponential backoff between retries.

    Returns:
        Parsed JSON dict from the API.

    Raises:
        LiquipediaAPIError: If the request ultimately fails due to network/HTTP/API errors after retries.
    """
    headers = {
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "application/json",
    }
    base = {
        "format": "json",
        "formatversion": "2",
        "maxlag": "5",
    }
    query = {**base, **params}

    for attempt in range(retries):
        try:
            resp = requests.get(LIQUIPEDIA_RL_API, params=query, headers=headers, timeout=15)
        except requests.RequestException as exc:
            # Transient network error: retry with backoff
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise LiquipediaAPIError(f"Network error contacting Liquipedia: {exc}") from exc

        # Handle HTTP errors
        if resp.status_code >= 500:
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise LiquipediaAPIError(f"Liquipedia server error (HTTP {resp.status_code})")
        if resp.status_code == 429:
            # Too many requests: back off more
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt + 1))
                continue
            raise LiquipediaAPIError("Rate limited by Liquipedia (HTTP 429). Please slow down.")

        data = resp.json()

        # MediaWiki maxlag signal can be returned in 'error' or warnings
        if "error" in data:
            code = data["error"].get("code")
            if code == "maxlag" and attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise LiquipediaAPIError(f"API error: {data['error']}")

        return data

    # Shouldn't reach here because of returns/raises above
    raise LiquipediaAPIError("Exhausted retries without a successful response.")


def _search_player_page(query: str, user_agent: Optional[str] = None) -> Optional[str]:
    """
    Use MediaWiki 'search' to find the most relevant player page title.

    Strategy:
    - Prefer titles in Player namespace if available.
    - Otherwise, fall back to the top search result.

    Args:
        query: The player name or handle to search for (free text).
        user_agent: Optional custom User-Agent for the underlying API calls.

    Returns:
        A page title (string) or None if no result.

    Raises:
        LiquipediaAPIError: If the API request fails.
    """
    data = _lp_get(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": "5",
            "srprop": "",
            "srwhat": "text",  # Search across page text; more flexible than only titles
        },
        user_agent=user_agent,
    )
    results = data.get("query", {}).get("search", []) or []
    if not results:
        return None

    # Prefer exact-ish title match (case-insensitive)
    lowered = query.strip().lower()
    for r in results:
        if r.get("title", "").strip().lower() == lowered:
            return r["title"]

    # Otherwise return the first result
    return results[0]["title"]


def _resolve_canonical_title(title: str, user_agent: Optional[str] = None) -> Optional[str]:
    """
    Resolve redirects/normalization to get the canonical page title.

    Args:
        title: A page title candidate, possibly non-canonical or a redirect.
        user_agent: Optional custom User-Agent for the API call.

    Returns:
        Canonical page title or None if the page is missing.

    Raises:
        LiquipediaAPIError: If the API request fails.
    """
    data = _lp_get(
        {
            "action": "query",
            "prop": "info",
            "titles": title,
            "redirects": "1",  # Follow redirects to get the final, canonical title
        },
        user_agent=user_agent,
    )
    pages = data.get("query", {}).get("pages", []) or []
    if not pages:
        return None
    page = pages[0]
    if page.get("missing"):
        return None
    return page.get("title")


def _get_page_wikitext(title: str, user_agent: Optional[str] = None) -> Optional[str]:
    """
    Fetch wikitext of the page via action=parse.

    Args:
        title: Canonical page title from Liquipedia.
        user_agent: Optional custom User-Agent for the API call.

    Returns:
        Wikitext string or None if parsing fails or page contains no wikitext.

    Raises:
        LiquipediaAPIError: If the API request fails.
    """
    data = _lp_get(
        {
            "action": "parse",
            "page": title,
            "prop": "wikitext",
        },
        user_agent=user_agent,
    )
    parse = data.get("parse", {})
    wikitext = parse.get("wikitext", "")
    return wikitext or None


def _extract_infobox_block(wikitext: str) -> Optional[str]:
    """
    Extract the Infobox player template block from page wikitext.

    The infobox usually starts with 'Infobox player' (case-insensitive).
    This function attempts a balanced-braces extraction for the first such template.

    Args:
        wikitext: Raw page wikitext as returned by the parse API.

    Returns:
        The raw infobox template text (including outer braces) if found, otherwise None.
    """
    # Find the start of infobox by marker
    start_match = re.search(r"\{\{\s*Infobox\s+player[^{]*", wikitext, flags=re.IGNORECASE)
    if not start_match:
        return None
    start_idx = start_match.start()

    # Balanced braces extraction from start_idx.
    # Note: This is a simple stack depth approach and does not parse nested templates fully,
    # but works reliably for well-formed infobox blocks.
    depth = 0
    i = start_idx
    while i < len(wikitext):
        if wikitext[i: i + 2] == "{{":
            depth += 1
            i += 2
            continue
        if wikitext[i: i + 2] == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return wikitext[start_idx:i]
            continue
        i += 1

    return None


def _parse_infobox_params(infobox: str) -> Dict[str, str]:
    """
    Parse simple key=value pairs inside the infobox.

    This is a lightweight parser:
    - Splits by lines starting with '|' to capture parameters.
    - Keeps the first occurrence of a key.
    - Trims markup braces around simple links/templates where possible.

    Args:
        infobox: The raw infobox template string including braces (as returned by _extract_infobox_block).

    Returns:
        Dict of lowercased parameter keys to raw string values.
    """
    params: Dict[str, str] = {}
    # Extract the body after the template name line
    # e.g., "{{Infobox player\n| id = X\n| team = Y\n}}"
    body = infobox.split("\n", 1)[1] if "\n" in infobox else infobox

    for line in body.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        # Remove the leading '|' and split on the first '='
        # noinspection PyBroadException
        try:
            key_val = line.lstrip()[1:]
            if "=" not in key_val:
                continue
            key, val = key_val.split("=", 1)
            key = key.strip().lower()
            val = val.strip()
            if key and key not in params:
                params[key] = val
        except Exception:
            # Ignore malformed lines
            continue
    return params


def _cleanup_wikilinks(text: str) -> str:
    """
    Simplify common wiki markups into plain text.

    Transformations:
    - [[Page|Label]] -> Label
    - [[Page]] -> Page
    - {{flag|...}}, {{abbr|...}} -> strip braces, keep obvious label part
    - Remove residual quotes and HTML tags
    - Normalize whitespace

    Args:
        text: A string potentially containing wiki markup.

    Returns:
        A cleaned string with simplified markup suitable for display or matching.
    """
    if not text:
        return text

    # Replace wiki links [[A|B]] / [[A]]
    text = re.sub(r"\[\[([^]|]+)\|([^]]+)]]", r"\2", text)
    text = re.sub(r"\[\[([^]]+)]]", r"\1", text)

    # Remove simple templates around a single value, keep inner content heuristically
    text = re.sub(r"\{\{\s*[^}|]+\|\s*([^}|]+)\s*}}", r"\1", text)

    # Remove remaining braces for uncommon templates
    text = re.sub(r"\{\{|}}", "", text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _derive_team_from_infobox(params: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Derive current team and player status from infobox parameters.

    Heuristics:
    - Team key candidates: 'team', 'current_team', 'organisation', 'org'.
    - Status key candidates: 'status', 'player_status', 'inactive', 'retired'.
    - If status indicates 'inactive' or 'retired', return (None, status).

    Args:
        params: Dictionary of infobox parameters (keys lowercased), as returned by _parse_infobox_params.

    Returns:
        (team or None, normalized_status or None)
    """
    # Status detection: pick the first present status-like key and normalize
    status_candidates = [
        "status",
        "player_status",
        "current_status",
        "activity",
        "inactive",
        "retired",
    ]
    raw_status = None
    for k in status_candidates:
        if k in params and params[k]:
            raw_status = params[k]
            break

    normalized_status = None
    if raw_status:
        s = _cleanup_wikilinks(raw_status).lower()
        if "retired" in s:
            normalized_status = "Retired"
        elif "inactive" in s:
            normalized_status = "Inactive"
        elif "active" in s:
            normalized_status = "Active"

    # Team extraction: choose the first meaningful team field
    team_candidates = [
        "team",
        "current_team",
        "organisation",
        "organization",
        "org",
        "team1",  # sometimes used
    ]
    raw_team = None
    for k in team_candidates:
        if k in params and params[k]:
            raw_team = params[k]
            break

    # Clean up common wiki markup for readability and consistency
    team = _cleanup_wikilinks(raw_team) if raw_team else None

    # Apply rule: if the player is inactive (or retired), do not return a current team
    if normalized_status in ("Inactive", "Retired"):
        team = None

    return team, normalized_status
