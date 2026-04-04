<template>
  <div class="map-wrap">
    <svg viewBox="0 0 100 100" class="map">
      <defs>
        <pattern id="district-hatch" width="2" height="2" patternUnits="userSpaceOnUse">
          <path d="M0,0 L2,2" stroke="#ffffff" stroke-width="0.12" opacity="0.28" />
        </pattern>
      </defs>

      <rect x="0" y="0" width="100" height="100" fill="#3a5a28" />

      <rect
        v-for="(road, idx) in arterialRoads"
        :key="`arterial-${idx}`"
        :x="road.x"
        :y="road.y"
        :width="road.width"
        :height="road.height"
        fill="#4a4a4a"
      />
      <rect
        v-for="(road, idx) in collectorRoads"
        :key="`collector-${idx}`"
        :x="road.x"
        :y="road.y"
        :width="road.width"
        :height="road.height"
        fill="#5d5d5d"
        opacity="0.85"
      />

      <rect
        v-for="(walk, idx) in sidewalks"
        :key="`walk-${idx}`"
        :x="walk.x"
        :y="walk.y"
        :width="walk.width"
        :height="walk.height"
        fill="#c7c1aa"
        opacity="0.45"
      />

      <path
        v-for="(stripe, idx) in laneStripes"
        :key="`lane-${idx}`"
        :d="stripe"
        stroke="#f7e587"
        stroke-width="0.35"
        stroke-dasharray="2.4,1.8"
        opacity="0.72"
      />

      <rect
        v-for="(feature, idx) in waterFeatures"
        :key="`water-${idx}`"
        :x="feature.x"
        :y="feature.y"
        :width="feature.width"
        :height="feature.height"
        :rx="feature.radius"
        fill="#2f85b3"
        opacity="0.88"
      />

      <circle
        v-for="(park, idx) in greenSpaces"
        :key="`park-${idx}`"
        :cx="park.cx"
        :cy="park.cy"
        :r="park.r"
        fill="#58aa38"
      />

      <rect
        v-for="(block, idx) in urbanBlocks"
        :key="`block-${idx}`"
        :x="block.x"
        :y="block.y"
        :width="block.width"
        :height="block.height"
        :fill="block.fill"
        rx="0.6"
      />

      <circle
        v-for="(dot, idx) in districtTextureDots"
        :key="`texture-${idx}`"
        :cx="dot.x"
        :cy="dot.y"
        r="0.26"
        fill="#e7e4d8"
        opacity="0.45"
      />

      <g v-for="district in districts" :key="district.district_id">
        <path
          v-if="shapeFor(district.map_region_key)"
          :d="shapeFor(district.map_region_key).path"
          :fill="districtFill(district)"
          stroke="#24323d"
          :stroke-width="hoveredDistrictId === district.district_id ? 0.7 : 0.45"
          :opacity="districtOpacity(district)"
          @mouseenter="hoveredDistrictId = district.district_id"
          @mouseleave="hoveredDistrictId = ''"
          @click="$emit('select-district', district.district_id)"
        />
        <path
          v-if="shapeFor(district.map_region_key)"
          :d="shapeFor(district.map_region_key).path"
          fill="url(#district-hatch)"
          opacity="0.28"
        />

        <circle
          v-if="districtSignal(district.district_id)?.watch"
          :cx="shapeFor(district.map_region_key).label.x"
          :cy="shapeFor(district.map_region_key).label.y"
          r="3"
          fill="none"
          stroke="#ffd166"
          stroke-width="0.38"
          stroke-dasharray="1.2,0.9"
          opacity="0.9"
        />

        <circle
          v-if="districtSignal(district.district_id)?.aftermath"
          :cx="shapeFor(district.map_region_key).label.x"
          :cy="shapeFor(district.map_region_key).label.y"
          r="4.1"
          fill="none"
          stroke="#7cd992"
          stroke-width="0.33"
          opacity="0.7"
        />

        <text
          v-if="shapeFor(district.map_region_key)"
          :x="shapeFor(district.map_region_key).label.x"
          :y="shapeFor(district.map_region_key).label.y"
          font-size="1.9"
          :fill="districtTextColor(district)"
          text-anchor="middle"
          font-weight="700"
        >{{ district.name }}</text>
      </g>

      <circle
        v-for="row in pressureHaloes"
        :key="`pressure-${row.district_id}`"
        :cx="row.x"
        :cy="row.y"
        :r="row.radius"
        fill="none"
        :stroke="row.stroke"
        stroke-width="0.32"
        opacity="0.7"
      />

      <g v-for="service in serviceLandmarks" :key="service.id">
        <rect
          :x="service.x - 0.6"
          :y="service.y - 0.6"
          :width="serviceSize(service)"
          :height="serviceSize(service)"
          :fill="serviceColor(service.kind)"
          :opacity="serviceOpacity(service)"
          @mouseenter="hoveredServiceId = service.id"
          @mouseleave="hoveredServiceId = ''"
          rx="0.2"
        />
        <title>{{ service.kind }}</title>
      </g>

      <circle
        v-for="resident in residentMarkers"
        :key="resident.person_id"
        :cx="resident.x"
        :cy="resident.y"
        :r="spatialReadback?.watchResidentIds?.includes(resident.person_id) ? 0.52 : 0.42"
        :fill="spatialReadback?.watchResidentIds?.includes(resident.person_id) ? '#ffd166' : '#ef476f'"
        stroke="#ffcad5"
        stroke-width="0.12"
        @click="$emit('select-resident', resident.person_id)"
      />
    </svg>

    <div class="readback-chip">
      <span>Watch {{ spatialReadback?.summary?.watchCount || 0 }}</span>
      <span>Pressure {{ spatialReadback?.summary?.pressureCount || 0 }}</span>
      <span>Aftermath {{ spatialReadback?.summary?.aftermathCount || 0 }}</span>
    </div>
    <div class="hover-chip" v-if="hoverDistrictSignal">
      <strong>{{ hoverDistrictSignal.name }}</strong>
      <span>pressure {{ hoverDistrictSignal.pressure.toFixed(2) }}</span>
      <span v-if="hoverDistrictSignal.watch">watch</span>
      <span v-if="hoverDistrictSignal.aftermath">aftermath</span>
    </div>
    <div class="selection-chip" v-if="selectedContext">
      <div class="line"><strong>{{ selectedDistrict?.name }}</strong> · {{ selectedContext.signal }}</div>
      <div class="line">Hot: {{ selectedContext.whyHot?.[0] || selectedContext.topWatchReason || 'No dominant localized driver yet.' }}</div>
      <div class="line">Watch {{ selectedContext.watched ? 'yes' : 'no' }} · Aftermath {{ selectedContext.aftermathPresent ? 'yes' : 'no' }}</div>
      <div class="line">Service context: {{ selectedContext.serviceKinds?.slice(0, 2).join(', ') || 'limited context' }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  arterialRoads,
  collectorRoads,
  districtTextureDots,
  greenSpaces,
  laneStripes,
  mapRegions,
  serviceLandmarks,
  sidewalks,
  urbanBlocks,
  waterFeatures,
} from '../../../lib/auralite/mapRegions'

