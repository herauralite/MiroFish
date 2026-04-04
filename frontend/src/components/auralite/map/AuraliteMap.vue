<template>
  <div class="map-wrap">
    <svg viewBox="0 0 100 100" class="map">
      <rect x="0" y="0" width="100" height="100" fill="#f6f8fa" />
      <g v-for="district in districts" :key="district.district_id">
        <rect
          v-if="rectFor(district.map_region_key)"
          :x="rectFor(district.map_region_key).x"
          :y="rectFor(district.map_region_key).y"
          :width="rectFor(district.map_region_key).width"
          :height="rectFor(district.map_region_key).height"
          :fill="selectedDistrictId===district.district_id ? '#ffd166' : '#dfe7ef'"
          stroke="#4a5568"
          @click="$emit('select-district', district.district_id)"
        />
        <text
          v-if="rectFor(district.map_region_key)"
          :x="rectFor(district.map_region_key).x + 1"
          :y="rectFor(district.map_region_key).y + 3"
          font-size="2.5"
        >{{ district.name }}</text>
      </g>
      <circle
        v-for="resident in residentMarkers"
        :key="resident.person_id"
        :cx="resident.x"
        :cy="resident.y"
        r="0.65"
        fill="#ef476f"
        @click="$emit('select-resident', resident.person_id)"
      />
    </svg>
  </div>
</template>

<script setup>
import { regionRects } from '../../../lib/auralite/districtConfig'

const props = defineProps({ districts: Array, residentMarkers: Array, selectedDistrictId: String })
defineEmits(['select-district', 'select-resident'])
const rectFor = (key) => regionRects.find((r) => r.regionKey === key)
</script>

<style scoped>
.map-wrap{border:1px solid #ddd;background:#fff;height:70vh}
.map{width:100%;height:100%}
</style>
