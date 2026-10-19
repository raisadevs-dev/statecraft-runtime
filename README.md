# TIGRESS Behaviour Engine v0.1

A small, runnable Python prototype that turns the TIGRESS character board into explicit, testable behaviour.

## What this is
- A deterministic character-state model.
- A context-aware rule engine for advice, boundaries, mistakes, repeated harm, and accountability.
- A small persistent JSON save file.
- A demo and unit tests.

## What this is not
This is not a sentient character or a clinical model of emotion. State values are simulation variables, not measurements of real feelings. The prototype does not infer someone's intent with certainty: callers provide an event category and context. Ambiguous events should use `UNCLEAR` and trigger a clarifying response.

## Requirements
- Python 3.10+
- No third-party packages

## Run
From this folder:

```bash
python demo.py
python -m unittest discover -s tests -v
```

To save state to a JSON file:

```bash
python demo.py --save data/tigress_state.json
```

## Architecture
- `tigress/models.py`: state, event, and decision data structures.
- `tigress/engine.py`: decision policy and cautious state updates.
- `tigress/storage.py`: JSON persistence.
- `demo.py`: runnable scenarios.
- `tests/test_engine.py`: regression tests.

## Behaviour loop
`EVENT → CONTEXT CHECK → DECISION → DIALOGUE → STATE UPDATE → OPTIONAL SAVE`

The engine does not let one event permanently define a person. Repeated patterns affect trust more than isolated mistakes. An apology alone does not reset trust; changed behaviour over time is represented by separate events.

## Example event categories
`SUPPORTIVE_ADVICE`, `REASONABLE_REQUEST`, `UNJUSTIFIED_RESTRICTION`, `DISRESPECT`, `HONEST_MISTAKE`, `REPEATED_HARM`, `GENUINE_APOLOGY`, `ACCOUNTABILITY_WITH_CHANGE`, `BOUNDARY_RESPECTED`, `UNCLEAR`.

## Next steps
1. Add a language-model adapter to extract structured event signals from free text.
2. Keep extraction separate from policy decisions.
3. Require uncertainty handling and allow the user to correct event interpretation.
4. Add an interaction UI only after tests cover the desired behaviour.
