<template>
    <v-container fluid class="py-4">
        <!-- ヘッダ -->
        <v-row align="center" class="mb-4 schedule-header">
            <v-col cols="auto">
                <v-btn
                    variant="outlined"
                    prepend-icon="mdi-calendar"
                    @click="showDatePicker = true"
                >
                    {{ displayDate }}
                </v-btn>
            </v-col>
            <v-col cols="auto">
                <v-btn
                    color="primary"
                    prepend-icon="mdi-refresh"
                    :loading="store.loading"
                    @click="doRefresh"
                >
                    更新
                </v-btn>
            </v-col>
            <v-col cols="auto" class="text-h6">
                <a
                    v-if="movieCode"
                    :href="
                        'https://hlo.tohotheater.jp/net/movie/TNPI3060J01.do?sakuhin_cd=' +
                        movieCode
                    "
                    target="_blank"
                    rel="noopener"
                    class="movie-link"
                    >{{ displayMovieName(decodedMovieKey) }}</a
                >
                <template v-else>{{
                    displayMovieName(decodedMovieKey)
                }}</template>
            </v-col>
            <v-spacer />
            <v-col cols="auto">
                <v-btn
                    variant="text"
                    size="small"
                    prepend-icon="mdi-collapse-all"
                    @click="collapseAll"
                >
                    すべて閉じる
                </v-btn>
            </v-col>
        </v-row>

        <!-- ローディング -->
        <div v-if="store.loading" class="text-center py-8">
            <v-progress-circular indeterminate size="64" />
            <p class="mt-4 text-grey">読み込み中...</p>
        </div>

        <!-- 地区毎 → 劇場毎に展開 -->
        <div
            v-else-if="regionGroups.length === 0"
            class="text-center text-grey py-8"
        >
            この作品の上映スケジュールがありません
        </div>

        <v-expansion-panels
            v-else
            v-model="openRegionPanels"
            variant="accordion"
            multiple
        >
            <v-expansion-panel
                v-for="(rg, ri) in regionGroups"
                :key="rg.region"
            >
                <v-expansion-panel-title>
                    <span class="text-h6">{{ rg.region }}</span>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                    <v-expansion-panels
                        v-model="cinemaPanelState[ri]"
                        variant="accordion"
                        multiple
                    >
                        <v-expansion-panel
                            v-for="group in rg.cinemaGroups"
                            :key="group.cinemaCode"
                        >
                            <v-expansion-panel-title>
                                <div class="d-flex align-center ga-2">
                                    <v-icon color="secondary"
                                        >mdi-filmstrip</v-icon
                                    >
                                    <span class="text-h6">{{
                                        group.cinemaName
                                    }}</span>
                                    <v-chip
                                        size="small"
                                        color="primary"
                                        class="ml-2"
                                        >{{ group.items.length }}回</v-chip
                                    >
                                </div>
                            </v-expansion-panel-title>
                            <v-expansion-panel-text>
                                <v-table density="comfortable">
                                    <thead>
                                        <tr>
                                            <th>上映タイプ</th>
                                            <th>スクリーン</th>
                                            <th>開始</th>
                                            <th>終了</th>
                                            <th>上映時間</th>
                                            <th>座席状況</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr
                                            v-for="(item, i) in group.items"
                                            :key="i"
                                            :class="{
                                                'row-closed':
                                                    item.seatStatus ===
                                                    '販売終了',
                                            }"
                                        >
                                            <td>
                                                {{
                                                    extractLabel(item.movieName)
                                                }}
                                            </td>
                                            <td>{{ item.screenName }}</td>
                                            <td>{{ item.startTime }}</td>
                                            <td>{{ item.endTime }}</td>
                                            <td>{{ item.duration }}分</td>
                                            <td>
                                                <v-chip
                                                    :color="
                                                        seatColor(
                                                            item.seatStatus,
                                                        )
                                                    "
                                                    size="small"
                                                >
                                                    {{ item.seatStatus || "—" }}
                                                </v-chip>
                                            </td>
                                        </tr>
                                    </tbody>
                                </v-table>
                            </v-expansion-panel-text>
                        </v-expansion-panel>
                    </v-expansion-panels>
                </v-expansion-panel-text>
            </v-expansion-panel>
        </v-expansion-panels>

        <!-- 日付ピッカー -->
        <v-dialog v-model="showDatePicker" max-width="360">
            <v-card>
                <v-date-picker
                    v-model="pickerDate"
                    color="primary"
                    :min="today"
                    :max="maxDate"
                />
                <v-card-actions>
                    <v-spacer />
                    <v-btn text @click="showDatePicker = false"
                        >キャンセル</v-btn
                    >
                    <v-btn color="primary" @click="onDateConfirm">OK</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- エラー -->
        <v-snackbar v-model="showError" color="error" timeout="4000">
            {{ store.error }}
        </v-snackbar>
    </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useScheduleStore } from "@/stores/schedule";
import {
    displayCinemaName,
    displayMovieName,
    regionSortIndex,
} from "@/utils/textNormalize";
import type { ScheduleItem } from "@/types";

const props = defineProps<{ movieKey: string }>();
const store = useScheduleStore();

