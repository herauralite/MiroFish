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
      <p class="subhead">Derived summary</p>
      <p>Active workers: {{ district.derived_summary?.active_workers ?? '—' }}</p>
      <p>Household pressure: {{ district.derived_summary?.household_pressure_index ?? '—' }}</p>
      <p>Evolution hook: {{ district.derived_summary?.evolution_hook?.risk ?? 'stable' }} ({{ district.derived_summary?.evolution_hook?.next_update_window ?? 'weekly' }})</p>
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
</style>
