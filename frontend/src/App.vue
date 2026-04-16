<template>
    <v-app>
        <v-app-bar color="primary" density="comfortable">
            <v-btn v-if="showBack" icon @click="$router.push('/')">
                <v-icon>mdi-arrow-left</v-icon>
            </v-btn>
            <v-btn v-else icon @click="$router.push('/')">
                <v-icon>mdi-movie-open</v-icon>
            </v-btn>
            <v-toolbar-title>CinemaBoard</v-toolbar-title>
        </v-app-bar>
        <v-main>
            <router-view />
        </v-main>
    </v-app>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const showBack = computed(() => route.name !== "main");
</script>
