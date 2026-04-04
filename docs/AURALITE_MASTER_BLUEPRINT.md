# Auralite Master Blueprint

## Purpose
Auralite is a city-scale living world simulation built on top of the MiroFish repository. The long-term goal is **not** to build a simple swarm demo, social feed simulator, or pure chat-agent sandbox. The goal is to build a **reality-faithful metropolis** populated by deeply simulated residents whose lives are shaped by place, institutions, scarcity, social ties, memory, belief, and interventions.

This document is the source-of-truth blueprint Codex must follow when implementing Auralite. If a local implementation choice conflicts with this document, this document wins unless explicitly superseded by a newer architecture note in the repository.

---

## North Star
Auralite v1 is a single massive hybrid metropolis designed to compress the essential structures of modern life into one continuous city. Deeply simulated residents live inside unequal structures of time, money, housing, information, health, mobility, and power. The world shapes the people and the people reshape the world.

### Core identity
- One giant city, not multiple disconnected maps.
- Reality-faithful, not reality-handcuffed.
- Fictional setting with realistic rules.
- MiroFish-style agent cognition is used as the **cognition layer**, not the entire world model.
- The sim must support interventions, branching, explainability, and history.

### Non-goals
- Do not reduce Auralite to a Twitter/Reddit-only simulation.
- Do not build only a static map viewer.
- Do not over-index on real-time news ingestion before the city itself is alive.
- Do not replace the world model with pure prompt-driven narrative roleplay.
- Do not let short-term implementation convenience break the long-term world architecture.

---

## High-Level Architecture
Auralite should be built as four connected layers:

1. **Presentation layer**
   - Interactive city map
   - District overlays
   - Agent/district/institution inspectors
   - Intervention console
   - Timeline/replay controls
   - Reports and explainability surfaces

2. **World orchestration layer**
   - World clock
   - District updates
   - Institution updates
   - Household updates
   - Event scheduling
   - Intervention application
   - Save/load orchestration

3. **Agent cognition layer**
   - Persona generation
   - Memory retrieval
   - Belief updates
   - Social reasoning
   - Interviews
   - Narrative interpretation
   - Explainable decision moments

4. **Persistence/history layer**
   - World state
   - Event logs
   - Agent memory
   - District history
   - Reports
   - Branching snapshots

### Core architectural rule
**The world is authoritative; agent cognition is contextual.**

That means:
- The city determines what is physically and structurally true.
- Institutions determine what is operationally possible.
- Households determine what is locally burdensome.
- Agents determine how they interpret and respond.

---

## Auralite v1 City Anatomy
Auralite v1 is one giant metro-region containing distinct but connected districts. These districts are not decorative. Each one must produce different constraints, opportunities, values, and social behavior.

### Districts
- **The Crown**: finance, politics, luxury, media, prestige
- **Glass Harbor**: startups, speculation, new wealth, innovation corridor
- **Old Meridian**: historic inner city, mixed-use culture, legacy communities
- **Southline**: industrial and logistics belt, labor realism, pollution, infrastructure
- **North Vale**: stabilizing suburb belt, schools, family life, routine pressure
- **Highgarden**: elite enclave, donor power, insulation, private influence
- **Ember District**: stressed transitional zone, precarious life, intense structural pressure
- **Ironwood Fringe**: outer edge where rural, suburban, and industrial life blur
- **Riverwake**: education, research, civic administration, nonprofits, ideology
- **Neon Market**: nightlife, vice, entertainment, rumor, fast money, hidden networks

### District design rules
- Every district must have a clear social and economic identity.
- Every district must have distinct pressures.
- Districts must interact through movement, housing pressure, institutions, and narratives.
- Changes in one district should be able to ripple into others.

---

## World Systems Blueprint
Auralite must model the systems below at city scale. These systems create pressure, tradeoffs, and unequal outcomes.

### Tier 1 systems (must be strong early)
- Time
- Population
- Households
- Economy
- Housing
- Movement/transport
- Institutions
- Media/information
- Intervention system

