<template>
  <div>
    <svg-icon icon-class="question" @click="goto" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
const url = ref('https://codebyggbond.dpdns.org/series/myprojects/FlowMind/')

function goto() {
  window.open(url.value)
}
</script>