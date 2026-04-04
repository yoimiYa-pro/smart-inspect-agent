<script setup>
import { useToastState, removeToast } from '../composables/useToast'

const state = useToastState()
</script>

<template>
  <div class="toast-host" aria-live="polite" aria-relevant="additions removals">
    <TransitionGroup name="toast" tag="div" class="toast-host__list">
      <div
        v-for="item in state.items"
        :key="item.id"
        class="toast-item"
        :class="`toast-item--${item.variant}`"
        role="status"
      >
        <span class="toast-item__text">{{ item.message }}</span>
        <button type="button" class="toast-item__dismiss" @click="removeToast(item.id)" aria-label="关闭通知">
          ×
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
