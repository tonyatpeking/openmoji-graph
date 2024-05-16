<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import GraphDiv from "./components/GraphDiv.vue";
</script>

<template>
  <div class="container">
    <h1>OpenMoji Graph Explorer</h1>
    <GraphDiv />
  </div>
</template>

<style scoped>
.logo.vite:hover {
  filter: drop-shadow(0 0 2em #747bff);
}

.logo.vue:hover {
  filter: drop-shadow(0 0 2em #249b73);
}

* {
  margin: 0;
  padding: 0;
}



html,
body {
  overflow: hidden;
}
</style>
