from dataclasses import dataclass
from .models import CharacterState, Event, EventType


@dataclass
class Decision:
    action: str
    dialogue: str
    explanation: str
    state_before: dict
    state_after: dict


class TigressEngine:
    """Rule-based prototype. It does not infer intent from raw text."""

    def __init__(self, state: CharacterState | None = None):
        self.state = state or CharacterState()

    def respond(self, event: Event) -> Decision:
        before = self.state.to_dict()
        kind = event.event_type

        # Ambiguous or low-context events are not treated as proven harm.
        if kind == EventType.UNCLEAR or not event.context_known:
            action = "ASK_FOR_CONTEXT"
            dialogue = "Mujhe poora context samajhna hai. Tum exactly kya kehna chahte ho, aur is request ki wajah kya hai?"
            explanation = "Insufficient context; no strong state update is justified."
        elif kind == EventType.SUPPORTIVE_ADVICE:
            action = "LISTEN_AND_EVALUATE"
            dialogue = "Main tumhari baat sunungi aur dekhungi ki yeh mere liye sahi hai ya nahi."
            explanation = "Advice is considered without surrendering independent judgment."
            self._small_update("openness", +0.01 * event.evidence_strength)
        elif kind == EventType.REASONABLE_REQUEST:
            action = "CONSIDER_AND_DECIDE"
            dialogue = "Main tumhari baat consider karungi. Phir hum dono ke liye practical solution dekhenge."
            explanation = "A reasonable request can be considered without automatic agreement."
        elif kind == EventType.UNJUSTIFIED_RESTRICTION:
            action = "CHALLENGE_AND_SET_BOUNDARY"
            dialogue = "Tumhari feelings sun sakti hoon, lekin meri choices par unilateral control acceptable nahi hai. Genuine concern hai toh discuss karte hain."
            explanation = "A restriction is challenged while leaving room for context and discussion."
            self._harm_update(event, severe=False)
        elif kind == EventType.DISRESPECT:
            action = "NAME_THE_BEHAVIOUR_AND_SET_BOUNDARY"
            dialogue = "Is tarah baat karna theek nahi hai. Hum disagreement kar sakte hain, lekin respect ke saath."
            explanation = "Disrespect calls for a clear boundary; response strength follows evidence."
            self._harm_update(event, severe=False)
        elif kind == EventType.HONEST_MISTAKE:
            action = "DISCUSS_AND_EVALUATE"
            dialogue = "Galti ho sakti hai. Pehle samajhte hain kya hua, phir dekhte hain ise kaise theek karna hai."
            explanation = "An isolated mistake is not automatically treated as a harmful pattern."
            self._small_update("hurt", -0.02 * event.evidence_strength)
        elif kind == EventType.REPEATED_HARM:
            action = "PROTECT_BOUNDARIES_AND_REASSESS_TRUST"
            dialogue = "Yeh baar-baar ho raha hai. Sirf explanation kaafi nahi; mujhe consistent change dekhna hoga. Filhaal main apni boundary maintain karungi."
            explanation = "Repeated harm has a larger effect than an isolated incident."
            self.state.harmful_pattern_count += 1
            self._harm_update(event, severe=True)
        elif kind == EventType.GENUINE_APOLOGY:
            action = "ACKNOWLEDGE_AND_OBSERVE"
            dialogue = "Apology sun li. Trust wapas aane mein waqt lagega; aage ka behaviour bhi matter karega."
            explanation = "An apology is acknowledged but does not automatically restore trust."
            self._small_update("defensiveness", -0.02 * event.evidence_strength)
        elif kind == EventType.ACCOUNTABILITY_WITH_CHANGE:
            action = "RECOGNISE_CHANGE_AND_REBUILD_GRADUALLY"
            dialogue = "Main tumhari responsibility lene aur behaviour badalne ki effort notice kar rahi hoon. Trust dheere-dheere rebuild ho sakta hai."
            explanation = "Observed accountability and changed behaviour can gradually rebuild trust."
            self.state.accountable_change_count += 1
            strength = event.evidence_strength
            self._small_update("trust", +0.08 * strength)
            self._small_update("emotional_safety", +0.07 * strength)
            self._small_update("hurt", -0.06 * strength)
            self._small_update("defensiveness", -0.05 * strength)
        elif kind == EventType.BOUNDARY_RESPECTED:
            action = "ACKNOWLEDGE_RESPECT"
            dialogue = "Thank you meri boundary respect karne ke liye. Isse baat karna aur trust build karna easier hota hai."
            explanation = "Respectful behaviour supports safety and trust over time."
            strength = event.evidence_strength
            self._small_update("trust", +0.04 * strength)
            self._small_update("emotional_safety", +0.05 * strength)
            self._small_update("defensiveness", -0.03 * strength)
        else:
            action = "ASK_FOR_CONTEXT"
            dialogue = "Main pehle context samajhna chahti hoon."
            explanation = "Fallback for unsupported event type."

        self.state.interaction_count += 1
        self.state.clamp()
        return Decision(action, dialogue, explanation, before, self.state.to_dict())

    def _harm_update(self, event: Event, severe: bool) -> None:
        # Evidence strength controls update size; no variable can exceed [0, 1].
        scale = event.evidence_strength
        trust_drop = (0.10 if severe else 0.05) * scale
        safety_drop = (0.12 if severe else 0.06) * scale
        hurt_rise = (0.12 if severe else 0.06) * scale
        defense_rise = (0.08 if severe else 0.04) * scale
        self._small_update("trust", -trust_drop)
        self._small_update("emotional_safety", -safety_drop)
        self._small_update("hurt", +hurt_rise)
        self._small_update("defensiveness", +defense_rise)

    def _small_update(self, name: str, delta: float) -> None:
        setattr(self.state, name, getattr(self.state, name) + delta)
