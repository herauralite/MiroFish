<template>
  <div class="panel">
    <h3>Resident</h3>
    <div v-if="resident">
      <p><strong>{{ resident.name }}</strong> ({{ resident.age }})</p>
      <p>{{ resident.occupation }} | {{ resident.current_activity }}</p>
      <p class="subhead">{{ inspectorSectionTitles.summary }}</p>
      <p>Status: {{ resident.employment_status }} · Shift: {{ resident.shift_window }}</p>
      <p>Routine: {{ resident.routine_type }} | Wage: ${{ resident.hourly_wage }}/hr</p>
      <p>Housing burden share: {{ resident.housing_burden_share }} | Service access: {{ resident.service_access_score }}</p>
      <p>Stress: {{ resident.state_summary?.stress }} | Commute reliability: {{ resident.state_summary?.commute_reliability }}</p>
      <p>Social support: {{ resident.social_context?.support_index ?? '—' }} | Social strain: {{ resident.social_context?.strain_index ?? '—' }}</p>
      <p>Support channel: {{ resident.social_context?.primary_support_channel || '—' }} | Employer adjacency: {{ resident.social_context?.employer_adjacency || '—' }}</p>
      <p class="subhead">Operator focus coherence</p>
      <p class="subtle">{{ formatInspectorLabeledLine('Role', operatorSurfaceRoles.inspector) }}</p>
      <p>{{ formatInspectorLabeledLine('Local anchor', residentAnchorLine) }}</p>
      <p>{{ formatInspectorLabeledLine('Local state', focusStateLine) }}</p>
      <p class="operator-priority">{{ formatInspectorLabeledLine('Action cue', localActionLine) }}</p>
      <p>{{ formatInspectorLabeledLine('Scope', localScopeLine) }}</p>
      <div class="signal-pills">
        <span class="pill conf">Conf {{ focusSignals.confidence }}</span>
        <span class="pill stab">Stable {{ focusSignals.stability }}</span>
        <span class="pill next">Next {{ focusSignals.nextCheck }}</span>
      </div>
      <p>{{ formatInspectorLabeledLine('Why now', localReasonLine) }}</p>
      <p>{{ formatInspectorLabeledLine('Local evidence', localEvidenceLine) }}</p>
      <p>{{ formatInspectorLabeledLine('Nearby context', localContextLine) }}</p>

      <p class="subhead">{{ inspectorSectionTitles.secondary }}</p>
      <p>{{ residentSecondaryContextLine }}</p>
      <p>{{ formatInspectorLabeledLine('Trajectory', formatInspectorTrajectoryLine(resident.trajectory?.signals)) }}</p>

      <p class="subhead">{{ inspectorSectionTitles.diagnostics }}</p>
      <p>{{ formatInspectorLabeledLine('Causal shift', `${residentCausalShiftLine} · why ${residentCausalWhyLine}`) }}</p>
      <p>{{ formatInspectorLabeledLine('Systems/support/ties', residentSystemsSupportTiesLine) }}</p>
      <p>{{ formatInspectorLabeledLine('Support edges', summarizeSocialTies(socialTies)) }}</p>
      <p>{{ formatInspectorLabeledLine('Social ripple', residentRippleLine) }}</p>
      <p class="subhead">Resident story thread</p>
      <p>{{ residentStory?.headline || 'No resident story thread captured yet.' }}</p>
      <p v-if="residentStory">
        Shift score: {{ residentStory.shift_score }} |
        stress Δ {{ residentStory.signals?.stress_delta ?? 0 }} |
        service Δ {{ residentStory.signals?.service_delta ?? 0 }}
      </p>
      <p v-if="residentStory">Story systems: {{ summarizeInspectorSystems(residentStory.top_systems) }}</p>

      <template v-if="household">
        <p class="subhead">Household context</p>
        <p>Type: {{ household.household_type }} | Members: {{ household.member_ids?.length }}</p>
        <p>Income: ${{ household.monthly_income }} | Rent: ${{ household.monthly_rent }}</p>
        <p>Cost burden: {{ household.housing_cost_burden }} | Pressure: {{ household.pressure_level }}</p>
        <p>Eviction risk: {{ household.eviction_risk }} | Landlord id: {{ household.landlord_id || '—' }}</p>
        <p>{{ formatInspectorLabeledLine('Local anchor', householdAnchorLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Local state', householdLocalStateLine) }}</p>
        <p class="operator-priority">{{ formatInspectorLabeledLine('Action cue', householdActionLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Scope', householdScopeLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Local reason', householdReasonLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Local evidence', householdEvidenceLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Nearby context', householdNearbyContextLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Coherence', coherenceSummary) }}</p>
        <p>{{ formatInspectorLabeledLine('Trajectory', formatInspectorTrajectoryLine(household.trajectory?.signals)) }}</p>
        <p>{{ formatInspectorLabeledLine('Causal shift', householdCausalShiftLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Systems/support', householdSystemsSupportLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Spatial lane', householdSpatialLaneLine) }}</p>
        <p>{{ formatInspectorLabeledLine('Household ripple', householdRippleLine) }}</p>
      </template>

      <template v-if="institutionContext.length">
        <p class="subhead">Institution context</p>
        <p v-for="inst in institutionContext" :key="inst.institution_id">
          {{ institutionLine(inst) }}
        </p>
      </template>
      <template v-if="institutionSpatialContext?.length">
        <p class="subhead">Institution spatial context + coherence</p>
        <p v-for="inst in institutionSpatialContext" :key="`spatial-${inst.institution_id}`">
          {{ institutionSpatialLine(inst) }}
        </p>
        <p>{{ formatInspectorLabeledLine('Coherence', institutionCoherenceLine) }}</p>
      </template>
      <template v-if="socialGraph?.edge_counts">
        <p class="subhead">City social graph scaffold</p>
        <p>Edges — household: {{ socialGraph.edge_counts.household ?? 0 }}, coworker: {{ socialGraph.edge_counts.coworker ?? 0 }}, district-local: {{ socialGraph.edge_counts.district_local ?? 0 }}</p>
      </template>
    </div>
    <p v-else>Select a resident marker</p>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import {
  formatCompactWhyLine,
  formatEvidenceBundleLine,
  formatLocalActionCueLine,
  formatLocalAnchorLine,
  formatLocalNearbyContextLine,
  formatFocusStateLine,
  formatFocusSignalSet,
  formatScenarioScopeLine,
  operatorSurfaceRoles,
} from '../../../lib/auralite/operatorFocusFormatting'
import {
  formatCoherenceLaneLine,
  formatInstitutionCoherenceLine,
  formatInstitutionContextLine,
  formatInstitutionSpatialLine,
  formatInspectorLabeledLine,
  formatInspectorRippleLine,
  formatInspectorTrajectoryLine,
  inspectorSectionTitles,
  summarizeInspectorSystems,
} from '../../../lib/auralite/inspectorFraming'

const props = defineProps({
  resident: Object,
  household: Object,
  institutions: Array,
  socialTies: Array,
  socialGraph: Object,
  residentStoryThreads: { type: Array, default: () => [] },
  residentSpatialContext: { type: Object, default: null },
  householdSpatialContext: { type: Object, default: null },
  householdResidentCoherence: { type: Object, default: null },
  institutionSpatialContext: { type: Array, default: () => [] },
  institutionCoherence: { type: Object, default: null },
  operatorFocusReadback: { type: Object, default: null },
})

const institutionContext = computed(() => (props.institutions || []).filter(Boolean))
const residentStory = computed(() =>
  (props.residentStoryThreads || []).find((thread) => thread.resident_id === props.resident?.person_id),
)
const coherenceSummary = computed(() => {
  const coherence = props.householdResidentCoherence
  if (!coherence) return '—'
  const district = coherence.residentDistrictMatchesHousehold ? 'aligned district anchor' : `mixed district anchor (${coherence.sameDistrictLabel})`
  const watch = coherence.watchedAlignment ? 'watch alignment stable' : 'watch alignment split'
  const aftermath = coherence.aftermathAlignment ? 'aftermath alignment stable' : 'aftermath alignment split'
  return `${district} · ${watch} · ${aftermath}`
})
const focusExplainability = computed(() => props.operatorFocusReadback?.explainability || {})
const focusSignals = computed(() => formatFocusSignalSet(props.operatorFocusReadback?.priorities?.confidence || {}))
const residentCausalShiftLine = computed(() => {
  const changed = props.resident?.derived_summary?.causal_readout?.what_changed || {}
  return `stress ${changed.stress ?? 0}, housing ${changed.housing_stability ?? 0}, employment ${changed.employment_stability ?? 0}`
})
const residentTieSummary = computed(() => {
  const social = props.resident?.social_context || {}
  return `ties hh ${social.household_ties ?? 0}, coworker ${social.coworker_ties ?? 0}, district ${social.district_local_ties ?? 0}`
})
const residentSystemsSupportTiesLine = computed(() => {
  const systems = summarizeSystems(props.resident?.derived_summary?.causal_readout?.top_system_contributors)
  const support = props.resident?.social_context?.support_index ?? '—'
  const strain = props.resident?.social_context?.strain_index ?? '—'
  return `systems ${systems} · support ${support} · strain ${strain} · ${residentTieSummary.value}`
})
const focusStateLine = computed(() => {
  const signal = props.operatorFocusReadback?.coherence?.district_signal || props.residentSpatialContext?.districtSignal || 'mixed'
  const watch = props.operatorFocusReadback?.coherence?.district_watch ?? props.residentSpatialContext?.inWatchedArea
  const aftermath = props.operatorFocusReadback?.coherence?.district_aftermath ?? props.residentSpatialContext?.aftermathTouchesDistrict
  return formatFocusStateLine({ signal, watch, aftermath })
})
const residentAnchorLine = computed(() => formatLocalAnchorLine({
  district: props.residentSpatialContext?.district_name || props.resident?.district_id || 'unscoped district',
  location: props.residentSpatialContext?.current_location_id || props.resident?.current_location_id || 'no location anchor',
  subject: props.resident?.person_id ? `resident ${props.resident.person_id}` : 'resident —',
}, 96))
const localActionLine = computed(() => {
  return formatLocalActionCueLine({
    driver: focusExplainability.value?.district?.what || 'No dominant district driver yet.',
    nextCheck: focusExplainability.value?.nextCheck?.what || 'Continue watchlist monitoring.',
  })
})
const localScopeLine = computed(() => formatScenarioScopeLine({
  resident: props.resident?.person_id ? `resident ${props.resident.person_id}` : props.resident?.name || '—',
  institution: summarizeKinds(props.residentSpatialContext?.serviceContext?.relevantKinds),
}))
const localReasonLine = computed(() => formatCompactWhyLine(focusExplainability.value?.nextCheck?.why || 'Immediate follow-up reason is still forming.'))
const localEvidenceLine = computed(() => formatEvidenceBundleLine(props.operatorFocusReadback?.priorities?.evidence || {}))
const localContextLine = computed(() => {
  return formatLocalNearbyContextLine({
    district: props.operatorFocusReadback?.selected?.district_name || props.residentSpatialContext?.district_name || props.resident?.district_id || 'unscoped district',
    service: summarizeKinds(props.residentSpatialContext?.serviceContext?.relevantKinds),
    nearby: summarizeNearbyInstitutions(props.residentSpatialContext?.serviceContext?.nearbyInstitutions),
  }, 132)
})
const residentSecondaryContextLine = computed(() => {
  const services = summarizeKinds(props.residentSpatialContext?.serviceContext?.relevantKinds)
  const nearby = summarizeNearbyInstitutions(props.residentSpatialContext?.serviceContext?.nearbyInstitutions)
  return formatCoherenceLaneLine({
    anchor: props.residentSpatialContext?.district_name || props.resident?.district_id || 'unscoped district',
    lane: props.residentSpatialContext?.current_location_id || props.resident?.current_location_id || 'no location anchor',
    watch: props.residentSpatialContext?.inWatchedArea,
    aftermath: props.residentSpatialContext?.aftermathTouchesDistrict,
    signal: props.residentSpatialContext?.districtSignal || 'mixed',
    context: `services ${services} · nearby ${nearby}`,
  })
})
const residentCausalWhyLine = computed(() => (
  props.resident?.derived_summary?.causal_readout?.why_changed?.[0] || 'No dominant resident-level driver identified.'
))
const householdAnchorLine = computed(() => {
  return formatLocalAnchorLine({
    district: props.householdSpatialContext?.district_name || props.household?.district_id || 'unscoped district',
    location: props.householdSpatialContext?.home_location_id || props.household?.home_location_id || 'no home anchor',
    subject: props.household?.household_id ? `hh ${props.household.household_id}` : 'hh —',
  }, 96)
})
const householdLocalStateLine = computed(() => {
  const signal = props.householdSpatialContext?.districtSignal || props.operatorFocusReadback?.coherence?.district_signal || 'mixed'
  const watch = props.householdSpatialContext?.inWatchedArea ?? props.operatorFocusReadback?.coherence?.district_watch
  const aftermath = props.householdSpatialContext?.aftermathTouchesDistrict ?? props.operatorFocusReadback?.coherence?.district_aftermath
  return formatFocusStateLine({ signal, watch, aftermath })
})
const householdActionLine = computed(() => {
  return formatLocalActionCueLine({
    driver: props.household?.derived_summary?.causal_readout?.why_changed?.[0] || 'No dominant household-level driver identified.',
    nextCheck: props.operatorFocusReadback?.priorities?.nextCheck?.what || 'Continue watchlist monitoring.',
  }, 108)
})
const householdReasonLine = computed(() => formatCompactWhyLine(
  props.household?.derived_summary?.causal_readout?.why_changed?.[0]
  || focusExplainability.value?.nextCheck?.why
  || 'Immediate household follow-up reason is still forming.',
))
const householdEvidenceLine = computed(() => formatEvidenceBundleLine(props.operatorFocusReadback?.priorities?.evidence || {}))
const householdNearbyContextLine = computed(() => {
  return formatLocalNearbyContextLine({
    district: props.householdSpatialContext?.district_name || props.household?.district_id || 'unscoped district',
    service: summarizeKinds(props.householdSpatialContext?.serviceContext?.relevantKinds),
    nearby: summarizeNearbyInstitutions(props.householdSpatialContext?.serviceContext?.nearbyInstitutions),
  }, 132)
})

const householdScopeLine = computed(() => formatScenarioScopeLine({
  resident: props.household?.household_id ? `hh ${props.household.household_id}` : '—',
  institution: summarizeKinds(props.householdSpatialContext?.serviceContext?.relevantKinds),
}))
const householdCausalShiftLine = computed(() => {
  const changed = props.household?.derived_summary?.causal_readout?.what_changed || {}
  return `stress ${changed.stress ?? 0}, housing ${changed.housing_stability ?? 0}, employment ${changed.employment_stability ?? 0}`
})
const householdSystemsSupportLine = computed(() => {
  const systems = summarizeSystems(props.household?.derived_summary?.causal_readout?.top_system_contributors)
  const support = props.household?.social_context?.support_exposure ?? '—'
  const strain = props.household?.social_context?.local_strain_index ?? '—'
  return `systems ${systems} · support ${support} · strain ${strain}`
})
const householdSpatialLaneLine = computed(() => {
  const services = summarizeKinds(props.householdSpatialContext?.serviceContext?.relevantKinds)
  return formatCoherenceLaneLine({
    anchor: props.householdSpatialContext?.district_name || props.household?.district_id || 'unscoped district',
    lane: props.householdSpatialContext?.home_location_id || props.household?.home_location_id || '—',
    watch: props.householdSpatialContext?.inWatchedArea,
    aftermath: props.householdSpatialContext?.aftermathTouchesDistrict,
    signal: props.householdSpatialContext?.districtSignal || props.operatorFocusReadback?.coherence?.district_signal || 'mixed',
    context: `services ${services}`,
  })
})
const householdRippleLine = computed(() => {
  const context = props.household?.derived_summary?.propagation_context || {}
  return formatInspectorRippleLine({
    incomingStress: context.incoming_social_stress ?? 0,
    delta: context.stress_delta,
    edges: summarizePropagationEdges(context.incoming_social_edges || [], 'household'),
  })
})
const residentRippleLine = computed(() => {
  const context = props.resident?.derived_summary?.propagation_context || {}
  return formatInspectorRippleLine({
    incomingStress: context.incoming_social_stress ?? 0,
    edgeCount: context.recent_social_event_count ?? 0,
    edges: summarizePropagationEdges(context.incoming_social_edges || [], 'person'),
  })
})
const institutionLine = (inst = {}) => (
  formatInstitutionContextLine(inst, 176)
)
const institutionSpatialLine = (inst = {}) => (
  formatInstitutionSpatialLine(inst, 176)
)
const institutionCoherenceLine = computed(() => {
  return formatInstitutionCoherenceLine(props.institutionCoherence || {}, 176)
})

const summarizeSystems = (systems = []) => summarizeInspectorSystems(systems)
const summarizeSocialTies = (ties = []) => {
  if (!ties?.length) return '—'
  return ties.slice(0, 5).map((tie) => `${tie.tie_type}: ${tie.person?.name || tie.person_id}`).join(' · ')
}
const summarizePropagationEdges = (edges = [], mode = 'person') => {
  if (!edges?.length) return '—'
  const idKey = mode === 'household' ? 'from_person_id' : 'from_person_id'
  return edges.slice(0, 4).map((edge) => `${edge.tie_type} ${edge[idKey]} (${edge.stress_shift})`).join(' · ')
}
const summarizeKinds = (kinds = []) => (kinds?.length ? kinds.slice(0, 4).join(', ') : '—')
const summarizeNearbyInstitutions = (rows = []) => {
  if (!rows?.length) return '—'
  return rows.slice(0, 3).map((row) => `${row.type}: ${row.name} (access ${row.access_score}, pressure ${row.pressure_index})`).join(' · ')
}
</script>
<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
p{margin:4px 0}
.subhead{margin-top:8px;font-weight:700}
.operator-priority{font-weight:600}
.signal-pills{display:flex;gap:6px;flex-wrap:wrap;margin:1px 0 4px}
.pill{display:inline-flex;align-items:center;padding:1px 6px;border-radius:999px;font-size:10.5px;font-weight:600}
.pill.conf{background:#fff2cc;color:#8a5a00}
.pill.stab{background:#e7f6ff;color:#055a7a}
.pill.next{background:#e9f8ec;color:#1d6b34}
.subtle{color:#667085}
</style>
