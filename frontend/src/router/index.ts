import {createRouter, createWebHistory} from "vue-router";





const router  = createRouter({
  // 使用 HTML5 历史模式，URL 看起来很自然，没有 # 号
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/task',
      name: 'task',
      component: () => import(/* webpackChunkName: "task" */'../views/TaskView.vue')
    }
  ]
})




export default router
