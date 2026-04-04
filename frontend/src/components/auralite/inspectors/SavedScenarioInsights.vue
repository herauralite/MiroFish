<template>
  <div class="panel">
    <h3>Saved Scenario Insights</h3>
    <p class="hint" v-if="!insights.length">No saved scenario insights yet.</p>
    <ul v-else class="list">
      <li v-for="item in recentInsights" :key="item.insight_id">
        <div class="row"><strong>{{ item.scenario_name }}</strong> · {{ item.world_time || '—' }}</div>
        <div class="row">{{ item.source }} · {{ item.condition_direction }}</div>
        <div class="row">{{ item.what_happened }}</div>
        <div class="row">districts: {{ summarizeDistricts(item.districts_that_mattered) }}</div>
        <div class="row">systems: {{ summarizeSystems(item.systems_that_mattered) }}</div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  insights: { type: Array, default: () => [] },
})

const recentInsights = computed(() => [...props.insights].reverse().slice(0, 6))

const summarizeDistricts = (rows = []) => {
  if (!rows.length) return '—'
  return rows.slice(0, 3).map((row) => `${row.name || row.district_id} (${Number(row.shift_score || 0).toFixed(3)})`).join(', ')
}

const summarizeSystems = (rows = []) => {
  if (!rows.length) return '—'
  return rows.slice(0, 3).map((row) => `${row.system} (${Number(row.score || 0).toFixed(3)})`).join(', ')
}
</script>

<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
.hint{font-size:12px;color:#666}
.list{list-style:none;padding:0;margin:8px 0;display:flex;flex-direction:column;gap:8px}
.list li{border:1px solid #ececec;padding:8px;background:#fafafa}
.row{font-size:12px;margin:2px 0}
</style>
