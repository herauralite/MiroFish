<template>
  <div class="map-wrap">
    <svg viewBox="0 0 100 100" class="map">
      <rect x="0" y="0" width="100" height="100" fill="#3a5a28" />

      <rect
        v-for="(road, idx) in majorRoads"
        :key="`road-${idx}`"
        :x="road.x"
        :y="road.y"
        :width="road.width"
        :height="road.height"
        fill="#4a4a4a"
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

      <g v-for="district in districts" :key="district.district_id">
        <path
          v-if="shapeFor(district.map_region_key)"
          :d="shapeFor(district.map_region_key).path"
          :fill="districtFill(district)"
          stroke="#24323d"
          stroke-width="0.45"
          opacity="0.7"
          @click="$emit('select-district', district.district_id)"
        />
        <text
          v-if="shapeFor(district.map_region_key)"
          :x="shapeFor(district.map_region_key).label.x"
          :y="shapeFor(district.map_region_key).label.y"
          font-size="1.9"
          fill="#f4f8fb"
          text-anchor="middle"
          font-weight="700"
        >{{ district.name }}</text>
      </g>

      <circle
        v-for="resident in residentMarkers"
        :key="resident.person_id"
        :cx="resident.x"
        :cy="resident.y"
        r="0.44"
        fill="#ef476f"
        stroke="#ffcad5"
        stroke-width="0.12"
        @click="$emit('select-resident', resident.person_id)"
      />
    </svg>
  </div>
</template>

<script setup>
import { greenSpaces, laneStripes, majorRoads, mapRegions, urbanBlocks, waterFeatures } from '../../../lib/auralite/mapRegions'

const props = defineProps({ districts: Array, residentMarkers: Array, selectedDistrictId: String })
defineEmits(['select-district', 'select-resident'])

const shapeFor = (key) => mapRegions.find((r) => r.regionKey === key)

const districtFill = (district) => {
  const shape = shapeFor(district.map_region_key)
  if (!shape) return '#d9e2ec'
  return props.selectedDistrictId === district.district_id ? '#ffcb6b' : shape.tone
}
</script>

<style scoped>
.map-wrap { border: 1px solid #2d4431; background: #1d2b1f; height: 70vh; border-radius: 8px; overflow: hidden; }
.map { width: 100%; height: 100%; }
</style>
