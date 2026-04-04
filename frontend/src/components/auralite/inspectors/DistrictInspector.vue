<template>
  <div class="panel">
    <h3>District Inspector</h3>
    <div v-if="district">
      <p><strong>{{ district.name }}</strong> · {{ district.state_phase }}</p>
      <p>{{ district.summary }}</p>
      <p class="subhead">Summary first</p>
      <p><strong>Local anchor:</strong> {{ districtAnchorLine }}</p>
      <p><strong>Local state:</strong> {{ districtStateLine }}</p>
      <p class="operator-priority"><strong>Action cue:</strong> {{ districtActionLine }}</p>
      <p><strong>Scope:</strong> {{ districtScopeLine }}</p>
      <p><strong>Why now:</strong> {{ districtWhyNowLine }}</p>
      <p><strong>Local evidence:</strong> {{ districtEvidenceLine }}</p>
      <p><strong>Nearby context:</strong> {{ districtNearbyContextLine }}</p>
      <p><strong>Pressure/phase:</strong> {{ pressurePhaseSummaryLine }}</p>

      <p class="subhead">Secondary context</p>
      <p><strong>District profile:</strong> archetype {{ district.archetype }} · population {{ district.population_count }} · activity {{ district.current_activity_level }}</p>
      <p><strong>Service/institution context:</strong> {{ serviceInstitutionContextLine }}</p>
      <p><strong>Watch/aftermath/ripple:</strong> {{ watchAftermathRippleLine }}</p>
      <p><strong>Story thread:</strong> {{ districtStory?.headline || 'No district story thread captured yet.' }}</p>
      <p v-if="districtStory">Shift {{ districtStory.shift_score }} · phase {{ districtStory.state_phase }} · systems {{ summarizeStorySystems(districtStory.top_systems) }}</p>

      <p class="subhead">Deeper diagnostics</p>
      <p><strong>Causal readout:</strong> {{ causalReadoutLine }}</p>
      <p><strong>Top systems:</strong> {{ topSystems }}</p>
      <p><strong>Pressure decomposition:</strong> hh {{ district.household_pressure }} · employment {{ district.employment_pressure }} · service {{ district.service_access_score }} · transit {{ district.transit_reliability }}</p>
      <p><strong>Institution scaffolding:</strong> {{ institutionScaffoldLine }}</p>
      <p class="subhead">Operator check next</p>
      <ul class="driver-list">
        <li v-for="(check, idx) in (spatialContext?.checkNext || [])" :key="`check-${idx}`">{{ check }}</li>
        <li v-if="!(spatialContext?.checkNext || []).length">Continue district watchlist monitoring.</li>
      </ul>
      <ul class="driver-list">
        <li v-for="(driver, index) in district.derived_summary?.pressure_drivers || []" :key="index">{{ driver }}</li>
      </ul>
      <p>Resident stress index: {{ district.derived_summary?.resident_stress_index ?? '—' }}</p>
      <p class="subhead">Evolution hook</p>
      <p>{{ district.derived_summary?.evolution_hook?.risk ?? 'stable' }} ({{ district.derived_summary?.evolution_hook?.next_update_window ?? 'weekly' }})</p>
      <p class="subhead">Recent intervention effect hook</p>
      <p>
        World Δ hh pressure: {{ comparisonSummary?.household_pressure_index ?? 0 }} |
        Δ service access: {{ comparisonSummary?.service_access_score ?? 0 }} |
        Δ stressed districts: {{ comparisonSummary?.stressed_districts ?? 0 }}
      </p>
      <p v-if="districtShift">
        District Δ pressure: {{ districtShift.pressure_delta }} |
        Δ service: {{ districtShift.service_access_delta }} |
        phase: {{ districtShift.phase_before }} → {{ districtShift.phase_after }}
      </p>
      <ul class="driver-list" v-if="districtShift?.causal_notes?.length">
        <li v-for="(note, idx) in districtShift.causal_notes" :key="`cause-${idx}`">{{ note }}</li>
      </ul>
    </div>
    <p v-else>Select a district</p>
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
  formatScenarioScopeLine,
} from '../../../lib/auralite/operatorFocusFormatting'

const props = defineProps({
  district: Object,
  spatialContext: Object,
  comparisonSummary: Object,
  latestDistrictShifts: { type: Array, default: () => [] },
  districtStoryThreads: { type: Array, default: () => [] },
  operatorFocusReadback: { type: Object, default: null },
})

const districtShift = computed(() =>
  props.latestDistrictShifts.find((shift) => shift.district_id === props.district?.district_id),
)

