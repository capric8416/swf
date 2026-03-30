<template>
  <div class="personal-stats-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">个人统计</h1>
        <p class="page-subtitle">查看您的详细编码数据和AI使用统计</p>
      </div>
      <div class="header-actions">
        <el-radio-group v-model="timeRange" size="default">
          <el-radio-button label="7天" />
          <el-radio-button label="30天" />
          <el-radio-button label="90天" />
        </el-radio-group>
        <tech-button :icon="Download" @click="exportData">导出数据</tech-button>
      </div>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-section">
      <div class="overview-card primary">
        <div class="card-bg-icon">
          <el-icon><DocumentChecked /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">总提交数</div>
          <div class="card-value">
            <stat-number :value="overviewData.totalCommits" :duration="2000" />
          </div>
          <div class="card-trend up">
            <el-icon><ArrowUp /></el-icon>
            <span>+{{ overviewData.commitGrowth }}%</span>
          </div>
        </div>
      </div>

      <div class="overview-card success">
        <div class="card-bg-icon">
          <el-icon><EditPen /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">代码行数</div>
          <div class="card-value">
            <stat-number :value="overviewData.totalLines" :duration="2000" />
          </div>
          <div class="card-meta">+{{ overviewData.additions }} / -{{ overviewData.deletions }}</div>
        </div>
      </div>

      <div class="overview-card warning">
        <div class="card-bg-icon">
          <el-icon><Coin /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">Token使用</div>
          <div class="card-value">
            <stat-number :value="overviewData.totalTokens" :duration="2000" />
          </div>
          <div class="card-meta">{{ overviewData.avgTokensPerDay }} / 天</div>
        </div>
      </div>

      <div class="overview-card purple">
        <div class="card-bg-icon">
          <el-icon><Timer /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">编码时长</div>
          <div class="card-value">
            <stat-number :value="overviewData.totalHours" :duration="2000" :decimals="1" />
            <span class="unit">h</span>
          </div>
          <div class="card-meta">{{ overviewData.activeDays }} 个活跃日</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-row">
        <tech-card title="代码贡献热力图" :icon="Calendar" class="heatmap-card">
          <div class="contribution-heatmap">
            <div class="heatmap-header">
              <span class="heatmap-title">{{ heatmapTotal }} 次贡献在过去一年</span>
              <div class="heatmap-legend">
                <span>少</span>
                <div v-for="i in 5" :key="i" class="legend-cell" :class="`level-${i-1}`" />
                <span>多</span>
              </div>
            </div>
            <div class="heatmap-grid">
              <div class="month-labels">
                <span v-for="month in monthLabels" :key="month">{{ month }}</span>
              </div>
              <div class="weeks-container">
                <div v-for="(week, wIndex) in contributionData" :key="wIndex" class="heatmap-week"
                >
                  <div
                    v-for="(day, dIndex) in week"
                    :key="dIndex"
                    class="heatmap-day"
                    :class="`level-${day.level}`"
                    :title="day.date ? `${day.date}: ${day.count} 次贡献` : '无数据'"
                  />
                </div>
              </div>
            </div>
          </div>
        </tech-card>

        <tech-card title="语言统计" :icon="PieChart" class="language-card">
          <tech-chart :option="languageOption" height="280px" />
          <div class="language-list">
            <div
              v-for="lang in languageStats"
              :key="lang.name"
              class="language-item"
            >
              <span class="lang-color" :style="{ background: lang.color }" />
              <span class="lang-name">{{ lang.name }}</span>
              <span class="lang-percent">{{ lang.percent }}%</span>
              <span class="lang-lines">{{ lang.lines.toLocaleString() }} 行</span>
            </div>
          </div>
        </tech-card>
      </div>

      <div class="chart-row">
        <tech-card title="Token使用详情" :icon="DataAnalysis" class="token-card">
          <div class="token-stats">
            <div class="token-stat-item">
              <div class="stat-label">Prompt Tokens</div>
              <div class="stat-value">{{ tokenStats.promptTokens.toLocaleString() }}</div>
              <div class="stat-bar">
                <div
                  class="stat-progress"
                  :style="{ width: `${(tokenStats.promptTokens / tokenStats.totalTokens) * 100}%` }"
                />
              </div>
            </div>
            <div class="token-stat-item">
              <div class="stat-label">Completion Tokens</div>
              <div class="stat-value">{{ tokenStats.completionTokens.toLocaleString() }}</div>
              <div class="stat-bar">
                <div
                  class="stat-progress completion"
                  :style="{ width: `${(tokenStats.completionTokens / tokenStats.totalTokens) * 100}%` }"
                />
              </div>
            </div>
          </div>
          <tech-chart :option="tokenUsageOption" height="200px" />
        </tech-card>

        <tech-card title="活跃时段" :icon="Clock" class="activity-card">
          <tech-chart :option="activityOption" height="320px" />
        </tech-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Download,
  DocumentChecked,
  EditPen,
  Coin,
  Timer,
  Calendar,
  PieChart,
  DataAnalysis,
  Clock,
  ArrowUp,
} from '@element-plus/icons-vue'
import TechCard from '@/components/tech/TechCard.vue'
import TechButton from '@/components/tech/TechButton.vue'
import TechChart from '@/components/tech/TechChart.vue'
import StatNumber from '@/components/tech/StatNumber.vue'
import type { EChartsOption } from 'echarts'

