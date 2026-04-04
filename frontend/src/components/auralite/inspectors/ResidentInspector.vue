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
      </template>

      <template v-if="institutionContext.length">
        <p class="subhead">Institution context</p>
        <p v-for="inst in institutionContext" :key="inst.institution_id">
          {{ inst.institution_type }}: {{ inst.name }}
          (access {{ inst.access_score }}, pressure {{ inst.pressure_index }})
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

const props = defineProps({ resident: Object, household: Object, institutions: Array, socialTies: Array, socialGraph: Object })

const institutionContext = computed(() => (props.institutions || []).filter(Boolean))
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
</script>
<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
p{margin:4px 0}
.subhead{margin-top:8px;font-weight:700}
</style>
