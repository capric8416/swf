<template>
  <div class="project-stats-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">项目统计</h1>
        <p class="page-subtitle">查看各项目的详细统计数据和成员贡献</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedProject" placeholder="选择项目" style="width: 200px">
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
        <tech-button :icon="Refresh" @click="refreshData">刷新</tech-button>
      </div>
    </div>

    <!-- 项目概览 -->
    <div class="project-overview">
      <div class="project-info-card">
        <div class="project-header">
          <div class="project-icon">
            <el-icon><FolderOpened /></el-icon>
          </div>
          <div class="project-details">
            <h2>{{ currentProject?.name || '选择项目' }}</h2>
            <p>{{ currentProject?.description || '暂无描述' }}</p>
          </div>
        </div>
        <div class="project-meta">
          <div class="meta-item">
            <span class="meta-label">仓库地址</span>
            <a :href="currentProject?.repoUrl" target="_blank" class="meta-value link">
              {{ currentProject?.repoUrl || '-' }}
            </a>
          </div>
          <div class="meta-item">
            <span class="meta-label">创建时间</span>
            <span class="meta-value">{{ currentProject?.createdAt || '-' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">状态</span>
            <el-tag :type="currentProject?.status === 'active' ? 'success' : 'info'">
              {{ currentProject?.status === 'active' ? '活跃' : '归档' }}
            </el-tag>
          </div>
        </div>
      </div>

      <div class="project-stats-grid">
        <data-panel
          v-for="(stat, index) in projectStats"
          :key="index"
          :label="stat.label"
          :value="stat.value"
          :icon="stat.icon"
          :icon-color="stat.iconColor"
          :icon-bg-color="stat.iconBgColor"
          :suffix="stat.suffix"
        />
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-row">
        <tech-card title="提交趋势" :icon="TrendCharts" class="trend-card">
          <tech-chart :option="commitTrendOption" height="300px" />
        </tech-card>

        <tech-card title="语言分布" :icon="PieChart" class="language-card">
          <tech-chart :option="languageDistOption" height="300px" />
        </tech-card>
      </div>
    </div>

    <!-- 成员贡献 -->
    <tech-card title="成员贡献排行" :icon="UserFilled" class="members-card">
      <div class="members-table">
        <div class="table-header"
003e
          <div class="th rank">排名</div>
          <div class="th user">成员</div>
          <div class="th commits">提交数</div>
          <div class="th additions">新增代码</div>
          <div class="th deletions">删除代码</div>
          <div class="th tokens">Token使用</div>
          <div class="th activity">活跃度</div>
        </div>
        <div class="table-body">
          <div
            v-for="(member, index) in memberStats"
            :key="member.userId"
            class="table-row"
            :class="{ 'top-three': index < 3 }"
          >
            <div class="td rank">
              <span class="rank-badge" :class="`rank-${index + 1}`">{{ index + 1 }}</span>
            </div>
            <div class="td user">
              <div class="user-info">
                <div class="user-avatar">{{ member.username.slice(0, 2) }}</div>
                <span class="user-name">{{ member.username }}</span>
              </div>
            </div>
            <div class="td commits">{{ member.commits.toLocaleString() }}</div>
            <div class="td additions">+{{ member.additions.toLocaleString() }}</div>
            <div class="td deletions">-{{ member.deletions.toLocaleString() }}</div>
            <div class="td tokens">{{ member.tokens.toLocaleString() }}</div>
            <div class="td activity">
              <div class="activity-bar">
                <div
                  class="activity-fill"
                  :style="{ width: `${(member.commits / maxCommits) * 100}%` }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </tech-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Refresh,
  FolderOpened,
  TrendCharts,
  PieChart,
  UserFilled,
  DocumentChecked,
  EditPen,
  Delete,
  Coin,
  User,
} from '@element-plus/icons-vue'
import TechCard from '@/components/tech/TechCard.vue'
import TechButton from '@/components/tech/TechButton.vue'
import TechChart from '@/components/tech/TechChart.vue'
import DataPanel from '@/components/tech/DataPanel.vue'
import type { EChartsOption } from 'echarts'

// 模拟项目数据
const projects = ref([
  {
    id: 1,
    name: 'DevMetrics Platform',
    description: '开发者绩效统计平台前端项目',
    repoUrl: 'https://github.com/example/devmetrics',
    status: 'active',
    createdAt: '2024-01-15',
  },
  {
    id: 2,
    name: 'AI Assistant Core',
    description: 'AI助手核心服务',
    repoUrl: 'https://github.com/example/ai-core',
    status: 'active',
    createdAt: '2024-02-20',
  },
  {
    id: 3,
    name: 'Data Sync Service',
    description: '数据同步服务',
    repoUrl: 'https://github.com/example/data-sync',
    status: 'archived',
    createdAt: '2023-11-10',
  },
])

const selectedProject = ref(1)

const currentProject = computed(() =>
  projects.value.find((p) => p.id === selectedProject.value)
)

// 项目统计数据
const projectStats = computed(() => [
  {
    label: '总提交数',
    value: 1258,
    icon: DocumentChecked,
    iconColor: '#00d4ff',
    iconBgColor: 'rgba(0, 212, 255, 0.1)',
  },
  {
    label: '贡献者',
    value: 8,
    icon: User,
    iconColor: '#00ff88',
    iconBgColor: 'rgba(0, 255, 136, 0.1)',
    suffix: '人',
  },
  {
    label: '代码行数',
    value: 125680,
    icon: EditPen,
    iconColor: '#ff9500',
    iconBgColor: 'rgba(255, 149, 0, 0.1)',
    suffix: '行',
  },
  {
    label: 'Pull Requests',
    value: 156,
    icon: Delete,
    iconColor: '#ff006e',
    iconBgColor: 'rgba(255, 0, 110, 0.1)',
  },
])

// 提交趋势图
const commitTrendOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['提交数', 'PR数'], textStyle: { color: 'rgba(255, 255, 255, 0.8)' } },
  grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['1月', '2月', '3月', '4月', '5月', '6月'],
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
      name: '提交数',
      type: 'line',
      smooth: true,
      data: [120, 180, 250, 320, 280, 350],
      lineStyle: { color: '#00d4ff', width: 3 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0, 212, 255, 0.4)' },
            { offset: 1, color: 'rgba(0, 212, 255, 0)' },
          ],
        },
      },
      itemStyle: { color: '#00d4ff' },
    },
    {
      name: 'PR数',
      type: 'line',
      smooth: true,
      data: [15, 22, 30, 38, 32, 45],
      lineStyle: { color: '#00ff88', width: 3 },
      itemStyle: { color: '#00ff88' },
    },
  ],
}))

