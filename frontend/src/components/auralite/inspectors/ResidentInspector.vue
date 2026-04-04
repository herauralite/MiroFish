<template>
  <div class="panel">
    <h3>Resident</h3>
    <div v-if="resident">
      <p><strong>{{ resident.name }}</strong> ({{ resident.age }})</p>
      <p>{{ resident.occupation }} | {{ resident.current_activity }}</p>
      <p>Status: {{ resident.employment_status }} · Shift: {{ resident.shift_window }}</p>
      <p>Routine: {{ resident.routine_type }} | Wage: ${{ resident.hourly_wage }}/hr</p>
      <p>Housing burden share: {{ resident.housing_burden_share }} | Service access: {{ resident.service_access_score }}</p>
      <p>Stress: {{ resident.state_summary?.stress }} | Commute reliability: {{ resident.state_summary?.commute_reliability }}</p>
      <p>Social support: {{ resident.social_context?.support_index ?? '—' }} | Social strain: {{ resident.social_context?.strain_index ?? '—' }}</p>
      <p>Support channel: {{ resident.social_context?.primary_support_channel || '—' }} | Employer adjacency: {{ resident.social_context?.employer_adjacency || '—' }}</p>
      <p class="subhead">Operator focus coherence</p>
      <p class="subtle"><strong>Role:</strong> {{ operatorSurfaceRoles.inspector }}</p>
      <p><strong>Focus state:</strong> {{ focusStateLine }}</p>
      <p class="operator-priority"><strong>Local next check:</strong> {{ focusExplainability.nextCheck.what }}</p>
      <div class="signal-pills">
        <span class="pill conf">Conf {{ focusSignals.confidence }}</span>
        <span class="pill stab">Stable {{ focusSignals.stability }}</span>
        <span class="pill next">Next {{ focusSignals.nextCheck }}</span>
      </div>
      <p>Scope: {{ operatorFocusReadback?.selected?.district_name || residentSpatialContext?.district_name || resident.district_id }} · {{ operatorSelectedLine }}</p>
      <p>Focus evidence: district {{ districtEvidenceLine }} · resident/household {{ residentEvidenceLine }} · institution {{ institutionEvidenceLine }} · next check {{ nextCheckEvidenceLine }}</p>
      <p>Resident/hh coherence signal: {{ focusExplainability.resident.what }}</p>
      <p>Institution coherence signal: {{ focusExplainability.institution.what }}</p>
      <p>Why this check: {{ focusExplainability.nextCheck.why }}</p>
      <p>Cross-layer relevance: {{ operatorRelevanceLine }}</p>
      <p class="subhead">Spatial context</p>
      <p>Situated in: {{ residentSpatialContext?.district_name || resident.district_id }} · Location anchor: {{ residentSpatialContext?.current_location_id || resident.current_location_id }}</p>
      <p>Watched resident: {{ residentSpatialContext?.isWatchedResident ? 'yes' : 'no' }} · Watched area: {{ residentSpatialContext?.inWatchedArea ? 'yes' : 'no' }}</p>
      <p>Intervention aftermath likely touches district: {{ residentSpatialContext?.aftermathTouchesDistrict ? 'yes' : 'no' }} (signal {{ residentSpatialContext?.districtSignal || 'mixed' }})</p>
      <p>Nearby service relevance: {{ summarizeKinds(residentSpatialContext?.serviceContext?.relevantKinds) }}</p>
      <p>Nearby institutions: {{ summarizeNearbyInstitutions(residentSpatialContext?.serviceContext?.nearbyInstitutions) }}</p>

      <p class="subhead">Resident trajectory (short-to-medium term)</p>
      <p>Stress trend: {{ trendLabel(resident.trajectory?.signals?.stress_trend) }}</p>
      <p>Housing stability trend: {{ trendLabel(resident.trajectory?.signals?.housing_stability_trend) }}</p>
      <p>Employment stability trend: {{ trendLabel(resident.trajectory?.signals?.employment_stability_trend) }}</p>
      <p>Service access trend: {{ trendLabel(resident.trajectory?.signals?.service_access_trend) }}</p>

      <p class="subhead">Resident causal readout</p>
      <p>
        What changed: stress {{ resident.derived_summary?.causal_readout?.what_changed?.stress ?? 0 }},
        housing {{ resident.derived_summary?.causal_readout?.what_changed?.housing_stability ?? 0 }},
        employment {{ resident.derived_summary?.causal_readout?.what_changed?.employment_stability ?? 0 }}
      </p>
      <p>Why: {{ resident.derived_summary?.causal_readout?.why_changed?.[0] || 'No dominant resident-level driver identified.' }}</p>
      <p>Top systems: {{ summarizeSystems(resident.derived_summary?.causal_readout?.top_system_contributors) }}</p>
      <p>Ties: household {{ resident.social_context?.household_ties ?? 0 }}, coworker {{ resident.social_context?.coworker_ties ?? 0 }}, district-local {{ resident.social_context?.district_local_ties ?? 0 }}</p>
      <p>Linked support edges: {{ summarizeSocialTies(socialTies) }}</p>
      <p>Incoming social spillover: {{ resident.derived_summary?.propagation_context?.incoming_social_stress ?? 0 }} ({{ resident.derived_summary?.propagation_context?.recent_social_event_count ?? 0 }} edges)</p>
      <p>Recent social ripple sources: {{ summarizePropagationEdges(resident.derived_summary?.propagation_context?.incoming_social_edges || [], 'person') }}</p>
      <p class="subhead">Resident story thread</p>
      <p>{{ residentStory?.headline || 'No resident story thread captured yet.' }}</p>
      <p v-if="residentStory">
        Shift score: {{ residentStory.shift_score }} |
        stress Δ {{ residentStory.signals?.stress_delta ?? 0 }} |
        service Δ {{ residentStory.signals?.service_delta ?? 0 }}
      </p>
      <p v-if="residentStory">Story systems: {{ summarizeSystems(residentStory.top_systems) }}</p>

      <template v-if="household">
        <p class="subhead">Household context</p>
        <p>Type: {{ household.household_type }} | Members: {{ household.member_ids?.length }}</p>
        <p>Income: ${{ household.monthly_income }} | Rent: ${{ household.monthly_rent }}</p>
        <p>Cost burden: {{ household.housing_cost_burden }} | Pressure: {{ household.pressure_level }}</p>
        <p>Eviction risk: {{ household.eviction_risk }} | Landlord id: {{ household.landlord_id || '—' }}</p>
        <p>Stress trend: {{ trendLabel(household.trajectory?.signals?.stress_trend) }}</p>
        <p>Housing stability trend: {{ trendLabel(household.trajectory?.signals?.housing_stability_trend) }}</p>
        <p>Employment stability trend: {{ trendLabel(household.trajectory?.signals?.employment_stability_trend) }}</p>
        <p>Service access trend: {{ trendLabel(household.trajectory?.signals?.service_access_trend) }}</p>
        <p>Household why: {{ household.derived_summary?.causal_readout?.why_changed?.[0] || 'No dominant household-level driver identified.' }}</p>
        <p>Household top systems: {{ summarizeSystems(household.derived_summary?.causal_readout?.top_system_contributors) }}</p>
        <p>Household social support: {{ household.social_context?.support_exposure ?? '—' }} | local strain: {{ household.social_context?.local_strain_index ?? '—' }}</p>
        <p>Household incoming social spillover: {{ household.derived_summary?.propagation_context?.incoming_social_stress ?? 0 }} | stress Δ: {{ household.derived_summary?.propagation_context?.stress_delta ?? 0 }}</p>
        <p>Household ripple sources: {{ summarizePropagationEdges(household.derived_summary?.propagation_context?.incoming_social_edges || [], 'household') }}</p>
        <p class="subhead">Household spatial context</p>
        <p>District anchor: {{ householdSpatialContext?.district_name || household.district_id }}</p>
        <p>Inside watched area: {{ householdSpatialContext?.inWatchedArea ? 'yes' : 'no' }} · District signal: {{ householdSpatialContext?.districtSignal || 'mixed' }}</p>
        <p>Intervention aftermath likely touches district: {{ householdSpatialContext?.aftermathTouchesDistrict ? 'yes' : 'no' }}</p>
        <p>Nearby service/institution relevance: {{ summarizeKinds(householdSpatialContext?.serviceContext?.relevantKinds) }}</p>
        <p>Nearby institutions (household-linked): {{ summarizeNearbyInstitutions(householdSpatialContext?.serviceContext?.nearbyInstitutions) }}</p>
        <p>Resident-household-district coherence: {{ coherenceSummary }}</p>
      </template>

      <template v-if="institutionContext.length">
        <p class="subhead">Institution context</p>
        <p v-for="inst in institutionContext" :key="inst.institution_id">
          {{ inst.institution_type }}: {{ inst.name }}
          (access {{ inst.access_score }}, pressure {{ inst.pressure_index }})
        </p>
      </template>
      <template v-if="institutionSpatialContext?.length">
        <p class="subhead">Institution spatial context + coherence</p>
        <p v-for="inst in institutionSpatialContext" :key="`spatial-${inst.institution_id}`">
          {{ inst.name }} ({{ inst.institution_type }}) · district {{ inst.district_name }} ·
          watched {{ inst.inWatchedArea ? 'yes' : 'no' }} · aftermath {{ inst.aftermathTouchesDistrict ? 'yes' : 'no' }} ·
          ecosystem {{ summarizeKinds(inst.ecosystem?.localKinds) }} · nearby {{ inst.ecosystem?.nearbyDistricts?.join(' / ') || '—' }} ·
          linked residents {{ inst.linkedResidentCount }} / households {{ inst.linkedHouseholdCount }}
        </p>
        <p>
          Coherence: resident-district aligned institutions {{ institutionCoherence?.residentDistrictInstitutionAlignment ?? 0 }}/{{ institutionCoherence?.institutionCount ?? 0 }} ·
          household-district aligned institutions {{ institutionCoherence?.householdDistrictInstitutionAlignment ?? 0 }}/{{ institutionCoherence?.institutionCount ?? 0 }} ·
          watched-area institution links {{ institutionCoherence?.watchedInstitutionCount ?? 0 }} ·
          aftermath-touch institution links {{ institutionCoherence?.aftermathInstitutionCount ?? 0 }}
        </p>
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
  formatEvidenceScoreLine,
  formatFocusSignalSet,
  formatNextCheckEvidenceLine,
  operatorSurfaceRoles,
} from '../../../lib/auralite/operatorFocusFormatting'

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
const operatorSelectedLine = computed(() => {
  const selected = props.operatorFocusReadback?.selected || {}
  const residentLabel = selected.resident_name ? `resident ${selected.resident_name}` : 'resident focus'
  const householdLabel = selected.household_id ? `household ${selected.household_id}` : 'no household anchor'
  const institutions = selected.institution_count ? `${selected.institution_count} institution links` : 'no institution links'
  return `${residentLabel} · ${householdLabel} · ${institutions}`
})
const operatorRelevanceLine = computed(() => {
  const relevance = props.operatorFocusReadback?.relevance || {}
  const district = (relevance.districtDrivers || []).slice(0, 1)
  const resident = (relevance.residentKinds || []).slice(0, 2)
  const household = (relevance.householdKinds || []).slice(0, 1)
  const institution = relevance.institutionLinks?.[0]?.label
  return [...district, ...resident, ...household, institution].filter(Boolean).join(' · ') || 'no linked relevance surfaced yet'
})
const focusExplainability = computed(() => props.operatorFocusReadback?.explainability || {})
const focusSignals = computed(() => formatFocusSignalSet(props.operatorFocusReadback?.priorities?.confidence || {}))
const focusStateLine = computed(() => {
  const signal = props.operatorFocusReadback?.coherence?.district_signal || props.residentSpatialContext?.districtSignal || 'mixed'
  const watch = toYesNo(props.operatorFocusReadback?.coherence?.district_watch ?? props.residentSpatialContext?.inWatchedArea)
  const aftermath = toYesNo(props.operatorFocusReadback?.coherence?.district_aftermath ?? props.residentSpatialContext?.aftermathTouchesDistrict)
  return `signal ${signal} · watch ${watch} · aftermath ${aftermath}`
})
const districtEvidenceLine = computed(() => formatEvidenceScoreLine(props.operatorFocusReadback?.priorities?.evidence?.district_driver || {}))
const residentEvidenceLine = computed(() => formatEvidenceScoreLine(props.operatorFocusReadback?.priorities?.evidence?.resident_household_relevance || {}))
const institutionEvidenceLine = computed(() => formatEvidenceScoreLine(props.operatorFocusReadback?.priorities?.evidence?.institution_link || {}))
const nextCheckEvidenceLine = computed(() => formatNextCheckEvidenceLine(props.operatorFocusReadback?.priorities?.evidence || {}))
const toYesNo = (value) => (value ? 'yes' : 'no')
const trendLabel = (trend) => {
  if (!trend) return '—'
  return `${trend.direction} (now ${trend.current}, Δ ${trend.delta})`
}
const summarizeSystems = (systems = []) => {
  if (!systems?.length) return '—'
  return systems.slice(0, 3).map((entry) => `${entry.system} (${entry.score})`).join(', ')
}
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
