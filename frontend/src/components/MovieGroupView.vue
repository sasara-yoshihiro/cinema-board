<template>
    <div v-if="groups.length === 0" class="text-center text-grey py-8">
        スケジュールデータがありません
    </div>

    <div v-else>
        <v-expansion-panels v-model="openPanels" variant="accordion" multiple>
            <v-expansion-panel v-for="group in groups" :key="group.movieName">
                <v-expansion-panel-title>
                    <div class="d-flex align-center ga-2">
                        <v-icon color="primary">mdi-movie</v-icon>
                        <a
                            v-if="group.items[0]?.movieCode"
                            :href="
                                'https://hlo.tohotheater.jp/net/movie/TNPI3060J01.do?sakuhin_cd=' +
                                group.items[0].movieCode
                            "
                            target="_blank"
                            rel="noopener"
                            class="text-h6 movie-link"
                            @click.stop
                            >{{ group.movieName }}</a
                        >
                        <span v-else class="text-h6">{{
                            group.movieName
                        }}</span>
                        <v-chip size="small" color="secondary" class="ml-2"
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
                                        item.seatStatus === '販売終了',
                                }"
                            >
                                <td>{{ extractLabel(item.movieName) }}</td>
                                <td>{{ item.screenName }}</td>
                                <td>{{ item.startTime }}</td>
                                <td>{{ item.endTime }}</td>
                                <td>{{ item.duration }}分</td>
                                <td>
                                    <v-chip
                                        :color="seatColor(item.seatStatus)"
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
    </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { ScheduleItem } from "@/types";

interface MovieGroup {
    movieName: string;
    items: ScheduleItem[];
}

defineProps<{ groups: MovieGroup[] }>();

const openPanels = ref<number[]>([]);

function collapseAll() {
    openPanels.value = [];
}

defineExpose({ collapseAll });

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
