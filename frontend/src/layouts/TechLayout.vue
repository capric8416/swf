<template>
  <div class="tech-layout">
    <!-- 背景效果 -->
    <div class="layout-bg">
      <div class="grid-pattern" />
      <div class="gradient-overlay" />
    </div>

    <!-- 侧边栏 -->
    <sidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />

    <!-- 主内容区 -->
    <div class="main-wrapper" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- 顶部栏 -->
      <app-header @toggle-sidebar="toggleSidebar" />

      <!-- 页面内容 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 扫描线装饰 -->
    <scan-line :speed="4" :opacity="0.3" :particles="true" :particle-count="15" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import AppHeader from '@/components/Header.vue'
import ScanLine from '@/components/tech/ScanLine.vue'

const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<style scoped lang="scss">
.tech-layout {
  position: relative;
  width: 1920px;
  height: 1080px;
  margin: 0 auto;
  background: var(--tech-bg-primary);
  overflow: hidden;
  display: flex;

  .layout-bg {
    position: absolute;
    inset: 0;
    z-index: 0;

    .grid-pattern {
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
      background-size: 50px 50px;
    }

    .gradient-overlay {
      position: absolute;
      inset: 0;
      background: radial-gradient(
        ellipse at 50% 0%,
        rgba(0, 212, 255, 0.05) 0%,
        transparent 50%
      );
    }
  }

  .main-wrapper {
    position: relative;
    z-index: 1;
    flex: 1;
    margin-left: 240px;
    display: flex;
    flex-direction: column;
    transition: margin-left 0.3s ease;

    &.sidebar-collapsed {
      margin-left: 64px;
    }
  }

  .main-content {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    overflow-x: hidden;
  }
}

// 页面切换动画
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
