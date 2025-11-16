# -*- coding: utf-8 -*-

import json
import re
import requests
import time

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
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

    def _tag(i: int) -> str:
        return _safe_str(starters[i].get("player_tag")) if i < len(starters) else ""

    def _flag(i: int) -> str:
        return _normalize_flag(starters[i].get("player_country")) if i < len(starters) else ""

    s4_tag = _safe_str(subs[0].get("player_tag")) if len(subs) >= 1 else ""
    s4_flag = _normalize_flag(subs[0].get("player_country")) if len(subs) >= 1 else ""

    lines = [
        "{{TeamCard",
        f"|team={team_name}",
        f"|p1={_tag(0)}|p1flag={_flag(0)}",
        f"|p2={_tag(1)}|p2flag={_flag(1)}",
        f"|p3={_tag(2)}|p3flag={_flag(2)}",
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
        json_path: Path to the input JSON file (e.g., _data/3v3-sam-champions-road-2025.json).
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


def get_true_player_name(player_name_input: str, user_agent: Optional[str] = None) -> None | str:
    """
    Given a Rocket League player name (query), returns the page title chosen by Liquipedia editors (top-of-page title).

    This version minimizes API calls by doing a single GET on "https://liquipedia.net/rocketleague/<player_name>" to
    both check existence and fetch HTML.

    Args:
        player_name_input: User-provided player name or handle.
        user_agent: Optional custom User-Agent; if omitted, a default is used.

    Returns:
        String: canonical_name (str|None)
    """
    ua = user_agent or DEFAULT_USER_AGENT

    # 1) Requête unique: existence + HTML rendu via l'URL canonique /rocketleague/<player_name>
    title_guess = player_name_input.replace(" ", "_")
    url = f"https://liquipedia.net/rocketleague/{title_guess}"
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en",
            },
            timeout=15,
            allow_redirects=True,
        )
    except requests.RequestException as e:
        raise LiquipediaAPIError(f"Erreur réseau Liquipedia: {e}") from e

    # 2) Vérifier existence
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise LiquipediaAPIError(f"Réponse HTTP inattendue {resp.status_code} pour {resp.url}")

    # 3) Extraire le titre réel de la page depuis le HTML
    canonical_name = _extract_page_title_from_html(resp.text)
    if not canonical_name:
        return None

    return canonical_name


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


def _extract_page_title_from_html(html: str) -> Optional[str]:
    """
    Extrait le titre canonique affiché en haut de page:
    - Priorité: h1#firstHeading (titre MediaWiki).
    - Fallback: meta property="og:title".
    - Fallback: balise <title> (en retirant les suffixes du site).

    Retourne None si non trouvable.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1) Titre principal MediaWiki
    h1 = soup.select_one("#firstHeading, h1.firstHeading")
    if h1:
        text = h1.get_text(strip=True)
        if text:
            return text

    # 2) Open Graph title
    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        return og.get("content").strip() or None

    # 3) Balise <title> (retirer suffixes connus)
    title_tag = soup.find("title")
    if title_tag and title_tag.text:
        raw = title_tag.text.strip()
        # Souvent: "<PageTitle> - Liquipedia Rocket League Wiki"
        cleaned = re.sub(r"\s*-\s*Liquipedia.*$", "", raw).strip()
        return cleaned or raw

    return None


if __name__ == "__main__":
    test = get_true_player_name(player_name_input='sadness', user_agent=DEFAULT_USER_AGENT)

    print(test)
