<template>
    <div v-if="screens.length === 0" class="text-center text-grey py-8">
        スケジュールデータがありません
    </div>

    <div v-else class="timeline-container">
        <!-- 時間軸ヘッダ -->
        <div class="timeline-header">
            <div class="screen-label-header"></div>
            <div class="time-axis">
                <div
                    v-for="h in hours"
                    :key="h"
                    class="time-tick"
                    :style="{ left: timeToPercent(h + ':00') + '%' }"
                >
                    {{ h }}:00
                </div>
                <!-- 15分毎罫線 (ヘッダ) -->
                <div
                    v-for="q in quarterMarks"
                    :key="'hq-' + q"
                    class="grid-line-quarter"
                    :style="{ left: minuteToPercent(q) + '%' }"
                />
                <!-- 現在時刻線 (ヘッダ) -->
                <div
                    v-if="nowPercent !== null"
                    class="now-line"
                    :style="{ left: nowPercent + '%' }"
                />
            </div>
        </div>

        <!-- スクリーン行 -->
        <div
            v-for="screen in screens"
            :key="screen.screenName"
            class="screen-row"
        >
            <div class="screen-label">{{ screen.screenName }}</div>
            <div class="screen-timeline">
                <!-- 時間罫線 (1時間毎) -->
                <div
                    v-for="h in hours"
                    :key="'grid-' + h"
                    class="grid-line"
                    :style="{ left: timeToPercent(h + ':00') + '%' }"
                />
                <!-- 15分毎罫線 -->
                <div
                    v-for="q in quarterMarks"
                    :key="'q-' + q"
                    class="grid-line-quarter"
                    :style="{ left: minuteToPercent(q) + '%' }"
                />
                <!-- 現在時刻線 -->
                <div
                    v-if="nowPercent !== null"
                    class="now-line"
                    :style="{ left: nowPercent + '%' }"
                />
                <!-- 上映ブロック -->
                <div
                    v-for="(item, i) in screen.items"
                    :key="i"
                    class="show-block"
                    :style="{
                        left: timeToPercent(item.startTime) + '%',
                        width:
                            durationPercent(item.startTime, item.endTime) + '%',
                    }"
                    :class="seatClass(item.seatStatus)"
                    @click="openDetail(item)"
                >
                    <div class="show-title">{{ item.movieName }}</div>
                    <div class="show-time">
                        {{ item.startTime }}–{{ item.endTime }}
                    </div>
                    <div v-if="item.seatStatus" class="show-seat">
                        {{ item.seatStatus }}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 詳細ダイアログ (Liquid Glass風) -->
    <v-dialog v-model="detailOpen" max-width="420">
        <div class="glass-card">
            <h3 class="glass-title">
                <a
                    v-if="detailItem?.movieCode"
                    :href="
                        'https://hlo.tohotheater.jp/net/movie/TNPI3060J01.do?sakuhin_cd=' +
                        detailItem.movieCode
                    "
                    target="_blank"
                    rel="noopener"
                    class="movie-link"
                    >{{ detailItem?.movieName }}</a
                >
                <template v-else>{{ detailItem?.movieName }}</template>
            </h3>
            <v-divider
                class="my-2"
                style="border-color: rgba(255, 255, 255, 0.15)"
            />
            <table class="glass-table">
                <tbody>
                    <tr>
                        <td>スクリーン</td>
                        <td>{{ detailItem?.screenName }}</td>
                    </tr>
                    <tr>
                        <td>開始</td>
                        <td>{{ detailItem?.startTime }}</td>
                    </tr>
                    <tr>
                        <td>終了</td>
                        <td>{{ detailItem?.endTime }}</td>
                    </tr>
                    <tr>
                        <td>上映時間</td>
                        <td>{{ detailItem?.duration }}分</td>
                    </tr>
                    <tr>
                        <td>座席状況</td>
                        <td>{{ detailItem?.seatStatus || "—" }}</td>
                    </tr>
                    <tr v-if="detailItem?.movieNameEn">
                        <td>英語名</td>
                        <td>{{ detailItem.movieNameEn }}</td>
                    </tr>
                </tbody>
            </table>
            <div class="text-right mt-4">
                <v-btn variant="text" @click="detailOpen = false">閉じる</v-btn>
            </div>
        </div>
    </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from "vue";
import type { ScheduleItem } from "@/types";

interface ScreenGroup {
    screenName: string;
    items: ScheduleItem[];
}

const props = defineProps<{ screens: ScreenGroup[] }>();

// --- 詳細ダイアログ ---
const detailOpen = ref(false);
const detailItem = ref<ScheduleItem | null>(null);

function openDetail(item: ScheduleItem) {
    detailItem.value = item;
    detailOpen.value = true;
}

// --- 現在時刻線 ---
const nowMinutes = ref(currentMinutes());
let timer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
    timer = setInterval(() => {
        nowMinutes.value = currentMinutes();
    }, 30_000);
});
onBeforeUnmount(() => {
    if (timer) clearInterval(timer);
});

function currentMinutes(): number {
    const now = new Date();
    return now.getHours() * 60 + now.getMinutes();
}

