<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const props = defineProps({
  hasReport: { type: Boolean, required: true },
  narrowScreen: { type: Boolean, default: false },
  collapsed: { type: Boolean, default: false },
  drawerOpen: { type: Boolean, default: false },
})

const emit = defineEmits(['close-mobile', 'menu-toggle'])

const route = useRoute()

function onNavClick() {
  emit('close-mobile')
}

function onMenuClick() {
  emit('menu-toggle')
}

function scrollToMain() {
  document.getElementById('main-content')?.scrollIntoView({ behavior: 'smooth' })
}

const reviewActive = computed(() => route.name === 'review')
const helpActive = computed(() => route.name === 'help')

const reportNav = [
  { name: 'report-overview', label: '审查总览', icon: 'overview' },
  { name: 'report-risks', label: '风险分析', icon: 'risk' },
  { name: 'report-clauses', label: '条款解读', icon: 'clauses' },
  { name: 'report-chat', label: '智能追问', icon: 'chat', featured: true },
]

function reportItemActive(navName) {
  return route.name === navName
}

const menuAria = computed(() => {
  if (props.narrowScreen) {
    return props.drawerOpen ? '关闭导航菜单' : '打开导航菜单'
  }
  return props.collapsed ? '展开侧栏' : '收起侧栏'
})
</script>

<template>
  <aside
    id="workspace-sidebar"
    class="app-sidebar"
    :class="{ 'app-sidebar--collapsed': collapsed }"
    aria-label="工作区导航"
  >
    <div class="sidebar-gemini-chrome">
      <button
        type="button"
        class="sidebar-icon-btn"
        :aria-label="menuAria"
        aria-controls="workspace-sidebar"
        :aria-expanded="narrowScreen ? drawerOpen : undefined"
        @click="onMenuClick"
      >
        <svg class="sidebar-glyph" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>
      <button
        v-show="!collapsed"
        type="button"
        class="sidebar-icon-btn"
        aria-label="转到主内容区域"
        @click="scrollToMain"
      >
        <svg class="sidebar-glyph" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="11" cy="11" r="6" stroke="currentColor" stroke-width="2" />
          <path
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            d="m20 20-3.2-3.2"
          />
        </svg>
      </button>
    </div>

    <div class="sidebar-brand">
      <span class="sidebar-brand-mark" aria-hidden="true" />
      <div class="sidebar-brand-text">
        <span class="sidebar-brand-title">智能合同审查</span>
        <span class="sidebar-brand-sub">工作区</span>
      </div>
    </div>

    <div class="sidebar-nav-scroll">
      <nav class="sidebar-nav" aria-label="功能导航">
        <RouterLink
          class="sidebar-nav-item"
          :class="{ 'sidebar-nav-item--active': reviewActive }"
          :to="{ name: 'review' }"
          :aria-current="reviewActive ? 'page' : undefined"
          :title="collapsed ? '合同与审查' : undefined"
          @click="onNavClick"
        >
          <span class="sidebar-nav-item__icon" aria-hidden="true">
            <svg class="sidebar-glyph" viewBox="0 0 24 24" fill="none">
              <path
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linejoin="round"
                d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
              />
              <path
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linejoin="round"
                d="M14 2v6h6M16 13H8M16 17H8M10 9H8"
              />
            </svg>
          </span>
          <span class="sidebar-nav-item__label">合同与审查</span>
        </RouterLink>

        <p class="sidebar-nav-section">审查结果</p>

        <template v-if="hasReport">
          <RouterLink
            v-for="item in reportNav"
            :key="item.name"
            class="sidebar-nav-item sidebar-nav-item--nested"
            :class="{
              'sidebar-nav-item--active': reportItemActive(item.name),
              'sidebar-nav-item--featured': item.featured,
            }"
            :to="{ name: item.name }"
            :aria-current="reportItemActive(item.name) ? 'page' : undefined"
            :title="collapsed ? (item.featured ? `${item.label}（对话式追问）` : item.label) : undefined"
            @click="onNavClick"
          >
            <span class="sidebar-nav-item__icon" aria-hidden="true">
              <svg
                v-if="item.icon === 'overview'"
                class="sidebar-glyph"
                viewBox="0 0 24 24"
                fill="none"
              >
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
              </svg>
              <svg
                v-else-if="item.icon === 'risk'"
                class="sidebar-glyph"
                viewBox="0 0 24 24"
                fill="none"
              >
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
              </svg>
              <svg
                v-else-if="item.icon === 'clauses'"
                class="sidebar-glyph"
                viewBox="0 0 24 24"
                fill="none"
              >
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
              </svg>
              <svg v-else class="sidebar-glyph" viewBox="0 0 24 24" fill="none">
                <path
                  stroke="currentColor"
                  stroke-width="1.75"
                  stroke-linejoin="round"
                  d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
                />
              </svg>
            </span>
            <span class="sidebar-nav-item__label">
              {{ item.label }}
              <span v-if="item.featured" class="sidebar-nav-item__pill" aria-hidden="true">对话</span>
            </span>
          </RouterLink>
        </template>
        <template v-else>
          <span
            v-for="item in reportNav"
            :key="item.name"
            class="sidebar-nav-item sidebar-nav-item--nested sidebar-nav-item--disabled"
            :class="{ 'sidebar-nav-item--featured': item.featured }"
            :title="'完成一次审查后可打开' + item.label"
            role="presentation"
          >
            <span class="sidebar-nav-item__icon" aria-hidden="true">
              <svg class="sidebar-glyph sidebar-glyph--muted" viewBox="0 0 24 24" fill="none">
                <rect
                  x="3"
                  y="3"
                  width="18"
                  height="18"
                  rx="2"
                  stroke="currentColor"
                  stroke-width="1.75"
                />
              </svg>
            </span>
            <span class="sidebar-nav-item__label">
              {{ item.label }}
              <span v-if="item.featured" class="sidebar-nav-item__pill" aria-hidden="true">对话</span>
            </span>
          </span>
        </template>
      </nav>
    </div>

    <div class="sidebar-footer">
      <RouterLink
        class="sidebar-nav-item sidebar-nav-item--footer"
        :class="{ 'sidebar-nav-item--active': helpActive }"
        :to="{ name: 'help' }"
        :aria-current="helpActive ? 'page' : undefined"
        :title="collapsed ? '使用说明' : undefined"
        @click="onNavClick"
      >
        <span class="sidebar-nav-item__icon" aria-hidden="true">
          <svg class="sidebar-glyph" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.75" />
            <path
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
            />
          </svg>
        </span>
        <span class="sidebar-nav-item__label">设置与使用说明</span>
      </RouterLink>
    </div>
  </aside>
</template>
