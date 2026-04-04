# Codex Execution Prompt — Auralite

Use this prompt when handing the Auralite project to Codex.

---

You are implementing **Auralite**, a city-scale living world simulation built on top of this repository.

Before making changes, read and treat the following file as the primary implementation source of truth:

- `docs/AURALITE_MASTER_BLUEPRINT.md`

Your job is to build toward that blueprint without losing sight of the long-term architecture.

## Critical mission
Auralite is **not** supposed to become:
- only a social-platform simulation,
- only a static city map,
- only an LLM chat sandbox,
- or only a dashboard.

Auralite is supposed to become:
- a **persistent city-scale world**,
- with **deeply simulated residents**,
- **households, districts, institutions, and events**,
- an **intervention sandbox**,
- and an **explainable report-driven simulation system**.

## Architectural rule
**The world is authoritative; agent cognition is contextual.**

This means:
- The world layer decides physical and structural truth.
- Institutions decide operational constraints.
- Households shape local burdens.
- Agents interpret and react through memory, belief, emotion, and relationships.

Do not collapse this separation.

## Repo adaptation rule
This repository already contains simulation, graph, and reporting structures. Reuse and evolve those where possible.

Specifically:
- Treat the existing MiroFish simulation/reporting/interview capabilities as a strong base for the **cognition + explainability** layer.
- Add the missing **world simulation** layer around it.
- Do not throw away the existing architecture unless absolutely necessary.
- Prefer incremental restructuring over destructive rewrites.

## Implementation style rules
1. Prefer **vertical slices** that move the project closer to the blueprint.
2. Keep code production-minded and organized.
3. Do not implement flashy UI disconnected from real sim state.
4. Do not add placeholder systems that contradict the blueprint.
5. Every meaningful implementation step should preserve the long-term path toward:
   - districts,
   - residents,
   - households,
   - institutions,
   - time,
   - movement,
   - pressure,
   - interventions,
   - history,
   - explainability.

## Immediate implementation target
Your first focus should be the earliest vertical slice of Auralite, corresponding to these roadmap areas from `docs/AURALITE_MASTER_BLUEPRINT.md`:
- Phase 1 — World shell
- Phase 2 — World state backbone
- Phase 3 — Population seeding
- partial Phase 4 — Basic life loop

## What to build first
Start by implementing the following in the cleanest practical way:

### First build batch
- Convert the uploaded city layout/front-end shell into the first Auralite city map experience.
- Define named districts and district config.
- Create the core world/state schema for:
  - world
  - city
  - district
  - building
  - person
  - household
- Create a seed population generator that assigns residents and households into districts.
- Add a simulation clock with time controls.
- Add visible agent markers and basic movement/routine behavior.
- Add a district inspector panel.
- Add a city HUD.

### Constraints for the first build batch
- The result must already feel like **one living city**, not just a UI mockup.
- Districts must be meaningful, not cosmetic.
- The code should leave room for households, institutions, interventions, and reports.
- Avoid overcommitting to exact real-world event ingestion at this stage.
- Use realistic but initially simplified systems when needed.

## How to work
For each major change:
1. Briefly state what part of the blueprint you are implementing.
2. Explain why this slice is the next correct step.
3. Implement the change.
4. Note what was intentionally left for later to avoid drift.

## Output expectations
When you respond with implementation work:
- show the files changed,
- keep the architecture aligned with `docs/AURALITE_MASTER_BLUEPRINT.md`,
- and explicitly mention any tradeoffs that were made for the current milestone.

## Guardrails
Do NOT:
- reduce Auralite to Twitter/Reddit agent simulation,
- build only cosmetic map UI,
- skip persistence/state modeling entirely,
- make every agent use expensive deep reasoning constantly,
- ignore households and districts,
- or drift into unrelated repo cleanup work unless it directly supports Auralite.

## Definition of success for the first milestone
A user should be able to open the app and see:
- a named district-based city,
- visible residents,
- a running city clock,
- basic movement/routine,
- district inspection,
- and the beginnings of a persistent Auralite world model.

When in doubt, follow the blueprint and preserve the long-term world simulation architecture.

---

If you are asked to continue after the first milestone, continue following the roadmap in `docs/AURALITE_MASTER_BLUEPRINT.md` in order, unless the user explicitly reprioritizes a different vertical slice.
