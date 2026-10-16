import { createRouter, createWebHistory } from 'vue-router'

/*
 * Rotas do painel. As telas completas chegam nos próximos PRs; neste andaime
 * só o Dashboard (placeholder) e a rota do cofre de provedores existem, para
 * provar a arquitetura (router + layout + base /static/spa/).
 */
const router = createRouter({
  history: createWebHistory('/app/'),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { title: 'Visão geral' },
    },
    {
      path: '/providers',
      name: 'providers',
      component: () => import('@/views/ProvidersView.vue'),
      meta: { title: 'Provedores de IA' },
    },
    {
      path: '/feedbacks',
      name: 'feedbacks',
      component: () => import('@/views/FeedbackListView.vue'),
      meta: { title: 'Feedbacks' },
    },
    {
      path: '/feedbacks/:id',
      name: 'feedback-detail',
      component: () => import('@/views/FeedbackDetailView.vue'),
      meta: { title: 'Detalhe do feedback' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string | undefined) ?? ''
  document.title = title ? `${title} · FeedLens` : 'FeedLens'
})

export default router
