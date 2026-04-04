<template>
  <div class="auralite-view">
    <AuraliteHUD
      :city="world.city"
      :world="world.world"
      :scenario-state="world.scenario_state"
      :last-snapshot-id="lastSnapshotId"
      @start="start"
      @pause="pause"
      @tick="tick"
      @speed="speed"
      @save="saveSnapshot"
      @load="loadSnapshot"
    />
    <div class="layout">
      <AuraliteMap
        :districts="world.districts || []"
        :resident-markers="residentMarkers"
        :selected-district-id="effectiveSelectedDistrictId"
        :selected-resident-id="effectiveSelectedResidentId"
        :spatial-readback="spatialReadback"
        :resident-spatial-readback="residentSpatialReadback"
        :household-spatial-readback="householdSpatialReadback"
        :institution-spatial-readback="institutionSpatialReadback"
        :operator-focus-readback="operatorFocusReadback"
        @select-district="selectDistrict"
        @select-resident="selectResident"
      />
      <div class="inspectors">
        <ExplainabilityHooks :artifacts="reportingArtifacts" />
        <ScenarioDigestPanel
          :digest="reportingArtifact('scenario_digest')"
          :key-actor-escalation="reportingArtifact('key_actor_escalation')"
          :monitoring-watchlist="reportingArtifact('monitoring_watchlist')"
          :stability-signals="reportingArtifact('stability_signals')"
          :operator-brief="reportingArtifact('operator_brief')"
        />
        <ScenarioHandoffPanel
          :handoff="reportingArtifact('scenario_handoff')"
          :session-continuity="reportingArtifact('operator_session_continuity', world.scenario_state?.operator_session_view || {})"
          :intervention-feedback="reportingArtifact('intervention_feedback_loop')"
        />
        <RunOutcomeSummary
          :outcome="reportingArtifact('scenario_outcome', world.scenario_state?.run_summary || {})"
          :drilldown="reportingArtifact('outcome_drilldown')"
        />
        <SavedScenarioInsights
          :insights="world.scenario_state?.saved_insights || []"
          :timeline="world.scenario_state?.timeline || []"
          :run-outcome="world.scenario_state?.scenario_outcome || world.reporting_state?.artifacts?.scenario_outcome || {}"
          :reporting-views="world.scenario_state?.reporting_views || {}"
          :filter-catalog="world.scenario_state?.insight_filter_catalog || {}"
        />
        <DistrictInspector
          :district="selectedDistrict"
          :spatial-context="spatialReadback.selectedDistrictContext"
          :comparison-summary="world.scenario_state?.last_comparison || {}"
          :latest-district-shifts="latestDistrictShifts"
          :district-story-threads="districtStoryThreads"
          :operator-focus-readback="operatorFocusReadback"
        />
        <ResidentInspector
          :resident="selectedResident"
          :household="selectedHousehold"
          :institutions="selectedResidentInstitutions"
          :social-ties="selectedResidentSocialTies"
          :social-graph="world.social_graph || {}"
          :resident-story-threads="residentStoryThreads"
          :resident-spatial-context="residentSpatialReadback.selectedResidentContext"
          :household-spatial-context="householdSpatialReadback.selectedHouseholdContext"
          :household-resident-coherence="householdSpatialReadback.coherence"
          :institution-spatial-context="institutionSpatialReadback.selectedInstitutionContext"
          :institution-coherence="institutionSpatialReadback.coherence"
          :operator-focus-readback="operatorFocusReadback"
        />
        <InterventionPanel
          :districts="world.districts || []"
          :available-levers="world.intervention_state?.available_levers || []"
          :active-scenario-name="world.scenario_state?.active_scenario_name || 'default-baseline'"
          :last-applied="world.intervention_state?.last_applied_at || ''"
          @apply="applyIntervention"
          @capture-baseline="captureBaseline"
          @set-scenario="setScenarioName"
        />
        <InterventionHistory
          :history="world.intervention_state?.history || []"
          :snapshots="world.scenario_state?.snapshots || []"
          :comparison-report="world.scenario_state?.last_comparison_report?.report || {}"
          :intervention-feedback="reportingArtifact('intervention_feedback_loop')"
          @load-snapshot="loadSnapshotById"
          @compare-to-snapshot="compareToSnapshot"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import AuraliteHUD from '../components/auralite/HUD/AuraliteHUD.vue'