const topSystems = computed(() =>
  (props.district?.derived_summary?.causal_readout?.top_system_contributors || [])
    .slice(0, 3)
    .map((item) => `${item.system} (${item.score})`)
    .join(', ') || '—',
)
const districtStory = computed(() =>
  (props.districtStoryThreads || []).find((thread) => thread.district_id === props.district?.district_id),
)
const districtAnchorLine = computed(() => formatLocalAnchorLine({
  district: props.district?.name || props.district?.district_id || 'unscoped district',
  location: props.district?.map_region_key || 'district region anchor',
  subject: props.district?.district_id ? `district ${props.district.district_id}` : 'district —',
}, 96))
const districtStateLine = computed(() => formatFocusStateLine({
  signal: props.spatialContext?.signal || 'mixed',
  watch: props.spatialContext?.watched,
  aftermath: props.spatialContext?.aftermathPresent,
}))
const districtActionLine = computed(() => formatLocalActionCueLine({
  driver: props.spatialContext?.whyHot?.[0] || props.spatialContext?.topWatchReason || 'No dominant local pressure driver yet.',
  nextCheck: props.operatorFocusReadback?.priorities?.nextCheck?.what || 'Continue district watchlist monitoring.',
}, 108))
const districtScopeLine = computed(() => formatScenarioScopeLine({
  resident: props.district?.district_id ? `district ${props.district.district_id}` : props.district?.name || '—',
  institution: summarizeServiceKinds(props.spatialContext?.serviceContext?.serviceKinds || []),
}))
const districtWhyNowLine = computed(() => formatCompactWhyLine(
  props.spatialContext?.topWatchReason
  || props.district?.derived_summary?.causal_readout?.why_changed?.[0]
  || 'Immediate district follow-up reason is still forming.',
))
const districtEvidenceLine = computed(() => formatEvidenceBundleLine(props.operatorFocusReadback?.priorities?.evidence || {}))
const districtNearbyContextLine = computed(() => formatLocalNearbyContextLine({
  district: props.district?.name || props.district?.district_id || 'unscoped district',
  service: summarizeServiceKinds(props.spatialContext?.serviceContext?.serviceKinds || []),
  nearby: summarizeNearbyDistricts(props.spatialContext?.serviceContext?.nearbyDistricts || []),
}, 132))
const pressurePhaseSummaryLine = computed(() => (
  `pressure ${props.district?.pressure_index ?? 0} · phase ${props.district?.state_phase || 'n/a'} · `
  + `employment ${props.district?.employment_rate ?? 0} · housing burden ${props.district?.average_housing_burden ?? 0}`
))
const serviceInstitutionContextLine = computed(() => (
  `services ${summarizeServiceKinds(props.spatialContext?.serviceContext?.serviceKinds || [])} · `
  + `channels ${summarizeServiceKinds(props.spatialContext?.serviceContext?.locationSupport || [])} · `
  + `footprint ${props.spatialContext?.serviceContext?.institutionCount ?? 0} · `
  + `avg pressure ${props.spatialContext?.serviceContext?.averageInstitutionPressure ?? 0}`
))
const watchAftermathRippleLine = computed(() => (
  `watch ${props.spatialContext?.watched ? 'yes' : 'no'}`
  + `${props.spatialContext?.watchUrgency ? ` (${props.spatialContext.watchUrgency})` : ''} · `
  + `aftermath ${props.spatialContext?.aftermathPresent ? 'yes' : 'no'} · `
  + `signal ${props.spatialContext?.signal || 'mixed'} · `
  + `neighbor pressure ${props.district?.derived_summary?.ripple_context?.neighbor_pressure ?? '—'} · `
  + `ripple ${props.district?.derived_summary?.ripple_context?.ripple_effect ?? '—'}`
))
const causalReadoutLine = computed(() => (
  `${props.district?.derived_summary?.causal_readout?.what_changed?.pressure_index ?? 0} pressure, `
  + `${props.district?.derived_summary?.causal_readout?.what_changed?.service_access_score ?? 0} service, `
  + `${props.district?.derived_summary?.causal_readout?.what_changed?.employment_rate ?? 0} employment · `
  + `phase ${props.district?.derived_summary?.causal_readout?.what_changed?.state_phase || 'n/a'} · `
  + `why ${props.district?.derived_summary?.causal_readout?.why_changed?.[0] || 'No dominant local driver identified yet.'}`
))
const institutionScaffoldLine = computed(() => (
  `employers ${props.district?.institution_summary?.employers ?? '—'} · `
  + `landlords ${props.district?.institution_summary?.landlords ?? '—'} · `
  + `transit ${props.district?.institution_summary?.transit_services ?? '—'} · `
  + `care/service ${props.district?.institution_summary?.care_services ?? '—'} · `
  + `stress ${props.district?.institution_summary?.institution_stress ?? '—'}`
))

const summarizeStorySystems = (systems = []) => {
  if (!systems?.length) return '—'
  return systems.slice(0, 3).map((entry) => `${entry.system} (${entry.score})`).join(', ')
}
const summarizeServiceKinds = (kinds = []) => {
  if (!kinds?.length) return '—'
  return [...new Set(kinds)].slice(0, 3).join(', ')
}
const summarizeNearbyDistricts = (districts = []) => {
  if (!districts?.length) return '—'
  return districts.slice(0, 3).map((row) => row.name).join(' · ')
}
</script>
<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
p{margin:4px 0}
.subhead{margin-top:8px;font-weight:700}
.driver-list{margin:6px 0 0;padding-left:18px}
</style>
