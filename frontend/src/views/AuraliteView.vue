<template>
  <div class="auralite-view">
    <AuraliteHUD :city="world.city" :world="world.world" @start="start" @pause="pause" @tick="tick" @speed="speed" />
    <div class="layout">
      <AuraliteMap
        :districts="world.districts || []"
        :resident-markers="residentMarkers"
        :selected-district-id="selectedDistrictId"
        @select-district="selectDistrict"
        @select-resident="selectResident"
      />
      <div class="inspectors">
        <DistrictInspector :district="selectedDistrict" />
        <ResidentInspector :resident="selectedResident" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import AuraliteHUD from '../components/auralite/HUD/AuraliteHUD.vue'
import AuraliteMap from '../components/auralite/map/AuraliteMap.vue'
import DistrictInspector from '../components/auralite/inspectors/DistrictInspector.vue'
import ResidentInspector from '../components/auralite/inspectors/ResidentInspector.vue'
import { controlAuraliteRuntime, getAuraliteWorld, tickAuraliteRuntime } from '../lib/auralite/api'

const world = ref({})
const selectedDistrictId = ref('')
const selectedResidentId = ref('')
let timer = null

const loadWorld = async () => {
  const res = await getAuraliteWorld()
  world.value = res.data
  if (!selectedDistrictId.value && world.value.districts?.length) {
    selectedDistrictId.value = world.value.districts[0].district_id
  }
}

const residentMarkers = computed(() => {
  const byLoc = new Map((world.value.locations || []).map((l) => [l.location_id, l]))
  const simMinute = new Date(world.value.world?.current_time || Date.now()).getMinutes()
  return (world.value.persons || []).map((p, idx) => {
    const loc = byLoc.get(p.current_location_id)
    const j = ((idx + simMinute) % 7) / 25
    return { person_id: p.person_id, x: (loc?.x || 0) * 10 + 10 + j, y: (loc?.y || 0) * 10 + 10 + j }
  })
})

const selectedDistrict = computed(() => (world.value.districts || []).find((d) => d.district_id === selectedDistrictId.value))
const selectedResident = computed(() => (world.value.persons || []).find((p) => p.person_id === selectedResidentId.value))

const selectDistrict = (id) => { selectedDistrictId.value = id }
const selectResident = (id) => { selectedResidentId.value = id }

const start = async () => { await controlAuraliteRuntime({ action: 'start' }); await loadWorld() }
const pause = async () => { await controlAuraliteRuntime({ action: 'pause' }); await loadWorld() }
const speed = async (value) => { await controlAuraliteRuntime({ action: 'speed', time_speed: value }); await loadWorld() }
const tick = async () => { await tickAuraliteRuntime({ minutes: 15 }); await loadWorld() }

onMounted(async () => {
  await loadWorld()
  timer = setInterval(loadWorld, 3000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.auralite-view{padding:12px;background:#f0f2f4;min-height:100vh}
.layout{display:grid;grid-template-columns: 1fr 320px;gap:12px;margin-top:12px}
.inspectors{display:flex;flex-direction:column;gap:12px}
</style>