### Tier 2 systems (strong, but can start simpler)
- Policing and crime perception
- Health
- Education
- Religion/culture/values
- Environment/infrastructure

### Tier 3 systems (deepen later)
- Multigenerational life-course
- Electoral politics at high realism
- Intercity/global systems
- Full childhood development
- Deep national/international layers

### Time model
Use multi-resolution time:
- Micro: movement, conversations, incidents, immediate needs
- Daily: work, spending, household pressure, health drift, news digestion
- Weekly: wages, rent pressure, institution trends, district mood
- Monthly/seasonal: migration, business turnover, trust shifts, district evolution

### Core city pressures
These pressures must eventually shape behavior:
- Scarcity
- Uncertainty
- Status
- Belonging
- Power
- Trust
- Time
- Distance
- Health
- Memory

---

## Agent Model
Auralite agents are not generic NPCs. They are memory-bearing, socially embedded, materially constrained people.

### Agent layers
1. Base identity
2. Trait profile
3. Needs and drives
4. Dynamic physical/emotional/material state
5. Memory
6. Beliefs
7. Relationships
8. Habits/routines
9. Goals/priorities
10. Decision loop

### Key requirements
- Agents must differ meaningfully even under similar conditions.
- Agents must be constrained by money, time, household obligations, and place.
- Agents should use deep reasoning selectively, not constantly.
- Agents should support inspection and interview.
- Agents should be able to explain their behavior in a person-specific, memory-aware way.

### Decision loop
Each agent should approximately follow:
1. Perceive
2. Interpret
3. Prioritize
4. Choose action
5. Act
6. Encode outcome into memory / belief / relationship state

### Memory model
Memory must exist in layered forms:
- Immediate memory
- Episodic memory
- Social memory
- Place memory
- Narrative memory

Memory should not be perfect. It can fade, distort, simplify, and become emotionally colored.

### Belief model
Beliefs must be structured and change gradually based on:
- Trusted sources
- Personal experiences
- Social pressure
- Emotional fit
- Repeated exposure
- Identity defense

---

## Simulation Runtime Blueprint
Auralite should run as a layered, multi-timescale world.

### Runtime cycle
1. World tick
2. System tick
3. District tick
4. Household tick
5. Agent tick
6. Event tick
7. Archive tick

### Cognition frequency
Not every agent action should invoke expensive deep reasoning.

Use three levels:
- **Reactive**: routine behavior, low cost, frequent
- **Deliberative**: meaningful disruptions, medium cost, occasional
- **Reflective**: major life/worldview moments, high cost, rare

### Attention model
Agents should not perceive everything. Attention should be shaped by:
- Proximity
- Personal relevance
- Emotional salience
- Social source
- Routine disruption
- Fear/hope level
- Class/district exposure
- Media habits

### Spatial rule
Distance must matter. People should not experience Auralite as if they teleport.

---

## World Data Model
Auralite should persist a connected world of entities across these layers:

### World layer
- AuraliteWorld
- City
- GlobalState
- WorldEventLog

### Spatial layer
- District
- Subdistrict / BlockCluster
- Building
- TransitNode
- TransitEdge

### Human layer
- Person
- Household
- Relationship
- Group

### Institution layer
- Institution
- Business
- ServiceNode

### Runtime layer
- DistrictState
- MarketState
- ActiveEvent
- Intervention
- Narrative

### Cognition/history layer
- Memory
- Belief
- Goal
- AgentTrajectory
- DistrictHistory
- ReportArtifact

### Source-of-truth rule
Every meaningful change must either:
- modify a persistent entity,
- generate a persistent event,
- or update a persistent history trace.

If nothing durable changes, nothing meaningful happened.

---

## Technical Architecture
Auralite should evolve the current MiroFish repo rather than discard it.

