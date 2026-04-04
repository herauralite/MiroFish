# Auralite File Map for Codex

## Purpose
This document tells Codex **where Auralite code should live in this repository**.

It exists to prevent architectural drift and random file placement.
It should be used together with:
- `docs/AURALITE_MASTER_BLUEPRINT.md`
- `docs/CODEX_AURALITE_EXECUTION_PROMPT.md`
- `docs/AURALITE_MILESTONE_01_BUILD_SPEC.md`

If Codex needs to add Auralite implementation files, it should prefer the paths in this document unless there is a strong repository-specific reason to adapt them.

---

## Guiding principle
Auralite should be added as a **layered extension** of the existing repo, not as a chaotic pile of unrelated files.

The code layout should reflect these major Auralite domains:
- world
- population
- institutions
- runtime/simulation
- cognition
- reporting
- frontend presentation

---

## Recommended backend structure

Base backend root:
- `backend/app/`

### 1. API layer
Use or extend:
- `backend/app/api/`

Recommended additions:
- `backend/app/api/auralite.py`

Purpose:
- world endpoints
- district endpoints
- resident endpoints
- runtime control endpoints
- save/load endpoints
- later intervention endpoints

### 2. Models layer
Use or extend:
- `backend/app/models/`

Recommended additions:
- `backend/app/models/auralite_world.py`
- `backend/app/models/auralite_city.py`
- `backend/app/models/auralite_district.py`
- `backend/app/models/auralite_location.py`
- `backend/app/models/auralite_person.py`
- `backend/app/models/auralite_household.py`
- `backend/app/models/auralite_event.py`
- `backend/app/models/auralite_narrative.py`

Purpose:
- define durable stateful entities
- keep world objects explicit and structured

### 3. Services layer
Use or extend:
- `backend/app/services/`

Recommended additions:
- `backend/app/services/auralite_world_service.py`
- `backend/app/services/auralite_seed_service.py`
- `backend/app/services/auralite_runtime_service.py`
- `backend/app/services/auralite_persistence_service.py`
- `backend/app/services/auralite_district_service.py`
- `backend/app/services/auralite_population_service.py`

Later additions:
- `backend/app/services/auralite_institution_service.py`
- `backend/app/services/auralite_intervention_service.py`
- `backend/app/services/auralite_narrative_service.py`
- `backend/app/services/auralite_reporting_service.py`

Purpose:
- world creation
- population seeding
- runtime ticking
- save/load
- district summaries
- state derivation for frontend

### 4. Cognition integration layer
Auralite should reuse current repo simulation/reporting capabilities where possible.
Do not duplicate MiroFish-style cognition logic in unrelated places.

Preferred approach:
- keep existing simulation/report/interview logic where it already lives
- add adapter/service files that bridge Auralite residents into that cognition layer when needed

Potential additions later:
- `backend/app/services/auralite_cognition_adapter.py`
- `backend/app/services/auralite_agent_inspection_service.py`

### 5. Storage / data directories
If the repo already has upload/runtime data conventions, reuse them.
For Auralite-specific persistent world files, prefer a clearly named subdirectory.

Recommended path patterns:
- `backend/uploads/auralite/worlds/`
- `backend/uploads/auralite/snapshots/`
- `backend/uploads/auralite/reports/`

If a database is used, keep the schema Auralite-aware but avoid scattering ad hoc save files across the repo.

---

## Recommended frontend structure

Base frontend root:
- `frontend/`

Codex should adapt to the existing frontend app structure, but should preserve a clean separation between:
- pages/views
- map rendering
- inspector panels
- state hooks/store
- reusable UI components

### 1. Auralite page/view
Preferred additions under the existing frontend page/view pattern.
Examples (adapt to framework used):
- `frontend/src/pages/Auralite.tsx`
- or `frontend/src/views/AuraliteView.tsx`

Purpose:
- main Auralite screen
- compose HUD, map, inspectors, controls

