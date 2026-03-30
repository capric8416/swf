<template>
  <div ref="chartContainer" class="tech-chart" :style="containerStyle">
    <div v-if="title" class="chart-header">
      <span class="chart-title">{{ title }}</span>
      <slot name="extra" />
    </div>
    <div ref="chartRef" class="chart-body" :style="chartStyle" />
    <div v-if="loading" class="chart-loading">
      <div class="loading-spinner" />
      <span>加载中...</span>
    </div>
    <div v-if="cornerDecoration" class="corner-decoration">
      <span class="corner top-left" />
      <span class="corner top-right" />
      <span class="corner bottom-left" />
      <span class="corner bottom-right" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'

interface Props {
  title?: string
  option: EChartsOption
  height?: string
  loading?: boolean
  autoResize?: boolean
  cornerDecoration?: boolean
  theme?: 'dark' | 'light'
}

const props = withDefaults(defineProps<Props>(), {
  height: '300px',
  loading: false,
  autoResize: true,
  cornerDecoration: true,
  theme: 'dark',
})

const chartRef = ref<HTMLElement>()
const chartContainer = ref<HTMLElement>()
const chartInstance = ref<ECharts | null>(null)

const containerStyle = computed(() => ({
  height: props.height,
}))

const chartStyle = computed(() => ({
  height: props.title ? `calc(100% - 40px)` : '100%',
}))

// 科技风深色主题
const techDarkTheme = {
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: 'JetBrains Mono, Consolas, monospace',
  },
  title: {
    textStyle: {
      color: '#ffffff',
    },
    subtextStyle: {
      color: 'rgba(255, 255, 255, 0.6)',
    },
  },
  line: {
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
  },
  categoryAxis: {
    axisLine: {
      lineStyle: {
        color: 'rgba(0, 212, 255, 0.3)',
      },
    },
    axisTick: {
      lineStyle: {
        color: 'rgba(0, 212, 255, 0.3)',
      },
    },
    axisLabel: {
      color: 'rgba(255, 255, 255, 0.6)',
    },
    splitLine: {
      lineStyle: {
        color: 'rgba(0, 212, 255, 0.1)',
      },
    },
  },
  valueAxis: {
    axisLine: {
      lineStyle: {
        color: 'rgba(0, 212, 255, 0.3)',
      },
    },
    axisTick: {
      lineStyle: {
        color: 'rgba(0, 212, 255, 0.3)',
      },
    },
    axisLabel: {
      color: 'rgba(255, 255, 255, 0.6)',
    },
    splitLine: {
      lineStyle: {
        color: 'rgba(0, 212, 255, 0.1)',
      },
    },
  },
  legend: {
    textStyle: {
      color: 'rgba(255, 255, 255, 0.8)',
    },
  },
  tooltip: {
    backgroundColor: 'rgba(13, 33, 55, 0.95)',
    borderColor: 'rgba(0, 212, 255, 0.3)',
    textStyle: {
      color: '#ffffff',
    },
    extraCssText: 'backdrop-filter: blur(10px);',
  },
}

// 科技风配色
const techColors = [
  '#00d4ff', // 科技青
  '#00ff88', // 荧光绿
  '#ff006e', // 霓虹粉
  '#ff9500', // 橙色
  '#9d4edd', // 紫色
  '#00b4d8', // 浅蓝
  '#90e0ef', // 淡青
  '#ff99c8', // 淡粉
]

const initChart = () => {
  if (!chartRef.value) return

  // 注册主题
  echarts.registerTheme('tech-dark', techDarkTheme)

  chartInstance.value = echarts.init(chartRef.value, 'tech-dark', {
    renderer: 'canvas',
  })

  const mergedOption: EChartsOption = {
    color: techColors,
    ...props.option,
  }

  chartInstance.value.setOption(mergedOption)

  // 自动调整大小
  if (props.autoResize) {
    window.addEventListener('resize', handleResize)
  }
}

const handleResize = () => {
  chartInstance.value?.resize()
}

const updateChart = () => {
  if (chartInstance.value) {
    chartInstance.value.setOption(props.option, true)
  }
}

// 监听配置变化
watch(() => props.option, updateChart, { deep: true })

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

onUnmounted(() => {
  if (props.autoResize) {
    window.removeEventListener('resize', handleResize)
  }
  chartInstance.value?.dispose()
})

defineExpose({
  chartInstance,
  resize: handleResize,
  updateChart,
})
</script>

<style scoped lang="scss">
.tech-chart {
  position: relative;
  background: var(--tech-bg-card);
  border: 1px solid var(--tech-border-secondary);
  border-radius: var(--tech-radius-lg);
  overflow: hidden;

  .chart-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--tech-border-secondary);

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--tech-text-primary);
      font-family: var(--tech-font-chinese);
    }
  }

  .chart-body {
    width: 100%;
    padding: 8px;
  }

  .chart-loading {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: rgba(10, 25, 41, 0.8);
    backdrop-filter: blur(4px);
    color: var(--tech-cyan);
    font-size: 14px;

    .loading-spinner {
      width: 32px;
      height: 32px;
      border: 2px solid var(--tech-border-secondary);
      border-top-color: var(--tech-cyan);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
  }

  .corner-decoration {
    position: absolute;
    inset: 0;
    pointer-events: none;

    .corner {
      position: absolute;
      width: 12px;
      height: 12px;
      border: 2px solid var(--tech-cyan);
      opacity: 0.5;

      &.top-left {
        top: -1px;
        left: -1px;
        border-right: none;
        border-bottom: none;
        border-top-left-radius: var(--tech-radius-lg);
      }

      &.top-right {
        top: -1px;
        right: -1px;
        border-left: none;
        border-bottom: none;
        border-top-right-radius: var(--tech-radius-lg);
      }

      &.bottom-left {
        bottom: -1px;
        left: -1px;
        border-right: none;
        border-top: none;
        border-bottom-left-radius: var(--tech-radius-lg);
      }

      &.bottom-right {
        bottom: -1px;
        right: -1px;
        border-left: none;
        border-top: none;
        border-bottom-right-radius: var(--tech-radius-lg);
      }
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
