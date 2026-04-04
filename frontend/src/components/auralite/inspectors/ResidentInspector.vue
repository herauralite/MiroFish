<template>
  <div class="panel">
    <h3>Resident</h3>
    <div v-if="resident">
      <p><strong>{{ resident.name }}</strong> ({{ resident.age }})</p>
      <p>{{ resident.occupation }} | {{ resident.current_activity }}</p>
      <p>Household: {{ resident.household_id }}</p>
      <p>Routine: {{ resident.routine_type }}</p>
      <p>Mood: {{ resident.state_summary?.mood }}</p>
    </div>
    <p v-else>Select a resident marker</p>
  </div>
</template>
<script setup>
defineProps({ resident: Object })
</script>
<style scoped>.panel{border:1px solid #ddd;padding:10px;background:#fff}</style>
