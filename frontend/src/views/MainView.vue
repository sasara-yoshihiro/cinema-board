<template>
    <v-container class="py-6">
        <!-- ページ読み込みエラー -->
        <div v-if="loadError" class="text-center py-16">
            <v-icon size="64" color="error" class="mb-4"
                >mdi-alert-circle-outline</v-icon
            >
            <h2 class="text-h5 mb-2">ページ読み込みエラー</h2>
            <p class="text-grey mb-4">{{ loadError }}</p>
            <v-btn color="primary" @click="loadData">再読み込み</v-btn>
        </div>

        <!-- メインコンテンツ -->
        <template v-else-if="store.initialLoaded">
            <v-tabs v-model="tab" color="primary" class="mb-4">
                <v-tab value="cinema"
                    ><v-icon start>mdi-filmstrip</v-icon>劇場から選ぶ</v-tab
                >
                <v-tab value="movie"
                    ><v-icon start>mdi-movie</v-icon>作品から選ぶ</v-tab
                >
            </v-tabs>

            <v-tabs-window v-model="tab">
                <!-- 劇場一覧タブ -->
                <v-tabs-window-item value="cinema">
                    <v-expansion-panels
                        v-model="openRegions"
                        variant="accordion"
                        multiple
                    >
                        <v-expansion-panel
                            v-for="group in cinemaGroups"
                            :key="group.region"
                        >
                            <v-expansion-panel-title>
                                <span class="text-h6">{{ group.region }}</span>
                            </v-expansion-panel-title>
                            <v-expansion-panel-text>
                                <div
                                    v-for="sub in group.prefectures"
                                    :key="sub.prefecture"
                                    class="mb-4"
                                >
                                    <h4 class="text-subtitle-1 text-grey mb-1">
                                        {{ sub.prefecture }}
                                    </h4>
                                    <v-row>
                                        <v-col
                                            v-for="cinema in sub.cinemas"
                                            :key="cinema.code"
                                            cols="12"
                                            sm="6"
                                            md="4"
                                            lg="3"
                                        >
                                            <v-btn
                                                block
                                                size="large"
                                                color="secondary"
                                                variant="elevated"
                                                class="py-6"
                                                @click="
                                                    $router.push({
                                                        name: 'cinema-schedule',
                                                        params: {
                                                            code: cinema.code,
                                                        },
                                                    })
                                                "
                                            >
                                                <v-icon start
                                                    >mdi-filmstrip</v-icon
                                                >
                                                {{
                                                    displayCinemaName(
                                                        cinema.name,
                                                    )
                                                }}
                                            </v-btn>
                                        </v-col>
                                    </v-row>
                                </div>
                            </v-expansion-panel-text>
                        </v-expansion-panel>
                    </v-expansion-panels>
                </v-tabs-window-item>

                <!-- 作品一覧タブ -->
                <v-tabs-window-item value="movie">
                    <div
                        v-if="movieList.length === 0"
                        class="text-center text-grey py-8"
                    >
                        上映中の作品がありません
                    </div>
                    <v-row v-else>
                        <v-col
                            v-for="movie in movieList"
                            :key="movie.key"
                            cols="12"
                            sm="6"
                            md="4"
                            lg="3"
                        >
                            <v-btn
                                block
                                size="large"
                                color="secondary"
                                variant="elevated"
                                class="py-6 text-none movie-btn"
                                @click="
                                    $router.push({
                                        name: 'movie-schedule',
                                        params: { movieKey: movie.key },
                                    })
                                "
                            >
                                <v-icon start>mdi-movie</v-icon>
                                {{ displayMovieName(movie.name) }}
                            </v-btn>
                        </v-col>
                    </v-row>
                </v-tabs-window-item>
            </v-tabs-window>
        </template>

        <!-- 初期ローディング -->
        <div v-else class="text-center py-16">
            <v-progress-circular indeterminate size="64" />
            <p class="mt-4 text-grey">読み込み中...</p>
        </div>
    </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useScheduleStore } from "@/stores/schedule";
import {
    displayCinemaName,
    displayMovieName,
    regionSortIndex,
    prefectureSortIndex,
} from "@/utils/textNormalize";
import type { Cinema } from "@/types";

const store = useScheduleStore();
const tab = ref("cinema");
const loadError = ref<string | null>(null);
const openRegions = ref<number[]>([]);

function formatToday(): string {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}${m}${day}`;
}

async function loadData() {
    loadError.value = null;
    try {
        await store.loadInitialData(formatToday());
    } catch {
        loadError.value = store.error ?? "データの読み込みに失敗しました";
    }
}

interface MovieEntry {
    key: string;
    name: string;
}

const movieList = computed<MovieEntry[]>(() => {
    const seen = new Map<string, string>();
    for (const item of store.allSchedules) {
        const key = normalizeMovieName(item.movieName);
        if (!seen.has(key)) {
            seen.set(key, key);
        }
    }
    return Array.from(seen.entries())
        .map(([key, name]) => ({ key, name }))
        .sort((a, b) => a.name.localeCompare(b.name));
});

interface PrefGroup {
    prefecture: string;
    cinemas: Cinema[];
}
interface RegionGroup {
    region: string;
    prefectures: PrefGroup[];
}

const cinemaGroups = computed<RegionGroup[]>(() => {
    // 劇場毎のスケジュール数をカウント
    const countMap = new Map<string, number>();
    for (const item of store.allSchedules) {
        countMap.set(item.cinemaCode, (countMap.get(item.cinemaCode) ?? 0) + 1);
    }

    const regionMap = new Map<string, Map<string, Cinema[]>>();
    for (const c of store.cinemas) {
        const region = c.region || "不明";
        const pref = c.prefecture || "不明";
        if (!regionMap.has(region)) regionMap.set(region, new Map());
        const prefMap = regionMap.get(region)!;
        if (!prefMap.has(pref)) prefMap.set(pref, []);
        prefMap.get(pref)!.push(c);
    }
    return Array.from(regionMap.entries())
        .sort((a, b) => regionSortIndex(a[0]) - regionSortIndex(b[0]))
        .map(([region, prefMap]) => ({
            region,
            prefectures: Array.from(prefMap.entries())
                .sort(
                    (a, b) =>
                        prefectureSortIndex(a[0]) - prefectureSortIndex(b[0]),
                )
                .map(([prefecture, cinemas]) => ({
                    prefecture,
                    cinemas: [...cinemas].sort(
                        (a, b) =>
                            (countMap.get(b.code) ?? 0) -
                            (countMap.get(a.code) ?? 0),
                    ),
                })),
        }));
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

onMounted(() => {
    if (!store.initialLoaded) {
        loadData();
    }
});
</script>

<style scoped>
.movie-btn {
    white-space: normal !important;
    word-break: break-word;
    height: auto !important;
    min-height: 48px;
}
</style>
