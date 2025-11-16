# Prizepool Filler - Implementation Plan

## Overview

This module automatically fills Liquipedia prize pool wikitext with tournament results from start.gg.

**Input:** Liquipedia wikitext with placeholder slots + start.gg event slug
**Output:** Updated wikitext with filled opponent data

---

## Implementation Roadmap

### 1. Get team results from start.gg

#### 1.1 - Understand the number of teams to fill in wikitext

**Goal:** Parse wikitext first to know how many teams we need before fetching from API

**Tasks:**

- [ ] Implement `parse_placement_range(place_str: str) -> tuple[int, int]`
    - Parse "1" → (1, 1)
    - Parse "65-72" → (65, 72)
    - Add validation for invalid formats

- [ ] Implement `extract_prizepool_slots(wikitext: str) -> list[dict]`
    - Use regex to find all `{{Slot|place=X-Y|...}}` blocks
    - Extract opponent count per slot
    - Return structured data:
      ```
      {
          "place_str": "65-72",
          "place_start": 65,
          "place_end": 72,
          "opponent_slots": [...]  # List of opponent entries
      }
      ```

- [ ] Implement `calculate_required_teams(slots: list[dict]) -> int`
    - Determine max placement needed
    - Return the `top_n` value for API fetch

**Technical notes:**

- Parse wikitext pattern: `|{{Slot|place=([^|}]+)...}}`
- Count opponent entries: `|{{Opponent|...}}`
- Handle edge case: slots without opponents (header rows, etc.)

---

#### 1.2 - Find a workaround if results can't be found because the tournament is ongoing

**Goal:** Handle tournaments that haven't finished yet, where full standings aren't available

**Tasks:**

- [ ] Detect when event standings are incomplete
    - Check if API returns fewer teams than needed
    - Check event state/status if available in API

- [ ] Implement fallback to phase-level results
    - Query specific completed phases (e.g., "Day 1", "Day 2")
    - Handle phase states (COMPLETED vs IN_PROGRESS)

- [ ] Implement `get_phase_results(event_slug, phase_name_filter) -> list[dict]`
    - Query all phases in event
    - Filter by completion state
    - Extract standings from phase groups

**Technical notes:**

- Phase states: typically 3 or "COMPLETED"
- Phase groups may have different sizes
- Need to handle partial results gracefully

---

#### 1.3 - Understand tournament structure (Phases and groups per phase)

**Goal:** Parse complex tournament structures with multiple phases and groups

**Tasks:**

- [ ] Implement `get_tournament_structure(event_slug) -> dict`
    - Retrieve all phases with their names and states
    - Get phase groups within each phase
    - Return structured hierarchy

- [ ] Handle group ordering for placement calculation
    - Groups may be ordered (B1, B2, B3...) or parallel
    - Determine if groups are sequential (cumulative placement) or independent

- [ ] Implement cumulative placement calculation
    - When groups are sequential:
        - B1 teams get placements 1-N
        - B2 teams get placements N+1 to N+M
        - etc.

**Technical notes:**

- Phase groups have `displayIdentifier` (e.g., "B1", "B2")
- Sort groups alphabetically for consistent ordering
- Consider asking user for placement strategy if ambiguous

**Data structure example:**

```json
{
  "Phase 1": {
    "state": "COMPLETED",
    "groups": [
      "A1",
      "A2"
    ]
  },
  "Phase 2": {
    "state": "IN_PROGRESS",
    "groups": [
      "B1",
      "B2",
      "B3"
    ]
  }
}
```

---

#### 1.4 - Extract teams' placement

**Goal:** Get final team placements from start.gg, handling different sources

**Tasks:**

- [ ] Leverage existing `startgg_tools.get_event_top_teams(event_slug, top_n)`
    - Primary method for completed events
    - Returns: placement, team_name, elimination_set_id

- [ ] Implement `get_teams_from_phases(event_slug, phase_names) -> list[dict]`
    - Fallback for ongoing tournaments
    - Combine results from multiple phases
    - Calculate placements based on group order

- [ ] Implement `get_elimination_details(set_id: int) -> dict`
    - Use existing `startgg_tools.get_set_details(set_id)`
    - Extract: opponent_name, winner_score, loser_score
    - Handle missing data gracefully

