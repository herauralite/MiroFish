<template>
  <div class="panel">
    <h3>Intervention Console (Light)</h3>
    <p class="hint">Dev-facing panel backed by backend intervention APIs.</p>

    <label>Scenario Name</label>
    <div class="row">
      <input v-model="scenarioName" type="text" placeholder="e.g. transit-resilience-pass" />
      <button @click="saveScenarioName">Set</button>
    </div>

    <label>District</label>
    <select v-model="selectedDistrict">
      <option v-for="district in districts" :key="district.district_id" :value="district.district_id">{{ district.name }}</option>
    </select>

    <label>Lever</label>
    <select v-model="selectedLever">
      <option v-for="lever in availableLevers" :key="lever" :value="lever">{{ lever }}</option>
    </select>

    <label>Intensity: {{ intensity.toFixed(2) }}</label>
    <input v-model.number="intensity" type="range" min="0.05" max="1" step="0.05" />

    <div class="row actions">
      <button @click="$emit('capture-baseline')">Capture Baseline</button>
      <button class="apply" @click="apply" :disabled="!selectedDistrict || !selectedLever">Apply Intervention</button>
    </div>

    <p v-if="lastApplied" class="last">Last apply: {{ lastApplied }}</p>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  districts: { type: Array, default: () => [] },
  availableLevers: { type: Array, default: () => [] },
  activeScenarioName: { type: String, default: 'default-baseline' },
  lastApplied: { type: String, default: '' },
})

const emit = defineEmits(['apply', 'capture-baseline', 'set-scenario'])

const selectedDistrict = ref('')
const selectedLever = ref('')
const intensity = ref(0.25)
const scenarioName = ref(props.activeScenarioName)

watch(() => props.activeScenarioName, (next) => {
  scenarioName.value = next || 'default-baseline'
})

watch(() => props.districts, (districts) => {
  if (!selectedDistrict.value && districts?.length) {
    selectedDistrict.value = districts[0].district_id
  }
}, { immediate: true })

watch(() => props.availableLevers, (levers) => {
  if (!selectedLever.value && levers?.length) {
    selectedLever.value = levers[0]
  }
}, { immediate: true })

const apply = () => {
  emit('apply', {
    district_id: selectedDistrict.value,
    lever: selectedLever.value,
    intensity: intensity.value,
  })
}

const saveScenarioName = () => {
  emit('set-scenario', scenarioName.value)
}

const availableLevers = computed(() => props.availableLevers || [])
</script>

<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
label{display:block;font-weight:700;font-size:12px;margin-top:8px}
input,select{width:100%;padding:6px;border:1px solid #ccc;border-radius:4px;margin-top:4px}
.row{display:flex;gap:8px;align-items:center}
button{padding:6px 10px;border:1px solid #222;background:#f6f6f6;cursor:pointer}
button.apply{background:#1f6feb;color:#fff;border-color:#1f6feb}
button:disabled{opacity:.5;cursor:not-allowed}
.actions{margin-top:10px}
.hint{font-size:12px;color:#666;margin:2px 0 6px}
.last{font-size:12px;color:#444;margin-top:8px}
</style>
