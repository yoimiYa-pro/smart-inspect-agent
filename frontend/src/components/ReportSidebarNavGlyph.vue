<script setup>
defineProps({
  variant: {
    type: String,
    required: true,
    validator: (v) => ['overview', 'risk', 'clauses', 'chat'].includes(v),
  },
  muted: { type: Boolean, default: false },
})
</script>

<template>
  <svg
    :class="['sidebar-glyph', { 'sidebar-glyph--muted': muted }]"
    viewBox="0 0 24 24"
    fill="none"
    aria-hidden="true"
  >
    <template v-if="variant === 'overview'">
      <rect
        x="3"
        y="3"
        width="7"
        height="9"
        rx="1.25"
        stroke="currentColor"
        stroke-width="1.75"
      />
      <rect
        x="14"
        y="3"
        width="7"
        height="5"
        rx="1.25"
        stroke="currentColor"
        stroke-width="1.75"
      />
      <rect
        x="14"
        y="12"
        width="7"
        height="9"
        rx="1.25"
        stroke="currentColor"
        stroke-width="1.75"
      />
      <rect
        x="3"
        y="16"
        width="7"
        height="5"
        rx="1.25"
        stroke="currentColor"
        stroke-width="1.75"
      />
    </template>
    <template v-else-if="variant === 'risk'">
      <path
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linejoin="round"
        d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
      />
      <path
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        d="M12 9v4M12 17h.01"
      />
    </template>
    <template v-else-if="variant === 'clauses'">
      <path
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"
        d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"
      />
      <path
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linejoin="round"
        d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"
      />
    </template>
    <template v-else>
      <path
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linejoin="round"
        d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
      />
    </template>
  </svg>
</template>
