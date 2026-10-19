import json
from pathlib import Path
from .models import CharacterState


def save_state(state: CharacterState, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def load_state(path: str | Path) -> CharacterState:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("State file must contain a JSON object.")
    return CharacterState.from_dict(data)
