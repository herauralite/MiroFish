<template>
  <div class="panel">
    <h3>District Inspector</h3>
    <div v-if="district">
      <p><strong>{{ district.name }}</strong> · {{ district.state_phase }}</p>
      <p>{{ district.summary }}</p>
      <p>Archetype: {{ district.archetype }}</p>
      <p>Population: {{ district.population_count }} | Activity: {{ district.current_activity_level }}</p>
      <p>Pressure: {{ district.pressure_index }} | Employment: {{ district.employment_rate }}</p>
      <p>Avg wage: ${{ district.average_hourly_wage }}/hr | Housing burden: {{ district.average_housing_burden }}</p>

      <p class="subhead">Causal readout</p>
      <p>What changed: {{ district.derived_summary?.causal_readout?.what_changed?.pressure_index ?? 0 }} pressure, {{ district.derived_summary?.causal_readout?.what_changed?.service_access_score ?? 0 }} service, {{ district.derived_summary?.causal_readout?.what_changed?.employment_rate ?? 0 }} employment</p>
      <p>Phase transition: {{ district.derived_summary?.causal_readout?.what_changed?.state_phase || 'n/a' }}</p>
      <p>Why: {{ district.derived_summary?.causal_readout?.why_changed?.[0] || 'No dominant local driver identified yet.' }}</p>
      <p>Top systems: {{ topSystems }}</p>

      <p class="subhead">Pressure decomposition</p>
      <p>Household pressure: {{ district.household_pressure }}</p>
      <p>Employment pressure: {{ district.employment_pressure }}</p>
      <p>Service access: {{ district.service_access_score }} | Transit reliability: {{ district.transit_reliability }}</p>
      <ul class="driver-list">
        <li v-for="(driver, index) in district.derived_summary?.pressure_drivers || []" :key="index">{{ driver }}</li>
      </ul>

      <p class="subhead">Institution scaffolding</p>
      <p>Employers: {{ district.institution_summary?.employers ?? '—' }} | Landlords: {{ district.institution_summary?.landlords ?? '—' }}</p>
      <p>Transit services: {{ district.institution_summary?.transit_services ?? '—' }} | Care/service nodes: {{ district.institution_summary?.care_services ?? '—' }}</p>
      <p>Institution stress: {{ district.institution_summary?.institution_stress ?? '—' }} | Capacity: {{ district.institution_summary?.service_capacity ?? '—' }}</p>
      <p>
        Employer pressure: {{ district.institution_summary?.employer_pressure ?? '—' }} |
        Landlord pressure: {{ district.institution_summary?.landlord_pressure ?? '—' }} |
        Transit pressure: {{ district.institution_summary?.transit_pressure ?? '—' }}
      </p>
      <p>Resident stress index: {{ district.derived_summary?.resident_stress_index ?? '—' }}</p>

      <p class="subhead">Ripple context</p>
      <p>
        Neighbor pressure: {{ district.derived_summary?.ripple_context?.neighbor_pressure ?? '—' }} |
        Local gap: {{ district.derived_summary?.ripple_context?.pressure_gap ?? '—' }} |
        Ripple effect: {{ district.derived_summary?.ripple_context?.ripple_effect ?? '—' }}
      </p>
      <p>
        Incoming neighbor pressure: {{ district.derived_summary?.propagation_context?.incoming_neighbor_pressure ?? 0 }} |
        Recent incoming events: {{ district.derived_summary?.propagation_context?.recent_neighbor_event_count ?? 0 }}
      </p>
      <p>Neighbor sources: {{ summarizeNeighborSources(district.derived_summary?.propagation_context?.incoming_sources || []) }}</p>

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

const props = defineProps({
  district: Object,
  comparisonSummary: Object,
  latestDistrictShifts: { type: Array, default: () => [] },
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

const summarizeNeighborSources = (sources = []) => {
  if (!sources?.length) return '—'
  return sources.slice(0, 4).map((source) => `${source.from} (${source.impact_pressure})`).join(' · ')
}
</script>
<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
p{margin:4px 0}
.subhead{margin-top:8px;font-weight:700}
.driver-list{margin:6px 0 0;padding-left:18px}
</style>
