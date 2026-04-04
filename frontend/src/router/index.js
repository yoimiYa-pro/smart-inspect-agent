import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import ReportLayout from '../layouts/ReportLayout.vue'
import HelpView from '../views/HelpView.vue'
import ReviewInputView from '../views/ReviewInputView.vue'
import ReportOverviewView from '../views/report/ReportOverviewView.vue'
import ReportRisksView from '../views/report/ReportRisksView.vue'
import ReportClausesView from '../views/report/ReportClausesView.vue'
import ReportChatView from '../views/report/ReportChatView.vue'
import { reviewResult } from '../composables/useContractReview'

function guardReport(_to, _from, next) {
  if (!reviewResult.value) {
    next({ name: 'review', replace: true })
  } else {
    next()
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DefaultLayout,
      children: [
        {
          path: '',
          name: 'review',
          component: ReviewInputView,
          meta: {
            title: '合同与审查',
            description: '粘贴合同全文，选择审查视角与模型，生成结构化风险报告与条款解读。',
          },
        },
        {
          path: 'report',
          component: ReportLayout,
          beforeEnter: guardReport,
          children: [
            {
              path: '',
              redirect: { name: 'report-overview' },
            },
            {
              path: 'overview',
              name: 'report-overview',
              component: ReportOverviewView,
              meta: {
                title: '审查总览',
                description: '本轮合同审查结论摘要、评级卡片与可信说明。',
              },
            },
            {
              path: 'risks',
              name: 'report-risks',
              component: ReportRisksView,
              meta: {
                title: '风险分析',
                description: 'TOP 风险与分级清单，可聚焦单条并跳转智能追问。',
              },
            },
            {
              path: 'clauses',
              name: 'report-clauses',
              component: ReportClausesView,
              meta: {
                title: '条款解读',
                description: '无风险条款与全文条款切分结果。',
              },
            },
            {
              path: 'chat',
              name: 'report-chat',
              component: ReportChatView,
              meta: {
                title: '智能追问',
                description: '针对选中风险与合同要点进行对话式追问。',
              },
            },
          ],
        },
        {
          path: 'help',
          name: 'help',
          component: HelpView,
          meta: {
            title: '使用说明',
            description: '智能合同审查工作台的操作说明、适用场景、mock 模式与隐私提示。',
          },
        },
      ],
    },
  ],
  scrollBehavior(to) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0, behavior: 'smooth' }
  },
})

export default router
