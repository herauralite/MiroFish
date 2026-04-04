<template>
  <div class="hud">
    <div>
      <h2>Auralite — {{ city?.name }}</h2>
      <p>{{ world?.current_time }} | residents: {{ city?.population_count }} | speed: {{ world?.time_speed }}x</p>
      <p>
        emp: {{ city?.world_metrics?.employment_rate ?? '—' }} |
        wage: ${{ city?.world_metrics?.avg_hourly_wage ?? '—' }}/hr |
        burden: {{ city?.world_metrics?.avg_housing_burden ?? '—' }} |
        hh pressure: {{ city?.world_metrics?.household_pressure_index ?? '—' }}
      </p>
      <p>
        stressed districts: {{ city?.world_metrics?.district_state_overview?.stressed ?? 0 }} |
        stabilizing: {{ city?.world_metrics?.district_state_overview?.stabilizing ?? 0 }}
      </p>
      <p v-if="lastSnapshotId" class="snapshot">Snapshot: {{ lastSnapshotId }}</p>
    </div>
    <TimeControls
      :speed="world?.time_speed || 1"
      @start="$emit('start')"
      @pause="$emit('pause')"
      @tick="$emit('tick')"
      @speed="$emit('speed', $event)"
      @save="$emit('save')"
      @load="$emit('load')"
    />
  </div>
</template>

<script setup>
import TimeControls from './TimeControls.vue'
defineProps({ city: Object, world: Object, lastSnapshotId: String })
defineEmits(['start', 'pause', 'tick', 'speed', 'save', 'load'])
</script>

<style scoped>
.hud{display:flex;justify-content:space-between;background:#111;color:#f2f2f2;padding:10px 12px;border:1px solid #333}
p{margin:0;font-size:12px}
h2{margin:0 0 4px 0;font-size:18px}
.snapshot{color:#8de1ff}
</style>
