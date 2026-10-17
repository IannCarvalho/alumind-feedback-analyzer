import { createRouter, createWebHistory } from 'vue-router'

/*
 * Rotas do painel. O SPA é o painel padrão, servido na raiz pelo Flask
 * (history base '/'); os assets saem de /static/spa/ (Vite `base`).
 */
const router = createRouter({
  history: createWebHistory('/'),
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
      // Única rota pública do SPA (o servidor a entrega sem sessão). "bare" =
      // sem a barra lateral do painel.
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: 'Entrar', layout: 'bare' },
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
