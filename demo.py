import argparse
from tigress.engine import TigressEngine
from tigress.models import CharacterState, Event, EventType
from tigress.storage import save_state, load_state


def show(engine: TigressEngine, event_type: EventType, description: str, strength: float = 0.8):
    decision = engine.respond(Event(event_type, description, evidence_strength=strength))
    print(f"\nEVENT: {event_type.value} | {description}")
    print(f"ACTION: {decision.action}")
    print(f"TIGRESS: {decision.dialogue}")
    print(f"WHY: {decision.explanation}")
    print("STATE:", {k: round(v, 2) if isinstance(v, float) else v
                     for k, v in decision.state_after.items()})


def main():
    parser = argparse.ArgumentParser(description="Run TIGRESS Behaviour Engine demo.")
    parser.add_argument("--save", help="Optional JSON path for persistent character state.")
    args = parser.parse_args()

    state = load_state(args.save) if args.save else CharacterState()
    engine = TigressEngine(state)

    show(engine, EventType.SUPPORTIVE_ADVICE, "A friend offers practical advice.")
    show(engine, EventType.UNJUSTIFIED_RESTRICTION,
         "Partner demands she stop speaking to a friend.")
    show(engine, EventType.REPEATED_HARM,
         "The same boundary is ignored repeatedly.")
    show(engine, EventType.GENUINE_APOLOGY,
         "Partner apologises.")
    show(engine, EventType.ACCOUNTABILITY_WITH_CHANGE,
         "Partner consistently respects the boundary over time.")

    if args.save:
        save_state(engine.state, args.save)
        print(f"\nSaved state to: {args.save}")


if __name__ == "__main__":
    main()
