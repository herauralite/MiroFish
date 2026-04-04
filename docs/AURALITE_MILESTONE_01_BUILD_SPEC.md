# Auralite Milestone 01 Build Spec

## Purpose
This file defines the **first concrete implementation milestone** for Auralite.

It exists to prevent drift and to give Codex a precise, practical target that is directly aligned with:
- `docs/AURALITE_MASTER_BLUEPRINT.md`
- `docs/CODEX_AURALITE_EXECUTION_PROMPT.md`

This milestone is intentionally narrow. It should produce the **first believable Auralite vertical slice** rather than attempting to implement the entire long-term simulation architecture at once.

---

## Milestone 01 name
**World Shell + State Backbone + Seeded City Life**

---

## Milestone 01 objective
Build the first working Auralite slice where a user can open the app and experience:
- a named district-based city,
- a running city clock,
- visible residents,
- basic daily movement/routine,
- district inspection,
- and a persistent world model that can support deeper future systems.

This is not the full Auralite simulation yet.
It is the first real, coherent, stateful version of the world.

---

## Scope included in Milestone 01

### Frontend
- Auralite city map view using the existing uploaded layout as the initial visual shell
- Named district overlays
- District click/selection
- City HUD
- Sim time controls
- Visible resident markers
- Basic agent movement rendering
- District inspector side panel
- Basic agent tooltip or lightweight inspection panel

### Backend
- World state root
- City state
- District state/config
- Building/location seed data
- Person schema
- Household schema
- Seed population generator
- Basic runtime clock
- Basic daily routine scheduler
- Persistence for save/load of the world state
- API endpoints needed to drive the first frontend slice

### Simulation logic
- Time advances
- Residents exist in districts
- Residents have homes and simple daily routines
- Residents move between simple destinations such as home/work/leisure anchors
- District activity changes as a function of time and resident presence

---

## Explicitly out of scope for Milestone 01
These should **not** be treated as required for this milestone:
- deep reflective cognition everywhere
- full memory graph implementation
- full belief system
- intervention branching
- detailed institutions with full load logic
- full reporting system for Auralite-specific runs
- detailed economy simulation
- realistic traffic simulation
- realistic crime/policing model
- real-world event ingestion
- multigenerational simulation

Small hooks for future support are good. Full implementation is not required yet.

---

## User-visible success criteria
Milestone 01 is complete when a user can:
1. Open the app and clearly see Auralite as one city with distinct named districts.
2. See a running city clock and basic time controls.
3. Click a district and inspect its identity and summary state.
4. See resident markers moving or changing location according to basic routine logic.
5. Inspect at least basic information about a resident.
6. Restart/reload the app without losing the core seeded world state unexpectedly.

If these six things do not work, Milestone 01 is not done.

---

## Architectural intent of Milestone 01
Milestone 01 must preserve the long-term architecture.

### Required architecture principles
- The map must connect to real world state, not static hardcoded visuals only.
- Districts must exist as real data objects, not only UI labels.
- Residents must exist as real stateful entities, not only decorative sprites.
- Households must exist as first-class entities even if their behavior is still simple.
- The simulation clock must exist as real backend state.
- The code must leave room for institutions, interventions, memory, reports, and history.

### Forbidden shortcuts
- Do not hardcode everything only in the frontend.
- Do not implement residents as anonymous visual particles.
- Do not make districts purely cosmetic.
- Do not bypass persistence entirely.
- Do not model movement in a way that makes future world-state authority impossible.

---

## Recommended repository additions
Codex may adapt these names if necessary, but the structure should stay close to this intent.

### Backend target modules
Potential new or expanded modules:
- `backend/app/services/auralite_world_service.py`
- `backend/app/services/auralite_seed_service.py`
- `backend/app/services/auralite_runtime_service.py`
- `backend/app/models/auralite_world.py`
- `backend/app/models/auralite_city.py`
- `backend/app/models/auralite_district.py`
- `backend/app/models/auralite_person.py`
- `backend/app/models/auralite_household.py`
- `backend/app/api/auralite.py`

### Frontend target areas
Potential new or expanded files:
- city map page/view
- district config and labels
- HUD/time controls component
- district inspector component
- agent markers layer
- state hooks/store for world data and sim updates

Codex should fit these into the existing repo structure in the least disruptive way.

---

## Minimum backend data model for Milestone 01
The following objects must exist in some durable structured form.

### 1. AuraliteWorld
Fields should include at least:
- `world_id`
- `city_id`
- `current_time`
- `time_speed`
- `is_running`
- `created_at`
- `updated_at`

### 2. City
Fields should include at least:
- `city_id`
- `name`
- `district_ids`
- `population_count`
- `world_metrics` (basic placeholder allowed)

### 3. District
Fields should include at least:
- `district_id`
- `name`
- `archetype`
- `summary`
- `map_region_key`
- `population_count`
- `housing_profile`
- `activity_profile`
- `current_activity_level`

The initial district list should be seeded from the Auralite blueprint:
- The Crown
- Glass Harbor
- Old Meridian
- Southline
- North Vale
- Highgarden
- Ember District
- Ironwood Fringe
- Riverwake
- Neon Market

### 4. Building / Location anchor
Milestone 01 can simplify buildings into anchor locations.
Each district should have enough anchors to support routine behavior.
Fields should include at least:
- `location_id`
- `district_id`
- `name`
- `type`
- `capacity`
- `x`
- `y`