const timeRange = ref('30天')

// 概览数据
const overviewData = ref({
  totalCommits: 1258,
  commitGrowth: 23.5,
  totalLines: 45680,
  additions: 52340,
  deletions: 6660,
  totalTokens: 2580000,
  avgTokensPerDay: '86K',
  totalHours: 186.5,
  activeDays: 45,
})

// 贡献热力图数据
const generateHeatmapData = () => {
  const weeks = 53
  const days = 7
  const data = []
  let total = 0

  for (let w = 0; w < weeks; w++) {
    const week = []
    for (let d = 0; d < days; d++) {
      const count = Math.random() > 0.6 ? Math.floor(Math.random() * 20) : 0
      total += count
      let level = 0
      if (count > 0) level = 1
      if (count >= 5) level = 2
      if (count >= 10) level = 3
      if (count >= 15) level = 4

      week.push({
        date: `2024-${w + 1}-${d + 1}`,
        count,
        level,
      })
    }
    data.push(week)
  }

  return { data, total }
}

const { data: contributionData, total: heatmapTotal } = generateHeatmapData()

const monthLabels = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

// 语言统计
const languageStats = ref([
  { name: 'TypeScript', percent: 45, lines: 205560, color: '#3178c6' },
  { name: 'Python', percent: 25, lines: 114200, color: '#3776ab' },
  { name: 'Vue', percent: 15, lines: 68520, color: '#4fc08d' },
  { name: 'CSS/SCSS', percent: 10, lines: 45680, color: '#c6538c' },
  { name: '其他', percent: 5, lines: 22840, color: '#8b949e' },
])

const languageOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c}%',
  },
  series: [
    {
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#0a1929',
        borderWidth: 2,
      },
      label: { show: false },
      data: languageStats.value.map((lang) => ({
        name: lang.name,
        value: lang.percent,
        itemStyle: { color: lang.color },
      })),
    },
  ],
}))

// Token统计
const tokenStats = ref({
  promptTokens: 1548000,
  completionTokens: 1032000,
  totalTokens: 2580000,
})

const tokenUsageOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
    splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.1)' } },
  },
  series: [
    {
      name: 'Prompt',
      type: 'bar',
      stack: 'total',
      data: [12000, 18000, 15000, 22000, 28000, 10000, 14000],
      itemStyle: { color: '#00d4ff' },
    },
    {
      name: 'Completion',
      type: 'bar',
      stack: 'total',
      data: [8000, 12000, 10000, 15000, 18000, 6000, 9000],
      itemStyle: { color: '#00ff88' },
    },
  ],
}))

// 活跃时段
const activityOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
  xAxis: {
    type: 'category',
    data: Array.from({ length: 24 }, (_, i) => `${i}:00`),
    axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
    splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.1)' } },
  },
  series: [
    {
      name: '活跃度',
      type: 'line',
      smooth: true,
      data: [2, 1, 0, 0, 1, 3, 8, 15, 25, 35, 45, 50, 48, 42, 38, 40, 45, 55, 60, 45, 30, 20, 10, 5],
      lineStyle: { color: '#ff006e', width: 3 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255, 0, 110, 0.4)' },
            { offset: 1, color: 'rgba(255, 0, 110, 0)' },
          ],
        },
      },
      itemStyle: { color: '#ff006e' },
    },
  ],
}))

const exportData = () => {
  console.log('Export data')
}
</script>