### 2. Map components
Recommended grouping:
- `frontend/src/components/auralite/map/AuraliteMap.tsx`
- `frontend/src/components/auralite/map/DistrictLayer.tsx`
- `frontend/src/components/auralite/map/ResidentLayer.tsx`
- `frontend/src/components/auralite/map/LocationLayer.tsx`

Purpose:
- render city shell
- render district overlays
- render resident markers
- later render events/institutions/heatmaps

### 3. Inspector components
Recommended grouping:
- `frontend/src/components/auralite/inspectors/DistrictInspector.tsx`
- `frontend/src/components/auralite/inspectors/ResidentInspector.tsx`
- later: `InstitutionInspector.tsx`

Purpose:
- selected entity detail views
- keep UI modular

### 4. HUD and controls
Recommended grouping:
- `frontend/src/components/auralite/HUD/AuraliteHUD.tsx`
- `frontend/src/components/auralite/HUD/TimeControls.tsx`
- later: `InterventionConsole.tsx`

Purpose:
- city title
- clock
- play/pause/speed
- global metrics

### 5. State and API hooks
Recommended grouping:
- `frontend/src/lib/auralite/api.ts`
- `frontend/src/lib/auralite/types.ts`
- `frontend/src/lib/auralite/hooks.ts`
- or equivalent store structure already used in repo

Purpose:
- fetch world state
- fetch districts/residents
- control sim runtime
- keep Auralite state logic out of random UI files

### 6. Static config/data
For named districts and other initial configuration, prefer explicit config files rather than burying them in components.

Recommended paths:
- `frontend/src/lib/auralite/districtConfig.ts`
- `frontend/src/lib/auralite/mapRegions.ts`

Purpose:
- stable district identity mapping
- map region to district object mapping

---

## Milestone 01 specific file priorities
If Codex is implementing Milestone 01 first, it should prioritize creating or extending files roughly in this order:

### Backend first-pass priorities
1. `backend/app/api/auralite.py`
2. `backend/app/services/auralite_world_service.py`
3. `backend/app/services/auralite_seed_service.py`
4. `backend/app/services/auralite_runtime_service.py`
5. `backend/app/services/auralite_persistence_service.py`
6. `backend/app/models/auralite_world.py`
7. `backend/app/models/auralite_district.py`
8. `backend/app/models/auralite_person.py`
9. `backend/app/models/auralite_household.py`
10. `backend/app/models/auralite_location.py`

### Frontend first-pass priorities
1. Auralite page/view file
2. Auralite map component
3. district config/map region config
4. HUD/time controls
5. district inspector
6. resident layer
7. resident lightweight inspector/tooltip
8. Auralite API hooks/types file

---

## What should stay out of milestone 01 files
To avoid polluting the early slice, do not jam these into the first milestone unless truly necessary:
- deep intervention branching logic
- complex report generation logic
- fully generalized institution engine
- large prompt templates scattered across UI files
- unrelated cleanup work in existing simulation files

Milestone 01 should establish the world shell and clean state backbone first.

---

## Relationship to existing repo files
Codex should treat existing repo systems as reusable infrastructure where helpful.

Examples:
- existing app factory and blueprints remain valid structural anchors
- existing simulation/report services may later power cognition/explainability features
- existing frontend app shell should be reused rather than bypassed

However, Auralite-specific world code should still be clearly named and separated so that:
- the world layer stays understandable
- future contributors can find Auralite logic quickly
- long-term architecture remains visible in the repo

---

## Naming rule
Use `auralite_` prefixed backend modules and clearly grouped frontend Auralite folders/components for all newly introduced world-sim logic.

This keeps the implementation easy to identify and reduces confusion between:
- original MiroFish functionality
- Auralite world simulation functionality

---

## Final instruction for Codex
If Codex needs to choose between:
- putting Auralite code in a random convenient place,
- or creating a clearly named Auralite-specific module structure,

it should choose the clearly named Auralite structure.

The file layout should make the long-term city simulation architecture obvious from the repository tree.
