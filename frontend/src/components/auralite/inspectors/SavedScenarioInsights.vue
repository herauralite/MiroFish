<template>
  <div class="panel">
    <h3>Scenario History + Saved Insights</h3>

    <div class="filters">
      <select v-model="activeSourceType">
        <option value="">All sources</option>
        <option v-for="row in sourceTypeOptions" :key="row" :value="row">{{ row }}</option>
      </select>
      <select v-model="activeDirection">
        <option value="">All directions</option>
        <option v-for="row in directionOptions" :key="row" :value="row">{{ row }}</option>
      </select>
      <select v-model="activeScenarioName">
        <option value="">All scenarios</option>
        <option v-for="row in scenarioOptions" :key="row" :value="row">{{ row }}</option>
      </select>
    </div>

    <div class="timeline">
      <h4>Recent scenario moments</h4>
      <p class="hint" v-if="!recentTimeline.length">No scenario moments recorded yet.</p>
      <ul v-else class="list compact">
        <li v-for="item in recentTimeline" :key="item.moment_id">
          <div class="row"><strong>#{{ item.order || '—' }}</strong> · {{ item.moment_type }} · {{ item.world_time || '—' }}</div>
          <div class="row">{{ item.scenario_name || 'default-baseline' }} · {{ item.source_type || 'system' }}</div>
        </li>
      </ul>
    </div>

    <h4>Saved insight cards</h4>
    <p class="hint" v-if="!filteredInsights.length">No saved scenario insights match filters.</p>
    <ul v-else class="list">
      <li v-for="item in filteredInsights" :key="item.insight_id">
        <div class="row"><strong>#{{ item.timeline_order || '—' }}</strong> · <strong>{{ item.scenario_name }}</strong> · {{ item.world_time || '—' }}</div>
        <div class="row">{{ item.source_type || item.source }} · {{ item.direction || item.condition_direction }}</div>
        <div class="row">{{ item.what_happened }}</div>
        <div class="row">districts: {{ summarizeDistricts(item.districts_that_mattered) }}</div>
        <div class="row">systems: {{ summarizeSystems(item.systems_that_mattered) }}</div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  insights: { type: Array, default: () => [] },
  timeline: { type: Array, default: () => [] },
  filterCatalog: { type: Object, default: () => ({}) },
})

const activeSourceType = ref('')
const activeDirection = ref('')
const activeScenarioName = ref('')

const sourceTypeOptions = computed(() => props.filterCatalog?.source_types || [])
const directionOptions = computed(() => props.filterCatalog?.directions || [])
const scenarioOptions = computed(() => props.filterCatalog?.scenario_names || [])

const recentTimeline = computed(() => [...props.timeline].reverse().slice(0, 8))
const filteredInsights = computed(() => [...props.insights]
  .filter((item) => !activeSourceType.value || (item.source_type || 'system') === activeSourceType.value)
  .filter((item) => !activeDirection.value || (item.direction || item.condition_direction || 'flat') === activeDirection.value)
  .filter((item) => !activeScenarioName.value || (item.scenario_name || 'default-baseline') === activeScenarioName.value)
  .reverse()
  .slice(0, 8))

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
.filters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-bottom:8px}
.filters select{font-size:12px;padding:4px}
.timeline{border-top:1px solid #ececec;border-bottom:1px solid #ececec;padding:6px 0;margin:8px 0}
.timeline h4,.panel h4{margin:4px 0;font-size:12px}
.hint{font-size:12px;color:#666}
.list{list-style:none;padding:0;margin:8px 0;display:flex;flex-direction:column;gap:8px}
.list li{border:1px solid #ececec;padding:8px;background:#fafafa}
.list.compact li{padding:6px}
.row{font-size:12px;margin:2px 0}
</style>