Suggested initial types:
- home
- work
- leisure
- service
- transit

### 5. Person
Fields should include at least:
- `person_id`
- `name`
- `age`
- `district_id`
- `household_id`
- `occupation`
- `home_location_id`
- `work_location_id` (nullable)
- `current_location_id`
- `current_activity`
- `routine_type`
- `state_summary` (lightweight)

### 6. Household
Fields should include at least:
- `household_id`
- `district_id`
- `home_location_id`
- `member_ids`
- `household_type`

---

## Seed generation requirements
Milestone 01 must include deterministic or semi-deterministic seeding.

### Seed generation should create
- the city
- all districts
- enough location anchors per district
- a starting resident population
- households
- home assignments
- work/leisure assignments where relevant

### Population density guidance
Milestone 01 does **not** need the full long-term target population.
Use a practical demo population that is large enough to feel alive but small enough to stay manageable.

Suggested starting range:
- **150 to 500 residents**

### Household rules
- Every resident must belong to a household
- Household types should vary
- Districts should produce different household mixes

### District differentiation rules
Population seeding should reflect district identity.
Examples:
- Highgarden should skew wealthy / elite / low density
- Southline should skew labor / industrial workforce
- North Vale should skew family households
- Ember District should skew precarious households
- Glass Harbor should skew younger professionals / startup workers

---

## Runtime requirements for Milestone 01
The runtime should be simple but real.

### Required runtime behavior
- World clock advances
- Time-of-day state is exposed to the frontend
- Residents change activities based on time blocks
- Residents move between anchor locations according to routine rules
- District activity levels update based on occupancy/time

### Suggested routine categories
Simple categories are enough for Milestone 01:
- office_worker
- shift_worker
- student_like
- family_homebody
- nightlife_worker
- retiree
- unemployed_or_flexible

### Suggested daily states
- sleeping
- commuting
- working
- at_home
- leisure
- idle

### Runtime simplification rule
Use coarse but believable time-block logic rather than premature deep AI reasoning.
This is acceptable for Milestone 01 as long as the system is structured to deepen later.

---

## Persistence requirements
Milestone 01 must support persistence.

### Minimum persistence capabilities
- save seeded world state
- reload the same world state
- preserve current time and active world data
- preserve residents and households

### Acceptable initial persistence options
Codex may choose a pragmatic initial storage method such as:
- JSON-backed persistence
- SQLite-backed persistence
- or a hybrid

The key requirement is that the world state is authoritative and reloadable.

---

## Frontend requirements in detail

### 1. City map shell
- Must visually use the uploaded city layout or a direct adaptation of it
- Must support district identification and selection
- Must display visible resident presence in some form

### 2. City HUD
Should display at least:
- city name: Auralite
- current simulated time
- current day phase (morning/day/evening/night acceptable)
- total resident count
- current sim state (running/paused)

### 3. Time controls
Should support at least:
- play
- pause
- speed toggle(s)

### 4. District inspector
On district selection, show at least:
- district name
- district archetype
- short description/identity summary
- current population count
- current activity level

### 5. Resident visualization
- Residents must be visible as moving or updating markers
- The system should not feel static
- Full pathfinding is not required yet, but movement should be understandable

### 6. Resident inspection
At minimum, clicking or hovering a resident should reveal:
- name
- district
- occupation
- current activity
- household reference or lightweight household summary

---

## Minimum API surface for Milestone 01
Codex may adapt paths, but the functionality should exist.

### Suggested endpoints
- `GET /api/auralite/world`
- `POST /api/auralite/world/init`
- `POST /api/auralite/world/start`
- `POST /api/auralite/world/pause`
- `POST /api/auralite/world/tick`
- `GET /api/auralite/districts`
- `GET /api/auralite/district/<district_id>`
- `GET /api/auralite/residents`
- `GET /api/auralite/resident/<person_id>`
- `POST /api/auralite/world/save`
- `POST /api/auralite/world/load`

### Minimum response responsibilities
The frontend must be able to fetch:
- global world state
- district list and details
- resident list with enough data for rendering
- current time
- sim status

---

## Done criteria for Codex
Codex should consider Milestone 01 complete only when all of the following are true:

1. The app contains a recognizable Auralite city shell.
2. Districts are named and inspectable.
3. A seeded population exists in backend state.
4. Households exist in backend state.
5. The sim clock runs.
6. Residents visibly change location/activity over time.
7. The frontend reflects live backend state, not static demo-only data.
8. The world can be saved and reloaded.
9. The code is structured to support later phases rather than painted into a corner.

---

## What Milestone 01 should prepare for next
Milestone 01 should make Phase 2 easier, not harder.

It should leave clean extension points for:
- richer household pressure
- jobs/rent/spending systems
- district state evolution
- institution logic
- memory and beliefs
- interventions
- reporting

If an implementation makes these harder, it is the wrong implementation.

---

## Codex instruction summary
If Codex is reading this file, the immediate task is:

1. Build the first stateful Auralite city shell.
2. Seed the city with districts, households, and residents.
3. Make time run.
4. Make residents visibly live simple daily lives.
5. Preserve the long-term architecture.

Prefer a clean, buildable, vertical slice over overengineering.
