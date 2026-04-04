<template>
  <div class="panel">
    <h3>District Inspector</h3>
    <div v-if="district">
      <p><strong>{{ district.name }}</strong></p>
      <p>{{ district.summary }}</p>
      <p>Archetype: {{ district.archetype }}</p>
      <p>Population: {{ district.population_count }}</p>
      <p>Activity: {{ district.current_activity_level }}</p>
    </div>
    <p v-else>Select a district</p>
  </div>
</template>
<script setup>
defineProps({ district: Object })
</script>
<style scoped>.panel{border:1px solid #ddd;padding:10px;background:#fff}</style>
