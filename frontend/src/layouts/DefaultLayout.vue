<script setup>
import { computed, onMounted, onScopeDispose, onUnmounted, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppFooter from '../components/AppFooter.vue'
import AppSidebar from '../components/AppSidebar.vue'
import HeroToolbar from '../components/HeroToolbar.vue'
import ToastHost from '../components/ToastHost.vue'
import { useDocumentTitle } from '../composables/useDocumentTitle'
import { pushToast } from '../composables/useToast'
import { reviewResult, useContractReview } from '../composables/useContractReview'

useDocumentTitle()

const route = useRoute()
const isReportPage = computed(() => route.path.startsWith('/report'))
const hasReport = computed(() => !!reviewResult.value)

const heroVariant = computed(() => {
  if (route.name === 'help') return 'help'
  if (route.name === 'review') return 'workspace'
  return 'full'
})

const narrowScreen = ref(false)
const sidebarOpen = ref(false)
const sidebarCollapsed = ref(false)
let mediaQueryList = null

function updateNarrowScreen() {
  narrowScreen.value = window.matchMedia('(max-width: 960px)').matches
}

function onMediaChange() {
  updateNarrowScreen()
  if (!narrowScreen.value) {
    sidebarOpen.value = false
  }
}

onMounted(() => {
  mediaQueryList = window.matchMedia('(max-width: 960px)')
  updateNarrowScreen()
  mediaQueryList.addEventListener('change', onMediaChange)
})

onUnmounted(() => {
  mediaQueryList?.removeEventListener('change', onMediaChange)
})

watch(
  () => route.fullPath,
  () => {
    if (narrowScreen.value) {
      sidebarOpen.value = false
    }
  },
)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function onSidebarMenuToggle() {
  if (narrowScreen.value) {
    toggleSidebar()
    return
  }
  sidebarCollapsed.value = !sidebarCollapsed.value
}

function closeMobileSidebar() {
  sidebarOpen.value = false
}

function onDrawerEsc(e) {
  if (e.key === 'Escape' && sidebarOpen.value && narrowScreen.value) {
    sidebarOpen.value = false
  }
}

watch(sidebarOpen, (open) => {
  if (open && narrowScreen.value) {
    document.addEventListener('keydown', onDrawerEsc)
  } else {
    document.removeEventListener('keydown', onDrawerEsc)
  }
})
onScopeDispose(() => document.removeEventListener('keydown', onDrawerEsc))

const {
  selectedRole,
  selectedModel,
  activeModel,
  modelOptions,
  modelSaving,
  useLlm,
  loading,
  errorMessage,
  chatError,
  setExample,
  clearAll,
  handleModelChange,
  submitReview,
} = useContractReview()

watch(errorMessage, (msg) => {
  if (msg) pushToast({ message: msg, variant: 'error', duration: 5200 })
})

watch(chatError, (msg) => {
  if (msg) pushToast({ message: msg, variant: 'error', duration: 5200 })
})

function setSelectedRole(v) {
  selectedRole.value = v
}
function setUseLlm(v) {
  useLlm.value = v
}

const appVersion = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.1.0'

const sidebarDesktopCollapsed = computed(
  () => sidebarCollapsed.value && !narrowScreen.value,
)

const workspaceClasses = computed(() => ({
  'app-workspace--sidebar-open': sidebarOpen.value && narrowScreen.value,
  'app-workspace--sidebar-collapsed': sidebarDesktopCollapsed.value,
}))

const composerDockVars = computed(() => {
  if (narrowScreen.value) {
    return { '--composer-dock-left': '0px' }
  }
  if (sidebarDesktopCollapsed.value) {
    return { '--composer-dock-left': 'var(--sidebar-width-collapsed)' }
  }
  return { '--composer-dock-left': 'var(--sidebar-width)' }
})
</script>

<template>
  <div
    class="page-shell page-shell--workspace"
    :class="{ 'page-shell--report': isReportPage }"
    :style="composerDockVars"
  >
    <a href="#main-content" class="skip-link">跳到主内容</a>

    <div class="app-workspace" :class="workspaceClasses">
      <AppSidebar
        :has-report="hasReport"
        :narrow-screen="narrowScreen"
        :collapsed="sidebarDesktopCollapsed"
        :drawer-open="sidebarOpen"
        @close-mobile="closeMobileSidebar"
        @menu-toggle="onSidebarMenuToggle"
      />

      <button
        v-if="narrowScreen && sidebarOpen"
        type="button"
        class="app-sidebar-backdrop"
        aria-label="关闭导航菜单"
        @click="closeMobileSidebar"
      />

      <div class="app-main">
        <header class="mobile-chrome">
          <button type="button" class="mobile-menu-btn" :aria-expanded="sidebarOpen" aria-controls="workspace-sidebar" @click="toggleSidebar">
            菜单
          </button>
          <span class="mobile-chrome-title">智能合同审查</span>
        </header>

        <HeroToolbar
          v-if="!isReportPage"
          :variant="heroVariant"
          :selected-role="selectedRole"
          :selected-model="selectedModel"
          :use-llm="useLlm"
          :model-options="modelOptions"
          :active-model="activeModel"
          :model-saving="modelSaving"
          :loading="loading"
          @update:selected-role="setSelectedRole"
          @update:use-llm="setUseLlm"
          @model-change="handleModelChange"
          @set-example="setExample"
          @clear-all="clearAll"
          @submit-review="submitReview"
        />

        <main id="main-content">
          <RouterView v-slot="{ Component }">
            <Transition name="route-fade" mode="out-in">
              <component :is="Component" />
            </Transition>
          </RouterView>
        </main>

        <AppFooter :version="appVersion" />
      </div>
    </div>

    <ToastHost />
  </div>
</template>
