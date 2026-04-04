<template>
  <div class="controls">
    <button @click="$emit('start')">▶</button>
    <button @click="$emit('pause')">⏸</button>
    <button @click="$emit('tick')">+15m</button>
    <button @click="$emit('save')">💾</button>
    <button @click="$emit('load')">↩</button>
    <select :value="speed" @change="$emit('speed', Number($event.target.value))">
      <option :value="1">1x</option>
      <option :value="6">6x</option>
      <option :value="12">12x</option>
      <option :value="24">24x</option>
    </select>
  </div>
</template>

<script setup>
defineProps({ speed: { type: Number, required: true } })
defineEmits(['start', 'pause', 'tick', 'speed', 'save', 'load'])
</script>