const today = new Date();
const selectedDate = ref(formatToday());
const pickerDate = ref<Date>(today);
const showDatePicker = ref(false);
const showError = ref(false);
const openRegionPanels = ref<number[]>([]);
const cinemaPanelState = ref<number[][]>([]);

const decodedMovieKey = computed(() => decodeURIComponent(props.movieKey));

const movieCode = computed(() => {
    const item = store.allSchedules.find(
        (s) => normalizeMovieName(s.movieName) === decodedMovieKey.value,
    );
    return item?.movieCode ?? "";
});

const maxDate = computed(() => {
    const d = new Date();
    d.setDate(d.getDate() + 6);
    return d;
});

const displayDate = computed(() => {
    const d = selectedDate.value;
    return `${d.slice(0, 4)}/${d.slice(4, 6)}/${d.slice(6, 8)}`;
});

watch(
    () => store.error,
    (v) => {
        if (v) showError.value = true;
    },
);

function formatToday(): string {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}${m}${day}`;
}

function formatYmd(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}${m}${day}`;
}

function onDateConfirm() {
    if (pickerDate.value) {
        const d = new Date(pickerDate.value);
        selectedDate.value = formatYmd(d);
    }
    showDatePicker.value = false;
    loadSchedules();
}

function doRefresh() {
    loadSchedules();
}

function loadSchedules() {
    store.fetchAllSchedules(selectedDate.value);
}

function collapseAll() {
    openRegionPanels.value = [];
    cinemaPanelState.value = regionGroups.value.map(() => []);
}

// 初期データが未ロードの場合にロードする
onMounted(async () => {
    if (!store.initialLoaded) {
        await store.loadInitialData(selectedDate.value);
    }
});

function normalizeMovieName(name: string): string {
    return name
        .replace(/[\(（].*?[\)）]/g, "")
        .replace(
            /\s*(IMAX|ドルビーシネマ|ドルビーアトモス|DOLBY\s*CINEMA|DOLBY\s*ATMOS|4DX|MX4D|字幕|吹替|日本語吹替|日本語字幕|2D|3D|TCX|BESTIA)\s*/gi,
            "",
        )
        .trim();
}

function timeToMinutes(t: string): number {
    const parts = t.split(":");
    return parseInt(parts[0] || "0", 10) * 60 + parseInt(parts[1] || "0", 10);
}

interface CinemaGroup {
    cinemaCode: string;
    cinemaName: string;
    items: ScheduleItem[];
}

interface RegionGroupEntry {
    region: string;
    cinemaGroups: CinemaGroup[];
}

const regionGroups = computed<RegionGroupEntry[]>(() => {
    const filtered = store.allSchedules.filter(
        (item) => normalizeMovieName(item.movieName) === decodedMovieKey.value,
    );

    // 劇場毎にグルーピング
    const map = new Map<string, ScheduleItem[]>();
    for (const item of filtered) {
        if (!map.has(item.cinemaCode)) map.set(item.cinemaCode, []);
        map.get(item.cinemaCode)!.push(item);
    }

    const cinemaMap = new Map(store.cinemas.map((c) => [c.code, c]));

    // 地区毎にグルーピング
    const regionMap = new Map<string, CinemaGroup[]>();
    for (const [cinemaCode, items] of map.entries()) {
        const cinema = cinemaMap.get(cinemaCode);
        const region = cinema?.region || "不明";
        const cinemaName = cinema ? displayCinemaName(cinema.name) : cinemaCode;
        if (!regionMap.has(region)) regionMap.set(region, []);
        regionMap.get(region)!.push({
            cinemaCode,
            cinemaName,
            items: items.sort(
                (a, b) =>
                    timeToMinutes(a.startTime) - timeToMinutes(b.startTime),
            ),
        });
    }

    return Array.from(regionMap.entries())
        .sort((a, b) => regionSortIndex(a[0]) - regionSortIndex(b[0]))
        .map(([region, cinemaGroups]) => ({
            region,
            cinemaGroups: cinemaGroups.sort((a, b) =>
                a.cinemaName.localeCompare(b.cinemaName),
            ),
        }));
});

// regionGroupsが変わったらcinemaPanelStateを初期化
watch(
    regionGroups,
    (groups) => {
        cinemaPanelState.value = groups.map(() => []);
    },
    { immediate: true },
);

function extractLabel(movieName: string): string {
    const tags: string[] = [];
    const patterns = [
        /IMAX/i,
        /ドルビーシネマ|DOLBY\s*CINEMA/i,
        /ドルビーアトモス|DOLBY\s*ATMOS/i,
        /4DX/i,
        /MX4D/i,
        /字幕/,
        /吹替|日本語吹替/,
        /3D/,
        /TCX/i,
        /BESTIA/i,
    ];
    for (const p of patterns) {
        if (p.test(movieName)) tags.push(movieName.match(p)![0]);
    }
    return tags.length > 0 ? tags.join(" / ") : "通常";
}

function seatColor(status: string): string {
    switch (status) {
        case "余裕あり":
            return "success";
        case "残りわずか":
            return "warning";
        case "満席":
            return "error";
        case "販売終了":
            return "grey";
        default:
            return "default";
    }
}
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

.row-closed {
    opacity: 0.4;
}

.movie-link {
    color: inherit;
    text-decoration: none;
}
.movie-link:hover {
    text-decoration: underline;
}
</style>