<style scoped lang="scss">
.personal-stats-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;

    .header-content {
      .page-title {
        font-size: 24px;
        font-weight: 600;
        color: var(--tech-text-primary);
        margin: 0 0 8px;
      }

      .page-subtitle {
        font-size: 14px;
        color: var(--tech-text-muted);
        margin: 0;
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 16px;
    }
  }

  .overview-section {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;

    .overview-card {
      position: relative;
      padding: 24px;
      background: var(--tech-bg-card);
      border-radius: var(--tech-radius-lg);
      border: 1px solid var(--tech-border-secondary);
      overflow: hidden;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-4px);
        box-shadow: var(--tech-glow-cyan-sm);
      }

      &.primary {
        border-color: rgba(0, 212, 255, 0.3);
        .card-bg-icon { color: rgba(0, 212, 255, 0.1); }
        .card-value { color: var(--tech-cyan); }
      }

      &.success {
        border-color: rgba(0, 255, 136, 0.3);
        .card-bg-icon { color: rgba(0, 255, 136, 0.1); }
        .card-value { color: var(--tech-green); }
      }

      &.warning {
        border-color: rgba(255, 149, 0, 0.3);
        .card-bg-icon { color: rgba(255, 149, 0, 0.1); }
        .card-value { color: var(--tech-orange); }
      }

      &.purple {
        border-color: rgba(157, 78, 221, 0.3);
        .card-bg-icon { color: rgba(157, 78, 221, 0.1); }
        .card-value { color: var(--tech-purple); }
      }

      .card-bg-icon {
        position: absolute;
        right: -20px;
        bottom: -20px;
        font-size: 120px;
        opacity: 0.5;
      }

      .card-content {
        position: relative;
        z-index: 1;

        .card-label {
          font-size: 14px;
          color: var(--tech-text-muted);
          margin-bottom: 8px;
        }

        .card-value {
          font-size: 32px;
          font-weight: 700;
          font-family: var(--tech-font-mono);
          margin-bottom: 8px;

          .unit {
            font-size: 18px;
            margin-left: 4px;
          }
        }

        .card-trend {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;

          &.up {
            color: var(--tech-green);
          }

          &.down {
            color: var(--tech-pink);
          }
        }

        .card-meta {
          font-size: 13px;
          color: var(--tech-text-muted);
        }
      }
    }
  }

  .charts-section {
    display: flex;
    flex-direction: column;
    gap: 20px;

    .chart-row {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 20px;

      &:last-child {
        grid-template-columns: 1fr 1fr;
      }
    }

    .heatmap-card {
      .contribution-heatmap {
        padding: 16px;

        .heatmap-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;

          .heatmap-title {
            font-size: 14px;
            color: var(--tech-text-secondary);
          }

          .heatmap-legend {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            color: var(--tech-text-muted);

            .legend-cell {
              width: 12px;
              height: 12px;
              border-radius: 2px;

              &.level-0 { background: rgba(0, 212, 255, 0.05); }
              &.level-1 { background: rgba(0, 212, 255, 0.2); }
              &.level-2 { background: rgba(0, 212, 255, 0.4); }
              &.level-3 { background: rgba(0, 212, 255, 0.6); }
              &.level-4 { background: rgba(0, 212, 255, 0.9); }
            }
          }
        }

        .heatmap-grid {
          .month-labels {
            display: flex;
            gap: 28px;
            margin-bottom: 8px;
            padding-left: 24px;
            font-size: 11px;
            color: var(--tech-text-muted);
          }

          .weeks-container {
            display: flex;
            gap: 4px;
            overflow-x: auto;

            .heatmap-week {
              display: flex;
              flex-direction: column;
              gap: 4px;

              .heatmap-day {
                width: 12px;
                height: 12px;
                border-radius: 2px;
                transition: all 0.2s ease;

                &.level-0 { background: rgba(0, 212, 255, 0.05); }
                &.level-1 { background: rgba(0, 212, 255, 0.2); }
                &.level-2 { background: rgba(0, 212, 255, 0.4); }
                &.level-3 { background: rgba(0, 212, 255, 0.6); }
                &.level-4 { background: rgba(0, 212, 255, 0.9); }

                &:hover {
                  transform: scale(1.3);
                  box-shadow: 0 0 8px rgba(0, 212, 255, 0.5);
                }
              }
            }
          }
        }
      }
    }

    .language-card {
      .language-list {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--tech-border-secondary);

        .language-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 0;
          font-size: 13px;

          .lang-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
          }

          .lang-name {
            flex: 1;
            color: var(--tech-text-primary);
          }

          .lang-percent {
            width: 40px;
            color: var(--tech-cyan);
            font-family: var(--tech-font-mono);
            font-weight: 600;
          }

          .lang-lines {
            width: 100px;
            text-align: right;
            color: var(--tech-text-muted);
            font-family: var(--tech-font-mono);
          }
        }
      }
    }

    .token-card {
      .token-stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid var(--tech-border-secondary);

        .token-stat-item {
          .stat-label {
            font-size: 12px;
            color: var(--tech-text-muted);
            margin-bottom: 8px;
          }

          .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--tech-text-primary);
            font-family: var(--tech-font-mono);
            margin-bottom: 8px;
          }

          .stat-bar {
            height: 4px;
            background: var(--tech-bg-tertiary);
            border-radius: 2px;
            overflow: hidden;

            .stat-progress {
              height: 100%;
              background: var(--tech-cyan);
              border-radius: 2px;
              transition: width 0.5s ease;

              &.completion {
                background: var(--tech-green);
              }
            }
          }
        }
      }
    }
  }
}
</style>