const nowPercent = computed(() => {
    if (hours.value.length === 0) return null;
    const min = hours.value[0] * 60;
    const max = (hours.value[hours.value.length - 1] + 1) * 60;
    if (nowMinutes.value < min || nowMinutes.value > max) return null;
    return ((nowMinutes.value - min) / (max - min)) * 100;
});
// 表示する時間範囲を動的に計算
const hours = computed(() => {
    let minH = 24;
    let maxH = 0;
    for (const s of props.screens) {
        for (const item of s.items) {
            const sh = parseHour(item.startTime);
            const eh = parseHour(item.endTime);
            if (sh < minH) minH = sh;
            if (eh > maxH) maxH = eh;
        }
    }
    if (minH > maxH) return [];
    const start = Math.max(0, minH);
    const end = Math.min(30, maxH + 1); // 深夜帯のため 30 まで許容
    const arr: number[] = [];
    for (let h = start; h <= end; h++) arr.push(h);
    return arr;
});

// 15分毎のマーク (毎正時を除く)
const quarterMarks = computed(() => {
    const marks: number[] = [];
    for (const h of hours.value) {
        marks.push(h * 60 + 15);
        marks.push(h * 60 + 30);
        marks.push(h * 60 + 45);
    }
    return marks;
});

function minuteToPercent(m: number): number {
    if (hours.value.length === 0) return 0;
    const min = hours.value[0] * 60;
    const max = (hours.value[hours.value.length - 1] + 1) * 60;
    return ((m - min) / (max - min)) * 100;
}

function parseHour(t: string): number {
    const parts = t.split(":");
    return parseInt(parts[0] || "0", 10);
}

function timeToMinutes(t: string): number {
    const parts = t.split(":");
    return parseInt(parts[0] || "0", 10) * 60 + parseInt(parts[1] || "0", 10);
}

function timeToPercent(t: string): number {
    if (hours.value.length === 0) return 0;
    const min = hours.value[0] * 60;
    const max = (hours.value[hours.value.length - 1] + 1) * 60;
    const range = max - min;
    return ((timeToMinutes(t) - min) / range) * 100;
}

function durationPercent(start: string, end: string): number {
    if (hours.value.length === 0) return 0;
    const min = hours.value[0] * 60;
    const max = (hours.value[hours.value.length - 1] + 1) * 60;
    const range = max - min;
    return ((timeToMinutes(end) - timeToMinutes(start)) / range) * 100;
}

function seatClass(status: string): string {
    switch (status) {
        case "余裕あり":
            return "seat-ok";
        case "残りわずか":
            return "seat-few";
        case "満席":
            return "seat-full";
        case "販売終了":
            return "seat-closed";
        default:
            return "";
    }
}
</script>

<style scoped>
.timeline-container {
    overflow-x: auto;
    min-width: 100%;
}

.timeline-header {
    display: flex;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    position: sticky;
    top: 0;
    background: rgb(var(--v-theme-surface));
    z-index: 1;
}

.screen-label-header {
    min-width: 120px;
    flex-shrink: 0;
}

.time-axis {
    position: relative;
    flex: 1;
    height: 32px;
    min-width: 900px;
}

.time-tick {
    position: absolute;
    top: 4px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    transform: translateX(-50%);
    white-space: nowrap;
}

.screen-row {
    display: flex;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    min-height: 72px;
}

.screen-label {
    min-width: 120px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    padding: 0 8px;
    font-weight: 600;
    font-size: 13px;
    background: rgba(255, 255, 255, 0.03);
}

.screen-timeline {
    position: relative;
    flex: 1;
    min-width: 900px;
}

.grid-line {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: rgba(255, 255, 255, 0.3);
    z-index: 0;
}

.grid-line-quarter {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 1px;
    background: rgba(255, 255, 255, 0.1);
    z-index: 0;
}

.show-block {
    position: absolute;
    top: 4px;
    bottom: 4px;
    border-radius: 4px;
    padding: 2px 4px;
    overflow: hidden;
    font-size: 11px;
    line-height: 1.3;
    cursor: pointer;
    background: rgba(30, 136, 229, 0.7);
    border-left: 3px solid rgb(30, 136, 229);
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: filter 0.15s;
}

.show-block:hover {
    filter: brightness(1.25);
}

.show-block.seat-ok {
    background: rgba(76, 175, 80, 0.5);
    border-left-color: #4caf50;
}
.show-block.seat-few {
    background: rgba(255, 152, 0, 0.5);
    border-left-color: #ff9800;
}
.show-block.seat-full {
    background: rgba(244, 67, 54, 0.5);
    border-left-color: #f44336;
}
.show-block.seat-closed {
    background: rgba(158, 158, 158, 0.4);
    border-left-color: #9e9e9e;
}

.show-title {
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.show-time {
    white-space: nowrap;
    opacity: 0.8;
}
.show-seat {
    white-space: nowrap;
    opacity: 0.7;
}

/* 現在時刻線 */
.now-line {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: rgba(244, 67, 54, 0.55);
    z-index: 2;
    pointer-events: none;
}

/* Liquid Glass ダイアログ */
.glass-card {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(24px) saturate(1.4);
    -webkit-backdrop-filter: blur(24px) saturate(1.4);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 16px;
    padding: 24px;
    color: #fff;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
}

.glass-title {
    font-size: 1.25rem;
    font-weight: 700;
}

.movie-link {
    color: inherit;
    text-decoration: none;
}
.movie-link:hover {
    text-decoration: underline;
}

.glass-table td {
    padding: 6px 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.glass-table td:first-child {
    width: 100px;
    opacity: 0.65;
    font-size: 0.85rem;
}
</style>