- [ ] Add rate limiting
    - Delay between API calls (1-2 seconds)
    - Respect start.gg rate limits

**Team data structure:**

```
{
    "placement": 65,
    "team_name": "Team XYZ",
    "elimination_set_id": 12345,
    "eliminated_by": "Team ABC",
    "score": "1-3"  # From loser's perspective
}
```

---

### 2. Fill the wikitext

#### 2.1 - Respect possible placement then group order

**Goal:** Correctly map teams to slots, respecting both placement and group ordering

**Tasks:**

- [ ] Implement `match_teams_to_slots(slots, teams) -> dict`
    - Map placement ranges to team lists
    - Handle ties (multiple teams same placement)
    - Validate slot capacity

- [ ] Handle group-based ordering
    - When using phase results, maintain group order
    - Ensure B1 teams → slots 1-N, B2 teams → slots N+1-M, etc.

- [ ] Implement `format_opponent_entry(team: dict) -> str`
    - Generate: `{{Opponent|TeamName|lastvs=OpponentName|lastvsscore=1-3}}`
    - Handle missing elimination data → empty lastvs/lastvsscore
    - Preserve TBD format when no team available

- [ ] Implement `fill_prizepool_wikitext(wikitext, teams) -> str`
    - Replace TBD opponents with formatted entries
    - Process slots in reverse order (avoid string index issues)
    - Pad with TBD if fewer teams than slots

**Technical notes:**

- Use string replacement (not regex substitution to avoid escaping issues)
- Validate each replacement succeeded
- Log warnings for mismatches

---

#### 2.2 - Handle lose per forfeit

**Goal:** Properly format scores when teams forfeit

**Tasks:**

- [ ] Implement `format_score(team_score: int, opponent_score: int) -> str`
    - Normal: `"1-3"` (team lost 1-3)
    - Team forfeited: `"FF-W"` (team_score == -1)
    - Opponent forfeited: `"W-FF"` (opponent_score == -1)

- [ ] Detect forfeit in set details
    - start.gg uses -1 for forfeit scores
    - Handle both sides forfeiting (edge case)

**Score format examples:**

```python
format_score(1, 3)  # "1-3" (normal loss)
format_score(-1, 0)  # "FF-W" (team forfeited)
format_score(0, -1)  # "W-FF" (opponent forfeited)
```

---

## Main Workflow Function

```python
def process_prizepool_from_event(
        event_slug: str,
        wikitext_path: str,
        output_path: str,
        phase_name: str = None,
        phase_group_name: str = None
) -> None:
    """
    Complete workflow to fill prizepool wikitext.

    Steps:
    1. Read and parse wikitext
    2. Determine how many teams needed
    3. Fetch teams from start.gg (event or phase)
    4. Get elimination details for each team
    5. Match teams to slots
    6. Generate updated wikitext
    7. Save output
    """
```

---

## Testing Strategy

### Unit Tests

- [ ] Test placement parsing (single, ranges, invalid)
- [ ] Test slot extraction from wikitext
- [ ] Test score formatting (normal, forfeits)
- [ ] Test team-to-slot matching

### Integration Tests

- [ ] Test with sample wikitext files
- [ ] Test with mock start.gg responses
- [ ] Test edge cases (ties, missing data, ongoing tournaments)

### Manual Testing

- [ ] Test with real completed tournament
- [ ] Test with real ongoing tournament (phase results)
- [ ] Validate output in Liquipedia format

---

## Edge Cases & Error Handling

- **Tied placements:** Multiple teams at same placement number
- **Forfeit scores:** -1 in API response
- **Missing elimination data:** Team not eliminated / data unavailable
- **Slot count mismatch:** More/fewer teams than expected
- **Ongoing tournaments:** Event standings incomplete
- **Phase ordering:** Ambiguous group ordering (may need user input)
- **API rate limits:** Add delays, handle 429 errors
- **Network errors:** Retry logic, clear error messages

---

## Dependencies

- `tournament_page_filler.startgg_tools` - Existing start.gg API tools
- `re` - Regex for wikitext parsing
- `time` - Rate limiting delays
- `typing` - Type hints for clarity

---

## Next Steps

1. ✅ Clean up existing code
2. ✅ Create implementation roadmap
3. **Start with 1.1:** Parse wikitext to understand team requirements
4. Implement each section incrementally with tests
5. Validate with real tournament data