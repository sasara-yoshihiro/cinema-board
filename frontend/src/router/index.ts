import { createRouter, createWebHistory } from 'vue-router'
import MainView from '@/views/MainView.vue'
import CinemaScheduleView from '@/views/CinemaScheduleView.vue'
import MovieScheduleView from '@/views/MovieScheduleView.vue'

const routes = [
  { path: '/', name: 'main', component: MainView },
  { path: '/cinema/:code', name: 'cinema-schedule', component: CinemaScheduleView, props: true },
  { path: '/movie/:movieKey', name: 'movie-schedule', component: MovieScheduleView, props: true },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
