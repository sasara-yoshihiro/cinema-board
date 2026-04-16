import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { Cinema, ScheduleItem } from '@/types'

export const useScheduleStore = defineStore('schedule', () => {
  const cinemas = ref<Cinema[]>([])
  const allSchedules = ref<ScheduleItem[]>([])
  const cinemaSchedules = ref<ScheduleItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const initialLoaded = ref(false)

  /** 初期読み込み: 劇場一覧 + 全スケジュールを同時取得 */
  async function loadInitialData(showDay: string) {
    loading.value = true
    error.value = null
    try {
      const [cinemasRes, schedulesRes] = await Promise.all([
        axios.get<Cinema[]>('/api/cinemas'),
        axios.get<ScheduleItem[]>('/api/schedules', { params: { show_day: showDay } }),
      ])
      cinemas.value = cinemasRes.data
      allSchedules.value = schedulesRes.data
      initialLoaded.value = true
    } catch (e: any) {
      error.value = e.message ?? 'データの読み込みに失敗しました'
      throw e
    } finally {
      loading.value = false
    }
  }

  /** 全スケジュールを再取得 */
  async function fetchAllSchedules(showDay: string) {
    loading.value = true
    error.value = null
    try {
      const { data } = await axios.get<ScheduleItem[]>('/api/schedules', { params: { show_day: showDay } })
      allSchedules.value = data
    } catch (e: any) {
      error.value = e.message ?? 'スケジュールの取得に失敗しました'
    } finally {
      loading.value = false
    }
  }

  /** 劇場指定スケジュールを取得 */
  async function fetchCinemaSchedule(cinemaCode: string, showDay: string) {
    loading.value = true
    error.value = null
    try {
      const { data } = await axios.get<ScheduleItem[]>(
        `/api/schedules/${encodeURIComponent(cinemaCode)}`,
        { params: { show_day: showDay } },
      )
      cinemaSchedules.value = data
    } catch (e: any) {
      error.value = e.message ?? 'スケジュールの取得に失敗しました'
    } finally {
      loading.value = false
    }
  }

  return {
    cinemas, allSchedules, cinemaSchedules, loading, error, initialLoaded,
    loadInitialData, fetchAllSchedules, fetchCinemaSchedule,
  }
})