// 语言分布图
const languageDistOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#0a1929',
        borderWidth: 2,
      },
      label: {
        show: true,
        formatter: '{b}\n{c}%',
        color: 'rgba(255, 255, 255, 0.8)',
      },
      labelLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.3)' } },
      data: [
        { value: 45, name: 'TypeScript', itemStyle: { color: '#3178c6' } },
        { value: 25, name: 'Vue', itemStyle: { color: '#4fc08d' } },
        { value: 15, name: 'Python', itemStyle: { color: '#3776ab' } },
        { value: 10, name: 'CSS', itemStyle: { color: '#c6538c' } },
        { value: 5, name: '其他', itemStyle: { color: '#8b949e' } },
      ],
    },
  ],
}))

// 成员统计数据
const memberStats = ref([
  { userId: 1, username: '张三', commits: 450, additions: 25000, deletions: 5000, tokens: 580000 },
  { userId: 2, username: '李四', commits: 380, additions: 22000, deletions: 4500, tokens: 420000 },
  { userId: 3, username: '王五', commits: 320, additions: 18000, deletions: 3800, tokens: 380000 },
  { userId: 4, username: '赵六', commits: 280, additions: 15000, deletions: 3200, tokens: 290000 },
  { userId: 5, username: '钱七', commits: 220, additions: 12000, deletions: 2500, tokens: 210000 },
  { userId: 6, username: '孙八', commits: 180, additions: 9500, deletions: 1800, tokens: 180000 },
  { userId: 7, username: '周九', commits: 150, additions: 8000, deletions: 1500, tokens: 150000 },
  { userId: 8, username: '吴十', commits: 120, additions: 6500, deletions: 1200, tokens: 120000 },
])

const maxCommits = computed(() => Math.max(...memberStats.value.map((m) => m.commits)))