### MiroFish responsibilities in Auralite
MiroFish-derived logic should become:
- Cognition service
- Memory/identity service
- Interview/introspection service
- Narrative/report service

### Auralite-added responsibilities
Auralite should add:
- World simulation engine
- Spatial city map system
- District and institution runtime
- Persistent city state
- Intervention sandbox

### Backend module targets
- `world`
- `population`
- `institutions`
- `simulation`
- `cognition`
- `reporting`
- `storage`

### Frontend surfaces
- City view
- District inspector
- Agent inspector
- Institution inspector
- Intervention console
- Timeline / replay
- Report pane

### Persistence strategy
Use a hybrid model:
- Structured relational state/history for durable entities and queryable logs
- Document/blob storage for heavy artifacts, memories, rich transcripts, and reports
- Snapshot support for branching experiments
- Optional graph layer for social/institution/narrative relationships

---

## Implementation Roadmap
This is the execution order Codex should follow.

### Phase 0 — Foundation lock-in
- Freeze blueprint and success criteria

### Phase 1 — World shell
- Convert uploaded layout into interactive district map
- Name districts
- Add camera, HUD, district inspector, day/night cycle

### Phase 2 — World state backbone
- Implement core world objects and persistence

### Phase 3 — Population seeding
- Generate residents, households, district allocation, traits, relationships

### Phase 4 — Basic life loop
- Daily routines, movement, work/home/leisure cycles, time controls

### Phase 5 — Core city pressures
- Employment, wages, rent, spending, transport burden, household stress

### Phase 6 — Social depth and cognition integration
- Memory, beliefs, interviews, explainable decisions, relationship drift

### Phase 7 — Institution engine
- Employers, hospitals, schools, police, transit, government, media, utilities

### Phase 8 — Event and intervention console
- Policy changes, shocks, district events, branching runs

### Phase 9 — Reporting and explainability
- Run summaries, causal chains, comparisons, key-agent and key-narrative reports

### Phase 10 — City evolution and long-run history
- Migration, district evolution, business turnover, trust shifts, long-run change

---

## True MVP Definition
The smallest version that still feels like Auralite should include:
- World shell
- World state backbone
- Population seeding
- Basic life loop
- Core city pressures
- Partial cognition integration
- Partial intervention console
- Partial explainability/reporting

That MVP should already let a user:
- Open a living city
- Inspect districts and people
- Watch daily life
- See inequality and pressure
- Inject a change
- Observe reactions
- Get a meaningful summary of what happened

---

## Implementation Guardrails for Codex
These rules exist to keep implementation aligned.

1. Do not collapse Auralite into a social-platform simulator.
2. Do not replace systems with pure prompt theater.
3. Do not optimize for breadth before depth.
4. Do not add flashy UI detached from real state.
5. Do not make every agent use expensive cognition every tick.
6. Do not treat districts as cosmetic.
7. Do not treat institutions as static background props.
8. Do not skip persistence and history just to demo movement.
9. Prefer buildable vertical slices over giant theoretical rewrites.
10. Keep the long-term world model intact even when implementing an MVP slice.

---

## Immediate Build Priority
If starting implementation now, the first three build batches should be:

### Build batch 1
- Convert uploaded layout into Auralite district map
- Define district data config
- Define core world schema
- Define person and household schema
- Create seed population generator
- Add sim clock and time controls
- Add agent markers and basic movement
- Add district inspector panel
- Add city HUD

### Build batch 2
- Add work/home/leisure loop
- Add jobs/rent/spending pressure
- Add household stress
- Add district state updates
- Add save/load run state

### Build batch 3
- Integrate cognition/memory layer
- Agent inspection
- Interviews
- Simple intervention injection
- Run summary output

---

## Final Principle
Auralite should become a world that can be watched, perturbed, inspected, and explained.

If an implementation choice makes Auralite look busier but less truthful, reject it.
If an implementation choice makes Auralite simpler now but preserves the long-term city/world model, prefer it.

This blueprint is the implementation anchor.
