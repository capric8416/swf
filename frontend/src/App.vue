<template>
  <div id="app" class="tech-app">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // 如果本地有token，尝试获取用户信息
  if (authStore.token) {
    authStore.fetchCurrentUser()
  }
})
</script>

<style scoped lang="scss">
.tech-app {
  width: 100%;
  min-width: 1920px;
  min-height: 1080px;
  background: var(--tech-bg-primary);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
