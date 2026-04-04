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

      <p class="subhead">Evolution hook</p>
      <p>{{ district.derived_summary?.evolution_hook?.risk ?? 'stable' }} ({{ district.derived_summary?.evolution_hook?.next_update_window ?? 'weekly' }})</p>
    </div>
    <p v-else>Select a district</p>
  </div>
</template>
<script setup>
defineProps({ district: Object })
</script>
<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
p{margin:4px 0}
.subhead{margin-top:8px;font-weight:700}
.driver-list{margin:6px 0 0;padding-left:18px}
</style>
