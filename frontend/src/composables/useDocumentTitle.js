import { watch } from 'vue'
import { useRoute } from 'vue-router'

const PRODUCT_NAME = '智能合同审查'
const TITLE_SUFFIX = ` · ${PRODUCT_NAME}`

function applyMetaDescription(content) {
  const el = document.querySelector('meta[name="description"]')
  if (el && content) {
    el.setAttribute('content', content)
  }
}

export function useDocumentTitle() {
  const route = useRoute()
  watch(
    () => [route.meta?.title, route.meta?.description],
    ([title, description]) => {
      document.title = `${title || '工作台'}${TITLE_SUFFIX}`
      if (typeof description === 'string' && description.length > 0) {
        applyMetaDescription(description)
      }
    },
    { immediate: true },
  )
}
