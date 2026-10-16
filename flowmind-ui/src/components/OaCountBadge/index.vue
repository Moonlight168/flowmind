<template>
  <span v-if="Number.isFinite(count) && count > 0" class="oa-count-badge"
    :title="`${label} ${count} 条`" :aria-label="`${label} ${count} 条`">
    {{ count > 99 ? '99+' : count }}
  </span>
</template>

<script setup>
defineProps({ count: { type: Number, default: null }, label: { type: String, default: '待处理' } })
</script>

<style scoped>
.oa-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  box-sizing: border-box;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
</style>