const props = defineProps({
  districts: Array,
  residentMarkers: Array,
  selectedDistrictId: String,
  spatialReadback: { type: Object, default: () => ({}) },
})
defineEmits(['select-district', 'select-resident'])
const hoveredDistrictId = ref('')
const hoveredServiceId = ref('')

const shapeFor = (key) => mapRegions.find((r) => r.regionKey === key)
const districtSignal = (districtId) => (props.spatialReadback?.districtSignals || []).find((row) => row.district_id === districtId)
const selectedDistrict = computed(() => (props.districts || []).find((row) => row.district_id === props.selectedDistrictId) || null)
const selectedContext = computed(() => props.spatialReadback?.selectedDistrictContext || null)
const hoverDistrictSignal = computed(() => {
  const districtId = hoveredDistrictId.value || props.selectedDistrictId
  const district = (props.districts || []).find((row) => row.district_id === districtId)
  const signal = districtSignal(districtId)
  if (!district || !signal) return null
  return { ...signal, name: district.name }
})

const districtFill = (district) => {
  const shape = shapeFor(district.map_region_key)
  if (!shape) return '#d9e2ec'
  if (props.selectedDistrictId === district.district_id) return '#ffcb6b'
  const signal = districtSignal(district.district_id)
  if (signal?.pressure >= 0.7) return '#b86a6a'
  if (signal?.signal === 'stabilizing') return '#6b9c78'
  return shape.tone
}
const districtOpacity = (district) => {
  if (!hoveredDistrictId.value) return 0.75
  return hoveredDistrictId.value === district.district_id ? 0.92 : 0.45
}
const districtTextColor = (district) => {
  if (props.selectedDistrictId === district.district_id || hoveredDistrictId.value === district.district_id) return '#ffffff'
  return '#e5edf5'
}

const pressureHaloes = computed(() => (props.spatialReadback?.districtSignals || [])
  .filter((row) => row.pressure >= 0.45)
  .map((row) => {
    const shape = shapeFor(row.map_region_key)
    return {
      district_id: row.district_id,
      x: shape?.label?.x || 50,
      y: shape?.label?.y || 50,
      radius: 2.8 + row.pressure * 2.1,
      stroke: row.signal === 'deteriorating' ? '#ff7b7b' : '#f1a94e',
    }
  }))

const serviceColor = (kind) => ({
  civic: '#f9f871',
  medical: '#7ed9ff',
  transit: '#ffd166',
  education: '#c7f9cc',
  industry: '#f29e4c',
}[kind] || '#f1f1f1')
const serviceDistrictId = (service) => {
  const regions = props.districts || []
  let nearest = null
  let bestDistance = Number.POSITIVE_INFINITY
  regions.forEach((district) => {
    const region = shapeFor(district.map_region_key)
    if (!region) return
    const distance = Math.hypot(region.label.x - service.x, region.label.y - service.y)
    if (distance < bestDistance) {
      bestDistance = distance
      nearest = district.district_id
    }
  })
  return nearest
}
const serviceOpacity = (service) => {
  if (hoveredServiceId.value === service.id) return 1
  if (!props.selectedDistrictId) return 0.86
  return serviceDistrictId(service) === props.selectedDistrictId ? 0.95 : 0.35
}
const serviceSize = (service) => (hoveredServiceId.value === service.id ? 1.45 : 1.2)
</script>

<style scoped>
.map-wrap { border: 1px solid #2d4431; background: #1d2b1f; height: 70vh; border-radius: 8px; overflow: hidden; position: relative; }
.map { width: 100%; height: 100%; }
.readback-chip {
  position: absolute;
  left: 10px;
  bottom: 10px;
  background: rgba(12, 16, 22, 0.8);
  border: 1px solid rgba(113, 141, 165, 0.6);
  color: #dce5ec;
  border-radius: 8px;
  font-size: 11px;
  display: flex;
  gap: 8px;
  padding: 5px 8px;
}
.hover-chip,.selection-chip{
  position:absolute;right:10px;background:rgba(10,14,20,.84);border:1px solid rgba(126,153,171,.6);color:#dce5ec;border-radius:8px;font-size:11px;padding:6px 8px;display:flex;gap:8px;flex-wrap:wrap;max-width:44%;
}
.hover-chip{top:10px}
.selection-chip{bottom:44px;display:block}
.line{margin:2px 0}
</style>