const refreshData = () => {
  console.log('Refresh project data')
}

watch(selectedProject, () => {
  refreshData()
})
</script>

<style scoped lang="scss">
.project-stats-page {
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

  .project-overview {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 20px;
    margin-bottom: 24px;

    .project-info-card {
      padding: 24px;
      background: var(--tech-bg-card);
      border: 1px solid var(--tech-border-secondary);
      border-radius: var(--tech-radius-lg);

      .project-header {
        display: flex;
        gap: 16px;
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid var(--tech-border-secondary);

        .project-icon {
          width: 56px;
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(0, 212, 255, 0.1);
          border-radius: var(--tech-radius-lg);
          color: var(--tech-cyan);
          font-size: 28px;
        }

        .project-details {
          h2 {
            font-size: 18px;
            font-weight: 600;
            color: var(--tech-text-primary);
            margin: 0 0 6px;
          }

          p {
            font-size: 13px;
            color: var(--tech-text-muted);
            margin: 0;
          }
        }
      }

      .project-meta {
        display: flex;
        flex-direction: column;
        gap: 12px;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 12px;

          .meta-label {
            width: 80px;
            font-size: 13px;
            color: var(--tech-text-muted);
          }

          .meta-value {
            flex: 1;
            font-size: 13px;
            color: var(--tech-text-secondary);

            &.link {
              color: var(--tech-cyan);
              text-decoration: none;

              &:hover {
                text-decoration: underline;
              }
            }
          }
        }
      }
    }

    .project-stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }
  }

  .charts-section {
    margin-bottom: 24px;

    .chart-row {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 20px;
    }
  }

  .members-card {
    .members-table {
      .table-header {
        display: grid;
        grid-template-columns: 80px 1fr 120px 120px 120px 120px 150px;
        gap: 16px;
        padding: 12px 16px;
        background: var(--tech-bg-tertiary);
        border-radius: var(--tech-radius-md);
        margin-bottom: 8px;

        .th {
          font-size: 13px;
          font-weight: 600;
          color: var(--tech-cyan);
          font-family: var(--tech-font-chinese);
        }
      }

      .table-body {
        .table-row {
          display: grid;
          grid-template-columns: 80px 1fr 120px 120px 120px 120px 150px;
          gap: 16px;
          padding: 14px 16px;
          border-bottom: 1px solid var(--tech-border-secondary);
          transition: all 0.3s ease;
          align-items: center;

          &:hover {
            background: rgba(0, 212, 255, 0.05);
          }

          &.top-three {
            background: rgba(0, 212, 255, 0.03);
          }

          .td {
            font-size: 14px;
            color: var(--tech-text-secondary);
            font-family: var(--tech-font-mono);

            &.user {
              font-family: var(--tech-font-chinese);

              .user-info {
                display: flex;
                align-items: center;
                gap: 10px;

                .user-avatar {
                  width: 32px;
                  height: 32px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  background: linear-gradient(135deg, var(--tech-cyan), var(--tech-purple));
                  color: white;
                  font-size: 12px;
                  font-weight: 600;
                  border-radius: 50%;
                }

                .user-name {
                  color: var(--tech-text-primary);
                }
              }
            }

            &.additions {
              color: var(--tech-green);
            }

            &.deletions {
              color: var(--tech-pink);
            }

            .rank-badge {
              display: inline-flex;
              align-items: center;
              justify-content: center;
              width: 28px;
              height: 28px;
              border-radius: 50%;
              font-size: 13px;
              font-weight: 600;
              font-family: var(--tech-font-mono);
              background: var(--tech-bg-tertiary);
              color: var(--tech-text-muted);

              &.rank-1 {
                background: linear-gradient(135deg, #ffd700, #ffaa00);
                color: #000;
              }

              &.rank-2 {
                background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
                color: #000;
              }

              &.rank-3 {
                background: linear-gradient(135deg, #cd7f32, #b87333);
                color: #fff;
              }
            }

            .activity-bar {
              width: 100%;
              height: 6px;
              background: var(--tech-bg-tertiary);
              border-radius: 3px;
              overflow: hidden;

              .activity-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--tech-cyan), var(--tech-green));
                border-radius: 3px;
                transition: width 0.5s ease;
              }
            }
          }
        }
      }
    }
  }
}
</style>
