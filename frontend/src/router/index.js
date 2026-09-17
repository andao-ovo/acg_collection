import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    children: [
      {
        path: '',
        name: 'works',
        component: () => import('@/views/WorkList.vue'),
        meta: { title: '作品列表' },
      },
      {
        path: 'work/:id',
        name: 'work-detail',
        component: () => import('@/views/WorkDetail.vue'),
        meta: { title: '作品详情' },
      },
      {
        path: 'stats',
        name: 'stats',
        component: () => import('@/views/Stats.vue'),
        meta: { title: '统计' },
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录 / 注册' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · ACG 收藏馆` : 'ACG 收藏馆'
})

export default router