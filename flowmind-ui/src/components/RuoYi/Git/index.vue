<template>
  <div>
    <svg-icon icon-class="github" @click="goto" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
const url = ref('https://github.com/Moonlight168/flowmind')

function goto() {
  window.open(url.value)
}
</script>
