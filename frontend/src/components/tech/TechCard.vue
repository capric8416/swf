<template>
  <div
    class="tech-card"
    :class="[
      `variant-${variant}`,
      { 'hoverable': hoverable, 'glow': glow, 'corner': cornerDecoration }
    ]"
    :style="customStyle"
  >
    <div v-if="title || $slots.header" class="card-header">
      <div class="header-content">
        <span v-if="icon" class="header-icon">
          <el-icon><component :is="icon" /></el-icon>
        </span>
        <h3 v-if="title" class="card-title">{{ title }}</h3>
        <slot name="header-extra" />
      </div>
      <div v-if="$slots.header" class="header-slot">
        <slot name="header" />
      </div>
    </div>
    <div class="card-body" :class="{ 'no-padding': noPadding }">
      <slot />
    </div>
    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer" />
    </div>
    <div v-if="scanLine" class="scan-line" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'

interface Props {
  title?: string
  icon?: Component
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
  hoverable?: boolean
  glow?: boolean
  cornerDecoration?: boolean
  scanLine?: boolean
  noPadding?: boolean
  height?: string
  minHeight?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  hoverable: true,
  glow: false,
  cornerDecoration: true,
  scanLine: false,
  noPadding: false,
})

const customStyle = computed(() => {
  const style: Record<string, string> = {}
  if (props.height) style.height = props.height
  if (props.minHeight) style.minHeight = props.minHeight
  return style
})
</script>

<style scoped lang="scss">
.tech-card {
  position: relative;
  background: var(--tech-bg-card);
  border: 1px solid var(--tech-border-secondary);
  border-radius: var(--tech-radius-lg);
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;

  // 角标装饰
  &.corner::before,
  &.corner::after {
    content: '';
    position: absolute;
    width: 12px;
    height: 12px;
    border: 2px solid var(--tech-cyan);
    transition: all 0.3s ease;
    z-index: 1;
  }

  &.corner::before {
    top: -1px;
    left: -1px;
    border-right: none;
    border-bottom: none;
    border-top-left-radius: var(--tech-radius-lg);
  }

  &.corner::after {
    bottom: -1px;
    right: -1px;
    border-left: none;
    border-top: none;
    border-bottom-right-radius: var(--tech-radius-lg);
  }

  // 变体样式
  &.variant-primary {
    border-color: rgba(0, 212, 255, 0.3);

    &.corner::before,
    &.corner::after {
      border-color: var(--tech-cyan);
    }
  }

  &.variant-success {
    border-color: rgba(0, 255, 136, 0.3);

    &.corner::before,
    &.corner::after {
      border-color: var(--tech-green);
    }
  }

  &.variant-warning {
    border-color: rgba(255, 149, 0, 0.3);

    &.corner::before,
    &.corner::after {
      border-color: var(--tech-orange);
    }
  }

  &.variant-danger {
    border-color: rgba(255, 0, 110, 0.3);

    &.corner::before,
    &.corner::after {
      border-color: var(--tech-pink);
    }
  }

  // 悬停效果
  &.hoverable:hover {
    border-color: var(--tech-border-primary);
    box-shadow: var(--tech-glow-cyan-sm);
    transform: translateY(-2px);

    &.corner::before,
    &.corner::after {
      width: 20px;
      height: 20px;
    }
  }

  // 发光效果
  &.glow {
    box-shadow: var(--tech-glow-cyan-sm);
    animation: pulse-glow 3s ease-in-out infinite;
  }

  // 头部
  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--tech-border-secondary);
    display: flex;
    align-items: center;
    justify-content: space-between;

    .header-content {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .header-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      background: rgba(0, 212, 255, 0.1);
      border-radius: var(--tech-radius-sm);
      color: var(--tech-cyan);
    }

    .card-title {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--tech-text-primary);
      font-family: var(--tech-font-chinese);
    }
  }

  // 内容区
  .card-body {
    flex: 1;
    padding: 20px;
    overflow: auto;

    &.no-padding {
      padding: 0;
    }
  }

  // 底部
  .card-footer {
    padding: 12px 20px;
    border-top: 1px solid var(--tech-border-secondary);
    background: rgba(0, 0, 0, 0.2);
  }

  // 扫描线
  .scan-line {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(
      90deg,
      transparent,
      var(--tech-cyan),
      transparent
    );
    animation: scan-line 3s linear infinite;
    opacity: 0.6;
    pointer-events: none;
  }
}

@keyframes scan-line {
  0% {
    transform: translateY(-100%);
  }
  100% {
    transform: translateY(calc(100% + 400px));
  }
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
  }
  50% {
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.4);
  }
}
</style>
