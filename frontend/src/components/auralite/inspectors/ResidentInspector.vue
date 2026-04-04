<template>
  <div class="panel">
    <h3>Resident</h3>
    <div v-if="resident">
      <p><strong>{{ resident.name }}</strong> ({{ resident.age }})</p>
      <p>{{ resident.occupation }} | {{ resident.current_activity }}</p>
      <p>Status: {{ resident.employment_status }} · Shift: {{ resident.shift_window }}</p>
      <p>Routine: {{ resident.routine_type }} | Wage: ${{ resident.hourly_wage }}/hr</p>
      <p>Housing burden share: {{ resident.housing_burden_share }} | Mood: {{ resident.state_summary?.mood }}</p>
      <p>Stress: {{ resident.state_summary?.stress }}</p>

      <template v-if="household">
        <p class="subhead">Household context</p>
        <p>Type: {{ household.household_type }} | Members: {{ household.member_ids?.length }}</p>
        <p>Income: ${{ household.monthly_income }} | Rent: ${{ household.monthly_rent }}</p>
        <p>Cost burden: {{ household.housing_cost_burden }} | Pressure: {{ household.pressure_level }}</p>
      </template>
    </div>
    <p v-else>Select a resident marker</p>
  </div>
</template>
<script setup>
defineProps({ resident: Object, household: Object })
</script>
<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
p{margin:4px 0}
.subhead{margin-top:8px;font-weight:700}
</style>