import AuraliteMap from '../components/auralite/map/AuraliteMap.vue'
import DistrictInspector from '../components/auralite/inspectors/DistrictInspector.vue'
import ExplainabilityHooks from '../components/auralite/inspectors/ExplainabilityHooks.vue'
import ScenarioDigestPanel from '../components/auralite/inspectors/ScenarioDigestPanel.vue'
import ScenarioHandoffPanel from '../components/auralite/inspectors/ScenarioHandoffPanel.vue'
import RunOutcomeSummary from '../components/auralite/inspectors/RunOutcomeSummary.vue'
import SavedScenarioInsights from '../components/auralite/inspectors/SavedScenarioInsights.vue'
import ResidentInspector from '../components/auralite/inspectors/ResidentInspector.vue'
import InterventionPanel from '../components/auralite/interventions/InterventionPanel.vue'
import InterventionHistory from '../components/auralite/interventions/InterventionHistory.vue'
import {
  applyAuraliteIntervention,
  compareAuraliteScenarios,
  controlAuraliteRuntime,
  getAuraliteWorld,
  loadAuraliteWorld,
  saveAuraliteWorld,
  setActiveScenario,
  tickAuraliteRuntime,
} from '../lib/auralite/api'
import {
  buildHouseholdSpatialReadback,
  buildInstitutionSpatialReadback,
  buildOperatorFocusReadback,
  buildResidentSpatialReadback,
  buildSpatialReadback,
} from '../lib/auralite/spatialReadback'

const world = ref({})
const selectedDistrictId = ref('')
const selectedResidentId = ref('')
const lastSnapshotId = ref('')
let timer = null

const resolveSelectionState = ({ worldState = {}, districtId = '', residentId = '' }) => {
  const districts = worldState.districts || []
  const residents = worldState.persons || []
  const districtById = new Map(districts.map((district) => [district.district_id, district]))
  const residentById = new Map(residents.map((resident) => [resident.person_id, resident]))

  const selectedResident = residentById.get(residentId) || null
  const resolvedResidentId = selectedResident ? selectedResident.person_id : ''
  const explicitDistrict = districtById.get(districtId) || null

  if (selectedResident?.district_id && districtById.has(selectedResident.district_id)) {
    return {
      selectedResidentId: resolvedResidentId,
      selectedDistrictId: selectedResident.district_id,
    }
  }

  if (explicitDistrict) {
    return {
      selectedResidentId: resolvedResidentId,
      selectedDistrictId: explicitDistrict.district_id,
    }
  }

  return {
    selectedResidentId: resolvedResidentId,
    selectedDistrictId: districts[0]?.district_id || '',
  }
}

const reconcileSelectionState = () => {
  const resolved = resolveSelectionState({
    worldState: world.value,
    districtId: selectedDistrictId.value,
    residentId: selectedResidentId.value,
  })
  selectedDistrictId.value = resolved.selectedDistrictId
  selectedResidentId.value = resolved.selectedResidentId
}

const loadWorld = async () => {
  world.value = await getAuraliteWorld()
  reconcileSelectionState()
}

const residentMarkers = computed(() => {
  const byLoc = new Map((world.value.locations || []).map((l) => [l.location_id, l]))
  const simMinute = new Date(world.value.world?.current_time || Date.now()).getMinutes()
  return (world.value.persons || []).map((p, idx) => {
    const loc = byLoc.get(p.current_location_id)
    const j = ((idx + simMinute) % 7) / 12
    return { person_id: p.person_id, x: (loc?.x || 0) + j, y: (loc?.y || 0) + j }
  })
})

const resolvedSelection = computed(() => resolveSelectionState({
  worldState: world.value,
  districtId: selectedDistrictId.value,
  residentId: selectedResidentId.value,
}))
const effectiveSelectedDistrictId = computed(() => resolvedSelection.value.selectedDistrictId)
const effectiveSelectedResidentId = computed(() => resolvedSelection.value.selectedResidentId)
const selectedDistrict = computed(() => (world.value.districts || []).find((d) => d.district_id === effectiveSelectedDistrictId.value))
const selectedResident = computed(() => (world.value.persons || []).find((p) => p.person_id === effectiveSelectedResidentId.value))
const selectedHousehold = computed(() => {
  const resident = selectedResident.value
  if (!resident) return null
  return (world.value.households || []).find((h) => h.household_id === resident.household_id) || null
})

const selectedResidentInstitutions = computed(() => {
  const resident = selectedResident.value
  if (!resident) return []
  const institutionsById = new Map((world.value.institutions || []).map((i) => [i.institution_id, i]))
  return [
    institutionsById.get(resident.employer_id),
    institutionsById.get(resident.transit_service_id),
    institutionsById.get(resident.service_provider_id),
    institutionsById.get(selectedHousehold.value?.landlord_id),
  ].filter(Boolean)
})
const latestDistrictShifts = computed(() =>
  world.value.scenario_state?.last_comparison_report?.report?.delta_summary?.district_shifts
    || (world.value.intervention_state?.history?.length
      ? (world.value.intervention_state.history.at(-1)?.effects?.delta_summary?.district_shifts || [])
      : []),
)
const reportingArtifacts = computed(() => world.value.reporting_state?.artifacts || {})
const reportingViews = computed(() => world.value.scenario_state?.reporting_views || {})
const reportingArtifact = (key, fallback = {}) => (
  reportingArtifacts.value?.[key]
  || reportingViews.value?.[key]
  || fallback
)
const districtStoryThreads = computed(() =>
  reportingArtifact('district_story_threads')?.threads
  || [],
)
const residentStoryThreads = computed(() =>
  reportingArtifact('resident_story_threads')?.threads
  || [],
)

