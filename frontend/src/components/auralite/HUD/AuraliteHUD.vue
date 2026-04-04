<template>
  <div class="hud">
    <div>
      <h2>Auralite — {{ city?.name }}</h2>
      <p>{{ world?.current_time }} | residents: {{ city?.population_count }}</p>
    </div>
    <TimeControls
      :speed="world?.time_speed || 1"
      @start="$emit('start')"
      @pause="$emit('pause')"
      @tick="$emit('tick')"
      @speed="$emit('speed', $event)"
    />
  </div>
</template>

<script setup>
import TimeControls from './TimeControls.vue'
defineProps({ city: Object, world: Object })
defineEmits(['start', 'pause', 'tick', 'speed'])
</script>

<style scoped>
.hud{display:flex;justify-content:space-between;background:#111;color:#f2f2f2;padding:10px 12px;border:1px solid #333}
p{margin:0;font-size:12px}
h2{margin:0 0 4px 0;font-size:18px}
</style>
