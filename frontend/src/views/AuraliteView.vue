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
        :selected-district-id="selectedDistrictId"
        :selected-resident-id="selectedResidentId"
        :spatial-readback="spatialReadback"
        :resident-spatial-readback="residentSpatialReadback"
        :household-spatial-readback="householdSpatialReadback"
        :institution-spatial-readback="institutionSpatialReadback"
        @select-district="selectDistrict"
        @select-resident="selectResident"
      />
      <div class="inspectors">
        <ExplainabilityHooks :artifacts="world.reporting_state?.artifacts || {}" />
        <ScenarioDigestPanel
          :digest="world.reporting_state?.artifacts?.scenario_digest || world.scenario_state?.reporting_views?.scenario_digest || {}"
          :key-actor-escalation="world.reporting_state?.artifacts?.key_actor_escalation || world.scenario_state?.reporting_views?.key_actor_escalation || {}"
          :monitoring-watchlist="world.reporting_state?.artifacts?.monitoring_watchlist || world.scenario_state?.reporting_views?.monitoring_watchlist || {}"
          :stability-signals="world.reporting_state?.artifacts?.stability_signals || world.scenario_state?.reporting_views?.stability_signals || {}"
          :operator-brief="world.reporting_state?.artifacts?.operator_brief || {}"
        />
        <ScenarioHandoffPanel
          :handoff="world.reporting_state?.artifacts?.scenario_handoff || world.scenario_state?.reporting_views?.scenario_handoff || {}"
          :session-continuity="world.reporting_state?.artifacts?.operator_session_continuity || world.scenario_state?.reporting_views?.operator_session_continuity || world.scenario_state?.operator_session_view || {}"
          :intervention-feedback="world.reporting_state?.artifacts?.intervention_feedback_loop || world.scenario_state?.reporting_views?.intervention_feedback_loop || {}"
        />
        <RunOutcomeSummary
          :outcome="world.reporting_state?.artifacts?.scenario_outcome || world.scenario_state?.run_summary || {}"
          :drilldown="world.reporting_state?.artifacts?.outcome_drilldown || world.scenario_state?.reporting_views?.outcome_drilldown || {}"
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
          :intervention-feedback="world.reporting_state?.artifacts?.intervention_feedback_loop || world.scenario_state?.reporting_views?.intervention_feedback_loop || {}"
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
  buildResidentSpatialReadback,
  buildSpatialReadback,
} from '../lib/auralite/spatialReadback'

const world = ref({})
const selectedDistrictId = ref('')
const selectedResidentId = ref('')
const lastSnapshotId = ref('')
let timer = null

const loadWorld = async () => {
  world.value = await getAuraliteWorld()
  if (!selectedDistrictId.value && world.value.districts?.length) {
    selectedDistrictId.value = world.value.districts[0].district_id
  }
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

const selectedDistrict = computed(() => (world.value.districts || []).find((d) => d.district_id === selectedDistrictId.value))
const selectedResident = computed(() => (world.value.persons || []).find((p) => p.person_id === selectedResidentId.value))
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
const districtStoryThreads = computed(() =>
  world.value.reporting_state?.artifacts?.district_story_threads?.threads
  || world.value.scenario_state?.reporting_views?.district_story_threads?.threads
  || [],
)
const residentStoryThreads = computed(() =>
  world.value.reporting_state?.artifacts?.resident_story_threads?.threads
  || world.value.scenario_state?.reporting_views?.resident_story_threads?.threads
  || [],
)

const spatialReadback = computed(() => buildSpatialReadback({
  world: world.value,
  selectedDistrictId: selectedDistrictId.value,
  latestDistrictShifts: latestDistrictShifts.value,
}))
const residentSpatialReadback = computed(() => buildResidentSpatialReadback({
  world: world.value,
  spatialReadback: spatialReadback.value,
  selectedResidentId: selectedResidentId.value,
}))
const householdSpatialReadback = computed(() => buildHouseholdSpatialReadback({
  world: world.value,
  spatialReadback: spatialReadback.value,
  residentSpatialReadback: residentSpatialReadback.value,
  selectedResidentId: selectedResidentId.value,
}))
const institutionSpatialReadback = computed(() => buildInstitutionSpatialReadback({
  world: world.value,
  spatialReadback: spatialReadback.value,
  residentSpatialReadback: residentSpatialReadback.value,
  householdSpatialReadback: householdSpatialReadback.value,
  selectedResidentId: selectedResidentId.value,
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

const selectDistrict = (id) => { selectedDistrictId.value = id }
const selectResident = (id) => {
  selectedResidentId.value = id
  const resident = (world.value.persons || []).find((row) => row.person_id === id)
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
