<template>
  <v-container fluid class="py-4">
    <!-- ヘッダ -->
    <v-row align="center" class="mb-4 schedule-header">
      <v-col cols="auto">
        <v-btn variant="outlined" prepend-icon="mdi-calendar" @click="showDatePicker = true">
          {{ displayDate }}
        </v-btn>
      </v-col>
      <v-col cols="auto">
        <v-btn color="primary" prepend-icon="mdi-refresh" :loading="store.loading" @click="doRefresh">
          更新
        </v-btn>
      </v-col>
      <v-col cols="auto" class="text-h6">
        {{ cinemaName }}
      </v-col>
      <v-spacer />
      <v-col v-if="viewMode === 'movie'" cols="auto">
        <v-btn variant="text" size="small" prepend-icon="mdi-collapse-all" @click="collapseAll">
          すべて閉じる
        </v-btn>
      </v-col>
      <v-col cols="auto">
        <v-btn-toggle v-model="viewMode" mandatory variant="outlined" density="comfortable">
          <v-btn value="movie"><v-icon start>mdi-movie</v-icon>作品別</v-btn>
          <v-btn value="screen"><v-icon start>mdi-monitor</v-icon>スクリーン別</v-btn>
        </v-btn-toggle>
      </v-col>
    </v-row>

    <!-- 作品別表示 -->
    <template v-if="viewMode === 'movie'">
      <MovieGroupView ref="movieGroupRef" :groups="movieGroups" />
    </template>

    <!-- スクリーン別表示 -->
    <template v-else>
      <ScreenTimelineView :screens="screenGroups" />
    </template>

    <!-- 日付ピッカー -->
    <v-dialog v-model="showDatePicker" max-width="360">
      <v-card>
        <v-date-picker v-model="pickerDate" color="primary" :min="today" :max="maxDate" />
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showDatePicker = false">キャンセル</v-btn>
          <v-btn color="primary" @click="onDateConfirm">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ローディング -->
    <v-overlay v-model="store.loading" class="align-center justify-center" persistent>
      <v-progress-circular indeterminate size="64" />
    </v-overlay>

    <!-- エラー -->
    <v-snackbar v-model="showError" color="error" timeout="4000">
      {{ store.error }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useScheduleStore } from '@/stores/schedule'
import MovieGroupView from '@/components/MovieGroupView.vue'
import ScreenTimelineView from '@/components/ScreenTimelineView.vue'
import { displayCinemaName } from '@/utils/textNormalize'
import type { ScheduleItem } from '@/types'

const props = defineProps<{ code: string }>()
const store = useScheduleStore()

const today = new Date()
const selectedDate = ref(formatYmd(today))
const pickerDate = ref<Date>(today)
const showDatePicker = ref(false)
const viewMode = ref<'movie' | 'screen'>('movie')
const showError = ref(false)
const movieGroupRef = ref<InstanceType<typeof MovieGroupView> | null>(null)

const cinemaName = computed(() => {
  const c = store.cinemas.find(c => c.code === props.code)
  return c ? displayCinemaName(c.name) : ''
})

const maxDate = computed(() => {
  const d = new Date()
  d.setDate(d.getDate() + 6)
  return d
})

watch(() => store.error, (v) => { if (v) showError.value = true })

const displayDate = computed(() => {
  const d = selectedDate.value
  return `${d.slice(0, 4)}/${d.slice(4, 6)}/${d.slice(6, 8)}`
})

function formatYmd(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}${m}${day}`
}

function onDateConfirm() {
  if (pickerDate.value) {
    const d = new Date(pickerDate.value)
    selectedDate.value = formatYmd(d)
  }
  showDatePicker.value = false
  loadSchedule()
}

function doRefresh() {
  loadSchedule()
}

function loadSchedule() {
  store.fetchCinemaSchedule(props.code, selectedDate.value)
}

function collapseAll() {
  movieGroupRef.value?.collapseAll()
}

// ---------- 作品別グループ ----------
interface MovieGroup {
  movieName: string
  items: ScheduleItem[]
}

const movieGroups = computed<MovieGroup[]>(() => {
  const map = new Map<string, ScheduleItem[]>()
  for (const item of store.cinemaSchedules) {
    const key = normalizeMovieName(item.movieName)
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(item)
  }
  return Array.from(map.entries()).map(([movieName, items]) => ({
    movieName,
    items: items.sort((a, b) => timeToMinutes(a.startTime) - timeToMinutes(b.startTime)),
  }))
})

function timeToMinutes(t: string): number {
  const parts = t.split(':')
  return parseInt(parts[0] || '0', 10) * 60 + parseInt(parts[1] || '0', 10)
}

function normalizeMovieName(name: string): string {
  return name
    .replace(/[\(（].*?[\)）]/g, '')
    .replace(/\s*(IMAX|ドルビーシネマ|ドルビーアトモス|DOLBY\s*CINEMA|DOLBY\s*ATMOS|4DX|MX4D|字幕|吹替|日本語吹替|日本語字幕|2D|3D|TCX|BESTIA)\s*/gi, '')
    .trim()
}

// ---------- スクリーン別グループ ----------
interface ScreenGroup {
  screenName: string
  items: ScheduleItem[]
}

const screenGroups = computed<ScreenGroup[]>(() => {
  const map = new Map<string, ScheduleItem[]>()
  for (const item of store.cinemaSchedules) {
    const key = item.screenName
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(item)
  }
  return Array.from(map.entries())
    .map(([screenName, items]) => ({
      screenName,
      items: items.sort((a, b) => a.startTime.localeCompare(b.startTime)),
    }))
    .sort((a, b) => a.screenName.localeCompare(b.screenName))
})

onMounted(() => {
  loadSchedule()
})
</script>

<style scoped>
.schedule-header {
  position: sticky;
  top: 48px;
  z-index: 3;
  background: rgb(var(--v-theme-background));
  padding-top: 8px;
  padding-bottom: 8px;
  margin-left: 0;
  margin-right: 0;
}
</style>
