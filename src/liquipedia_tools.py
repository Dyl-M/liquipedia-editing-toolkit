# -*- coding: utf-8 -*-

import json
from typing import List, Dict, Any, Optional

"""File Information
@file_name: startgg_tools.py
@author: Dylan "dyl-m" Monfret
Collection of "Liquipedia tools" and useful functions
"""


def _normalize_flag(country: Optional[str]) -> str:
    """
    Normalise un code pays (par ex. 'BR') vers une chaîne acceptable pour Liquipedia.
    - None -> ""
    - str -> str inchangée (les données semblent déjà au format ISO alpha-2)
    """
    return country or ""


def _safe_str(value: Optional[str]) -> str:
    """
    Évite 'None' dans les champs texte.
    """
    return value or ""


def format_team_card_from_entry(entry: Dict[str, Any], remove_empty_optional: bool = False) -> str:
    """
    Formate une entrée d'équipe (structure JSON fournie) vers la template Liquipedia TeamCard.

    Règles:
    - |team| = nom d'équipe
    - |p1|, |p2|, |p3| = 3 premiers membres (titulaires)
    - |s4| = 4e membre si présent (remplaçant)
      - si remove_empty_optional=True et aucun remplaçant -> ligne omise
      - sinon -> ligne présente, éventuellement vide
    - |c| et |cflag| = coach, toujours vide par défaut
      - si remove_empty_optional=True -> ligne omise
      - sinon -> ligne présente (vide)

    :param entry: dict d'équipe
    :param remove_empty_optional: si True, supprime les lignes s4/c quand elles seraient vides
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
        f"|p1={tag(0)}|p1flag={flag(0).lower()}",
        f"|p2={tag(1)}|p2flag={flag(1).lower()}",
        f"|p3={tag(2)}|p3flag={flag(2).lower()}",
    ]

    # s4 (remplaçant)
    has_sub = bool(s4_tag or s4_flag)
    if has_sub or not remove_empty_optional:
        lines.append(f"|s4={s4_tag}|s4flag={s4_flag.lower()}")

    # c (coach) toujours vide côté données
    if not remove_empty_optional:
        lines.append(f"|c=|cflag=")

    lines.append("}}")
    return "\n".join(lines)


def _join_cards_with_boxes(cards: List[str]) -> str:
    """
    Construit un bloc box avec les TeamCards fournies.
    Début: {{box|start|padding=2em}}
    Séparateur: {{box|break|padding=2em}}
    Fin: {{box|end}}
    """
    start = "{{box|start|padding=2em}}"
    sep = "\n{{box|break|padding=2em}}\n"
    end = "{{box|end}}"

    if not cards:
        # Bloc vide, mais structure respectée
        return "\n".join([start, end])

    return "\n".join([start, sep.join(cards), end])


def generate_team_cards_from_json(json_path: str, include_box_wrappers: bool = True) -> str:
    """
    Charge un fichier JSON (liste d'équipes) et renvoie un bloc texte
    contenant les TeamCards Liquipedia pour chaque équipe.

    Mise en forme liste:
    - commence par: {{box|start|padding=2em}}
    - chaque équipe séparée par: {{box|break|padding=2em}}
    - se termine par: {{box|end}}

    - json_path: chemin vers le fichier JSON (ex: data/3v3-sam-champions-road-2025.json)
    - include_box_wrappers: pour inclure ou non les wrappers box.
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


def _build_tabs_header(segments: List[int]) -> str:
    """
    Construit l'en-tête Tabs dynamic, sans la fermeture finale '}}'.
    Exemple pour [12, 32, 48, 64]:
    {{Tabs dynamic
    |name1=Top 12
    |name2=Places 13-32
    |name3=Places 33-48
    |name4=Places 49-64
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
    - Segment i covers (prev_end+1) ... segments[i].
    - Entries beyond the last segment are ignored (strict behavior).
    NOTE: Preserve input order; do not sort the entries here.
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


def generate_team_cards_tabs_from_json(json_path: str, segments: List[int], remove_empty_optional: bool = False) -> str:
    """
    Génère un bloc complet avec onglets dynamiques + sections boxées par segments de classement.

    Structure :
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

    :param segments:
    :param json_path:
    :param remove_empty_optional: retire les lignes s4/c si elles seraient vides
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
