<template>
  <div ref="chartContainer" class="base-chart" :style="containerStyle">
    <div ref="chartRef" class="chart-body" />
    <div v-if="loading" class="chart-loading">
      <div class="loading-spinner" />
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  onMounted,
  onUnmounted,
  watch,
  nextTick,
  provide,
  inject,
} from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'

export interface ChartProps {
  option: EChartsOption
  width?: string
  height?: string
  loading?: boolean
  autoResize?: boolean
  theme?: string | object
  renderer?: 'canvas' | 'svg'
  notMerge?: boolean
  lazyUpdate?: boolean
  silent?: boolean
}

const props = withDefaults(defineProps<ChartProps>(), {
  width: '100%',
  height: '300px',
  loading: false,
  autoResize: true,
  theme: 'dark',
  renderer: 'canvas',
  notMerge: false,
  lazyUpdate: false,
  silent: false,
})

const emit = defineEmits<{
  click: [params: any]
  dblclick: [params: any]
  mousedown: [params: any]
  mousemove: [params: any]
  mouseup: [params: any]
  mouseover: [params: any]
  mouseout: [params: any]
  resize: [width: number, height: number]
  finished: []
}>()

const chartRef = ref<HTMLElement>()
const chartContainer = ref<HTMLElement>()
const chartInstance = ref<ECharts | null>(null)
const resizeObserver = ref<ResizeObserver | null>(null)

// 容器样式
const containerStyle = computed(() => ({
  width: props.width,
  height: props.height,
}))

// 默认主题配置
const defaultDarkTheme = {
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: 'JetBrains Mono, Consolas, monospace',
  },
  title: {
    textStyle: { color: '#ffffff' },
    subtextStyle: { color: 'rgba(255, 255, 255, 0.6)' },
  },
  line: { smooth: true, symbol: 'circle', symbolSize: 8 },
  categoryAxis: {
    axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
    axisTick: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
    splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.1)' } },
  },
  valueAxis: {
    axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
    axisTick: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
    splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.1)' } },
  },
  legend: { textStyle: { color: 'rgba(255, 255, 255, 0.8)' } },
  tooltip: {
    backgroundColor: 'rgba(13, 33, 55, 0.95)',
    borderColor: 'rgba(0, 212, 255, 0.3)',
    textStyle: { color: '#ffffff' },
    extraCssText: 'backdrop-filter: blur(10px);',
  },
}

const defaultLightTheme = {
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: 'JetBrains Mono, Consolas, monospace',
  },
  title: {
    textStyle: { color: '#333333' },
    subtextStyle: { color: '#666666' },
  },
  line: { smooth: true, symbol: 'circle', symbolSize: 8 },
  categoryAxis: {
    axisLine: { lineStyle: { color: '#cccccc' } },
    axisTick: { lineStyle: { color: '#cccccc' } },
    axisLabel: { color: '#666666' },
    splitLine: { lineStyle: { color: '#eeeeee' } },
  },
  valueAxis: {
    axisLine: { lineStyle: { color: '#cccccc' } },
    axisTick: { lineStyle: { color: '#cccccc' } },
    axisLabel: { color: '#666666' },
    splitLine: { lineStyle: { color: '#eeeeee' } },
  },
  legend: { textStyle: { color: '#333333' } },
  tooltip: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#cccccc',
    textStyle: { color: '#333333' },
    extraCssText: 'box-shadow: 0 2px 8px rgba(0,0,0,0.15);',
  },
}

// 科技风配色
const techColors = [
  '#00d4ff', '#00ff88', '#ff006e', '#ff9500',
  '#9d4edd', '#00b4d8', '#90e0ef', '#ff99c8',
]

// 注册主题
const registeredThemes = new Set<string>()
const registerThemes = () => {
  if (!registeredThemes.has('tech-dark')) {
    echarts.registerTheme('tech-dark', defaultDarkTheme)
    registeredThemes.add('tech-dark')
  }
  if (!registeredThemes.has('tech-light')) {
    echarts.registerTheme('tech-light', defaultLightTheme)
    registeredThemes.add('tech-light')
  }
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  registerThemes()

  const themeName = typeof props.theme === 'string' ? props.theme : 'dark'

  chartInstance.value = echarts.init(chartRef.value, themeName, {
    renderer: props.renderer,
  })

  // 设置配置
  updateChart()

  // 绑定事件
  bindEvents()

  // 设置ResizeObserver
  if (props.autoResize && window.ResizeObserver) {
    resizeObserver.value = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        handleResize()
        emit('resize', width, height)
      }
    })
    resizeObserver.value.observe(chartContainer.value!)
  }
}

// 更新图表配置
const updateChart = () => {
  if (!chartInstance.value) return

  const mergedOption: EChartsOption = {
    color: techColors,
    ...props.option,
  }

  chartInstance.value.setOption(mergedOption, {
    notMerge: props.notMerge,
    lazyUpdate: props.lazyUpdate,
    silent: props.silent,
  })
}

// 绑定事件
const bindEvents = () => {
  if (!chartInstance.value) return

  const events = ['click', 'dblclick', 'mousedown', 'mousemove', 'mouseup', 'mouseover', 'mouseout']
  events.forEach((event) => {
    chartInstance.value!.on(event, (params: any) => {
      emit(event as any, params)
    })
  })

  chartInstance.value.on('finished', () => {
    emit('finished')
  })
}

// 调整大小
const handleResize = () => {
  chartInstance.value?.resize()
}

// 监听配置变化
watch(() => props.option, updateChart, { deep: true })

// 监听主题变化
watch(() => props.theme, () => {
  disposeChart()
  initChart()
})

// 销毁图表
const disposeChart = () => {
  resizeObserver.value?.disconnect()
  resizeObserver.value = null
  chartInstance.value?.dispose()
  chartInstance.value = null
}

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

onUnmounted(() => {
  disposeChart()
})

// 暴露方法
defineExpose({
  chartInstance,
  resize: handleResize,
  updateChart,
  getOption: () => chartInstance.value?.getOption(),
  clear: () => chartInstance.value?.clear(),
  dispatchAction: (payload: any) => chartInstance.value?.dispatchAction(payload),
  convertToPixel: (finder: any, value: any) => chartInstance.value?.convertToPixel(finder, value),
  convertFromPixel: (finder: any, value: any) => chartInstance.value?.convertFromPixel(finder, value),
  containPixel: (finder: any, value: any) => chartInstance.value?.containPixel(finder, value),
  getDataURL: (opts?: any) => chartInstance.value?.getDataURL(opts),
  getConnectedDataURL: (opts?: any) => chartInstance.value?.getConnectedDataURL(opts),
  appendData: (params: any) => chartInstance.value?.appendData(params),
})
</script>

<style scoped lang="scss">
.base-chart {
  position: relative;
  width: 100%;

  .chart-body {
    width: 100%;
    height: 100%;
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
    color: var(--tech-cyan, #00d4ff);
    font-size: 14px;

    .loading-spinner {
      width: 32px;
      height: 32px;
      border: 2px solid rgba(0, 212, 255, 0.2);
      border-top-color: var(--tech-cyan, #00d4ff);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
