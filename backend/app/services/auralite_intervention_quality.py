from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterventionQualityLane:
    key: str
    purpose: str
    adds_beyond_previous: str
    evidence_focus: str
    operator_question: str


INTERVENTION_QUALITY_LANES: tuple[InterventionQualityLane, ...] = (
    InterventionQualityLane(
        key="adaptability",
        purpose="Assesses whether intervention gains hold when local conditions shift.",
        adds_beyond_previous="First resilience-oriented lane after robustness.",
        evidence_focus="cross-district response variance, rebound slope, fragile gains",
        operator_question="Will this still work if context changes?",
    ),
    InterventionQualityLane(
        key="sustainability",
        purpose="Assesses whether adaptation can be maintained over time without hidden decay.",
        adds_beyond_previous="Adds temporal endurance over one-off adaptation.",
        evidence_focus="durability trend, recovery debt, fade velocity",
        operator_question="Can this stay healthy over sustained operation?",
    ),
    InterventionQualityLane(
        key="repeatability",
        purpose="Assesses whether sustainability can be reproduced in similar settings.",
        adds_beyond_previous="Adds consistency across repeated runs.",
        evidence_focus="run-to-run variance, analog agreement, recurrence fit",
        operator_question="Can we reproduce this outcome reliably?",
    ),
    InterventionQualityLane(
        key="reliability",
        purpose="Assesses whether repeatable outcomes remain stable under realistic noise.",
        adds_beyond_previous="Adds fault tolerance beyond repeat success.",
        evidence_focus="volatility band, exception burden, fallback success",
        operator_question="Can we trust this under real volatility?",
    ),
    InterventionQualityLane(
        key="predictability",
        purpose="Assesses whether reliability is forecastable before deployment.",
        adds_beyond_previous="Adds pre-deployment forecast confidence.",
        evidence_focus="lead-lag match, confidence lane, uncertainty spread",
        operator_question="Can we anticipate likely outcomes before action?",
    ),
    InterventionQualityLane(
        key="dependability",
        purpose="Assesses whether predictability remains actionable with operational constraints.",
        adds_beyond_previous="Adds operational commitments and execution friction.",
        evidence_focus="execution drift, blocker persistence, support axis quality",
        operator_question="Can operators depend on this in production conditions?",
    ),
    InterventionQualityLane(
        key="assurability",
        purpose="Assesses whether dependence is supportable with bounded evidence obligations.",
        adds_beyond_previous="Adds assurance burden and caveat discipline.",
        evidence_focus="evidence completeness, caveat closure, unresolved pressure",
        operator_question="Can we responsibly assure this claim now?",
    ),
    InterventionQualityLane(
        key="certifiability",
        purpose="Assesses whether assurance quality reaches certifiable standards.",
        adds_beyond_previous="Adds explicit certification readiness checks.",
        evidence_focus="criteria coverage, contradiction count, blocker trigger quality",
        operator_question="Would this pass formal certification review?",
    ),
    InterventionQualityLane(
        key="accreditability",
        purpose="Assesses whether certification can be institutionally accredited.",
        adds_beyond_previous="Final lane: external accreditation readiness synthesis.",
        evidence_focus="cross-institution fit, governance friction, unresolved external blockers",
        operator_question="Is this accreditation-ready as a governed intervention practice?",
    ),
)

# Explicitly bounded: the ladder stops at accreditability.
INTERVENTION_QUALITY_TOP_LANE = "accreditability"

POSTURE_PREFIXES: tuple[str, ...] = (
    "strongly_",
    "for_now_",
    "not_yet_",
    "unresolved_",
    "blocked_",
    "weakly_",
)


def lane_state_key(lane_key: str) -> str:
    return f"review_intervention_{lane_key}_state"


def lane_evidence_key(lane_key: str) -> str:
    return f"operator_review_intervention_{lane_key}_evidence"


def lane_history_key(lane_key: str) -> str:
    return f"compact_historical_intervention_{lane_key}_lines"


def lane_takeaway_key(lane_key: str) -> str:
    return f"intervention_{lane_key}_takeaway"


def lane_snapshot_key(lane_key: str) -> str:
    return f"operator_intervention_{lane_key}_snapshot"


def intervention_quality_lane_keys() -> tuple[str, ...]:
    return tuple(lane.key for lane in INTERVENTION_QUALITY_LANES)


def intervention_quality_contract_keys(lane_key: str) -> dict[str, str]:
    return {
        "state": lane_state_key(lane_key),
        "evidence": lane_evidence_key(lane_key),
        "history": lane_history_key(lane_key),
        "snapshot": lane_snapshot_key(lane_key),
        "takeaway": lane_takeaway_key(lane_key),
    }


def is_normalized_posture_token(token: str | None) -> bool:
    if not token or not isinstance(token, str):
        return False
    return token.startswith(POSTURE_PREFIXES)


def find_non_normalized_postures(evidence: dict) -> list[str]:
    invalid: list[str] = []
    for key, value in (evidence or {}).items():
        if not isinstance(key, str) or not isinstance(value, str):
            continue
        if "posture" not in key and "qualifier" not in key:
            continue
        if "posture" in key:
            if not is_normalized_posture_token(value):
                invalid.append(key)
            continue
        if "qualifier" in key and value and "_" in value and not is_normalized_posture_token(value):
            invalid.append(key)
    return invalid