const spatialReadback = computed(() => buildSpatialReadback({
  world: world.value,
  selectedDistrictId: effectiveSelectedDistrictId.value,
  latestDistrictShifts: latestDistrictShifts.value,
}))
const residentSpatialReadback = computed(() => buildResidentSpatialReadback({
  world: world.value,
  spatialReadback: spatialReadback.value,
  selectedResidentId: effectiveSelectedResidentId.value,
}))
const householdSpatialReadback = computed(() => buildHouseholdSpatialReadback({
  world: world.value,
  spatialReadback: spatialReadback.value,
  residentSpatialReadback: residentSpatialReadback.value,
  selectedResidentId: effectiveSelectedResidentId.value,
}))
const institutionSpatialReadback = computed(() => buildInstitutionSpatialReadback({
  world: world.value,
  spatialReadback: spatialReadback.value,
  residentSpatialReadback: residentSpatialReadback.value,
  householdSpatialReadback: householdSpatialReadback.value,
  selectedResidentId: effectiveSelectedResidentId.value,
}))
const operatorFocusReadback = computed(() => buildOperatorFocusReadback({
  world: world.value,
  spatialReadback: spatialReadback.value,
  residentSpatialReadback: residentSpatialReadback.value,
  householdSpatialReadback: householdSpatialReadback.value,
  institutionSpatialReadback: institutionSpatialReadback.value,
  selectedDistrictId: effectiveSelectedDistrictId.value,
  selectedResidentId: effectiveSelectedResidentId.value,
}))

const selectedResidentSocialTies = computed(() => {
  const resident = selectedResident.value
  if (!resident) return []
  const byId = new Map((world.value.persons || []).map((p) => [p.person_id, p]))
  return (resident.social_ties || []).map((tie) => ({
    ...tie,
    person: byId.get(tie.person_id) || null,
  }))
})

const selectDistrict = (id) => {
  const districtExists = (world.value.districts || []).some((district) => district.district_id === id)
  selectedDistrictId.value = districtExists ? id : ''
  const selectedResidentRow = (world.value.persons || []).find((row) => row.person_id === selectedResidentId.value)
  if (selectedResidentRow?.district_id && selectedResidentRow.district_id !== selectedDistrictId.value) {
    selectedResidentId.value = ''
  }
}
const selectResident = (id) => {
  const resident = (world.value.persons || []).find((row) => row.person_id === id)
  if (!resident) {
    selectedResidentId.value = ''
    return
  }
  selectedResidentId.value = id
  if (resident?.district_id) selectedDistrictId.value = resident.district_id
}

const start = async () => { await controlAuraliteRuntime({ action: 'start' }); await loadWorld() }
const pause = async () => { await controlAuraliteRuntime({ action: 'pause' }); await loadWorld() }
const speed = async (value) => { await controlAuraliteRuntime({ action: 'speed', time_speed: value }); await loadWorld() }
const tick = async () => { await tickAuraliteRuntime({ minutes: 15 }); await loadWorld() }

const saveSnapshot = async () => {
  const data = await saveAuraliteWorld({ snapshot_name: world.value.scenario_state?.active_scenario_name || 'manual-snapshot', label: 'manual' })
  lastSnapshotId.value = data.snapshot_id
  await loadWorld()
}

const loadSnapshot = async () => {
  if (!lastSnapshotId.value) return
  await loadAuraliteWorld({ snapshot_id: lastSnapshotId.value })
  await loadWorld()
}

const loadSnapshotById = async (snapshotId) => {
  if (!snapshotId) return
  lastSnapshotId.value = snapshotId
  await loadAuraliteWorld({ snapshot_id: snapshotId })
  await loadWorld()
}

const captureBaseline = async () => {
  const scenarioName = world.value.scenario_state?.active_scenario_name || 'default-baseline'
  const data = await saveAuraliteWorld({ snapshot_name: `${scenarioName}-baseline`, label: 'baseline' })
  lastSnapshotId.value = data.snapshot_id
  await loadWorld()
}

const setScenarioName = async (scenarioName) => {
  if (!scenarioName) return
  await setActiveScenario({ scenario_name: scenarioName })
  await loadWorld()
}

const applyIntervention = async ({ district_id, lever, intensity }) => {
  const scenarioName = world.value.scenario_state?.active_scenario_name || 'default-baseline'
  await applyAuraliteIntervention({
    notes: `scenario:${scenarioName}`,
    changes: [{ district_id, lever, intensity }],
  })
  await loadWorld()
}

const compareToSnapshot = async (snapshotId) => {
  if (!snapshotId) return
  await compareAuraliteScenarios({
    baseline_snapshot_id: world.value.scenario_state?.baseline_snapshot_id,
    compare_snapshot_id: snapshotId,
  })
  await loadWorld()
}

onMounted(async () => {
  await loadWorld()
  timer = setInterval(loadWorld, 3000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.auralite-view{padding:12px;background:#f0f2f4;min-height:100vh}
.layout{display:grid;grid-template-columns: 1fr 340px;gap:12px;margin-top:12px}
.inspectors{display:flex;flex-direction:column;gap:12px}
</style>
