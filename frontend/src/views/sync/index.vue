<template>
  <div class="sync-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">数据同步</h1>
        <p class="page-subtitle">管理您的代码和AI使用数据同步任务</p>
      </div>
      <div class="header-actions">
        <tech-button
          variant="primary"
          :icon="Refresh"
          :loading="isSyncing"
          :pulse="isSyncing"
          @click="startFullSync"
        >
          全量同步
        </tech-button>
      </div>
    </div>

    <!-- 同步状态概览 -->
    <div class="sync-overview">
      <div
        v-for="status in syncStatuses"
        :key="status.type"
        class="status-card"
        :class="status.status"
      >
        <div class="status-icon">
          <el-icon><component :is="status.icon" /></el-icon>
        </div>
        <div class="status-content">
          <div class="status-title">{{ status.name }}</div>
          <div class="status-time">上次同步: {{ status.lastSync }}</div>
          <div class="status-badge" :class="status.status">
            {{ statusText[status.status] }}
          </div>
        </div>
        <div class="status-action">
          <tech-button
            size="small"
            variant="ghost"
            :icon="RefreshRight"
            :loading="status.syncing"
            @click="startSync(status.type)"
          >
            同步
          </tech-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <!-- 左侧：同步日志 -->
      <tech-card title="同步日志" :icon="List" class="logs-card">
        <div ref="terminalRef" class="terminal">
          <div class="terminal-header">
            <div class="terminal-dots">
              <span class="dot red" />
              <span class="dot yellow" />
              <span class="dot green" />
            </div>
            <div class="terminal-title">sync_log.txt</div>
          </div>
          <div class="terminal-body">
            <div
              v-for="(log, index) in syncLogs"
              :key="index"
              class="log-line"
              :class="log.level"
            >
              <span class="log-time">[{{ log.time }}]</span>
              <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            <div v-if="isSyncing" class="log-line info">
              <span class="log-time">[{{ currentTime }}]</span>
              <span class="log-level">[INFO]</span>
              <span class="log-message">
                同步进行中
                <span class="loading-dots">...</span>
              </span>
            </div>
          </div>
        </div>
      </tech-card>

      <!-- 右侧：同步任务 -->
      <tech-card title="同步任务" :icon="Timer" class="tasks-card">
        <div class="tasks-list">
          <div
            v-for="task in syncTasks"
            :key="task.id"
            class="task-item"
            :class="task.status"
          >
            <div class="task-header">
              <div class="task-info">
                <span class="task-type">{{ taskTypeNames[task.type] }}</span>
                <span class="task-time">{{ task.createdAt }}</span>
              </div>
              <el-tag :type="taskStatusTypes[task.status]" size="small">
                {{ taskStatusNames[task.status] }}
              </el-tag>
            </div>

            <div v-if="task.status === 'running'" class="task-progress">
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: `${task.progress}%` }"
                />
              </div>
              <span class="progress-text">{{ task.progress }}%</span>
            </div>

            <div v-if="task.message" class="task-message">
              {{ task.message }}
            </div>
          </div>
        </div>

        <div class="sync-settings">
          <h4>自动同步设置</h4>
          <div class="setting-item">
            <span>启用自动同步</span>
            <el-switch v-model="autoSyncEnabled" />
          </div>
          <div class="setting-item">
            <span>同步间隔</span>
            <el-select v-model="syncInterval" size="small" style="width: 120px">
              <el-option label="15分钟" :value="15" />
              <el-option label="30分钟" :value="30" />
              <el-option label="1小时" :value="60" />
              <el-option label="6小时" :value="360" />
              <el-option label="12小时" :value="720" />
              <el-option label="24小时" :value="1440" />
            </el-select>
          </div>
        </div>
      </tech-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import {
  Refresh,
  RefreshRight,
  List,
  Timer,
  DocumentChecked,
  Coin,
  Monitor,
  Folder,
} from '@element-plus/icons-vue'
import TechCard from '@/components/tech/TechCard.vue'
import TechButton from '@/components/tech/TechButton.vue'

const isSyncing = ref(false)
const autoSyncEnabled = ref(true)
const syncInterval = ref(60)
const terminalRef = ref<HTMLElement>()

// 同步状态
type SyncStatus = 'success' | 'warning' | 'error' | 'syncing'

interface SyncStatusItem {
  type: string
  name: string
  icon: any
  lastSync: string
  status: SyncStatus
  syncing: boolean
}

const syncStatuses = ref<SyncStatusItem[]>([
  {
    type: 'code',
    name: '代码统计',
    icon: DocumentChecked,
    lastSync: '2024-03-28 14:30:00',
    status: 'success',
    syncing: false,
  },
  {
    type: 'token',
    name: 'Token使用',
    icon: Coin,
    lastSync: '2024-03-28 14:30:00',
    status: 'success',
    syncing: false,
  },
  {
    type: 'session',
    name: '会话数据',
    icon: Monitor,
    lastSync: '2024-03-28 14:30:00',
    status: 'warning',
    syncing: false,
  },
  {
    type: 'project',
    name: '项目信息',
    icon: Folder,
    lastSync: '2024-03-28 14:30:00',
    status: 'success',
    syncing: false,
  },
])

const statusText: Record<SyncStatus, string> = {
  success: '已同步',
  warning: '需同步',
  error: '同步失败',
  syncing: '同步中',
}

// 同步日志
interface LogEntry {
  time: string
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
}

const syncLogs = ref<LogEntry[]>([
  { time: '14:30:00', level: 'info', message: '开始执行全量同步任务...' },
  { time: '14:30:02', level: 'success', message: '代码统计同步完成，共 1,258 条记录' },
  { time: '14:30:05', level: 'success', message: 'Token使用数据同步完成，共 2,580,000 tokens' },
  { time: '14:30:08', level: 'warning', message: '会话数据同步延迟，正在重试...' },
  { time: '14:30:15', level: 'success', message: '会话数据同步完成，共 156 个会话' },
  { time: '14:30:18', level: 'success', message: '项目信息同步完成，共 8 个项目' },
  { time: '14:30:20', level: 'info', message: '全量同步任务执行完毕' },
])

const currentTime = computed(() => {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
})

// 同步任务
const taskTypeNames: Record<string, string> = {
  code: '代码统计同步',
  token: 'Token使用同步',
  session: '会话数据同步',
  full: '全量数据同步',
}

const taskStatusNames: Record<string, string> = {
  pending: '等待中',
  running: '进行中',
  completed: '已完成',
  failed: '失败',
}

const taskStatusTypes: Record<string, string> = {
  pending: 'info',
  running: 'warning',
  completed: 'success',
  failed: 'danger',
}

const syncTasks = ref([
  {
    id: 1,
    type: 'full',
    status: 'completed' as const,
    progress: 100,
    createdAt: '2024-03-28 14:30:00',
    message: '成功同步所有数据',
  },
  {
    id: 2,
    type: 'code',
    status: 'completed' as const,
    progress: 100,
    createdAt: '2024-03-28 10:15:00',
    message: '同步了 45 个提交',
  },
  {
    id: 3,
    type: 'token',
    status: 'running' as const,
    progress: 65,
    createdAt: '2024-03-28 14:35:00',
    message: '正在同步 Token 使用数据...',
  },
])

// 添加日志
const addLog = (level: LogEntry['level'], message: string) => {
  syncLogs.value.push({
    time: currentTime.value,
    level,
    message,
  })
  nextTick(() => {
    if (terminalRef.value) {
      terminalRef.value.scrollTop = terminalRef.value.scrollHeight
    }
  })
}

// 开始同步
const startSync = async (type: string) => {
  const status = syncStatuses.value.find((s) => s.type === type)
  if (status) {
    status.syncing = true
    status.status = 'syncing'
    addLog('info', `开始同步 ${status.name}...`)

    // 模拟同步过程
    await new Promise((resolve) => setTimeout(resolve, 2000))

    status.syncing = false
    status.status = 'success'
    status.lastSync = new Date().toLocaleString('zh-CN')
    addLog('success', `${status.name}同步完成`)
  }
}

// 开始全量同步
const startFullSync = async () => {
  isSyncing.value = true
  addLog('info', '开始执行全量同步任务...')

  for (const status of syncStatuses.value) {
    await startSync(status.type)
  }

  addLog('info', '全量同步任务执行完毕')
  isSyncing.value = false
}

// 自动滚动日志
watch(syncLogs, () => {
  nextTick(() => {
    const terminal = document.querySelector('.terminal-body')
    if (terminal) {
      terminal.scrollTop = terminal.scrollHeight
    }
  })
}, { deep: true })
</script>

<style scoped lang="scss">
.sync-page {
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
  }

  .sync-overview {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;

    .status-card {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 20px;
      background: var(--tech-bg-card);
      border: 1px solid var(--tech-border-secondary);
      border-radius: var(--tech-radius-lg);
      transition: all 0.3s ease;

      &.success {
        border-color: rgba(0, 255, 136, 0.3);
        .status-icon { color: var(--tech-green); background: rgba(0, 255, 136, 0.1); }
      }

      &.warning {
        border-color: rgba(255, 149, 0, 0.3);
        .status-icon { color: var(--tech-orange); background: rgba(255, 149, 0, 0.1); }
      }

      &.error {
        border-color: rgba(255, 0, 110, 0.3);
        .status-icon { color: var(--tech-pink); background: rgba(255, 0, 110, 0.1); }
      }

      &.syncing {
        border-color: rgba(0, 212, 255, 0.3);
        .status-icon {
          color: var(--tech-cyan);
          background: rgba(0, 212, 255, 0.1);
          animation: pulse 1.5s ease-in-out infinite;
        }
      }

      .status-icon {
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: var(--tech-radius-md);
        font-size: 24px;
      }

      .status-content {
        flex: 1;

        .status-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--tech-text-primary);
          margin-bottom: 4px;
        }

        .status-time {
          font-size: 12px;
          color: var(--tech-text-muted);
          margin-bottom: 6px;
          font-family: var(--tech-font-mono);
        }

        .status-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;

          &.success {
            background: rgba(0, 255, 136, 0.1);
            color: var(--tech-green);
          }

          &.warning {
            background: rgba(255, 149, 0, 0.1);
            color: var(--tech-orange);
          }

          &.error {
            background: rgba(255, 0, 110, 0.1);
            color: var(--tech-pink);
          }

          &.syncing {
            background: rgba(0, 212, 255, 0.1);
            color: var(--tech-cyan);
          }
        }
      }
    }
  }

  .main-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;

    .logs-card {
      .terminal {
        background: #0d1117;
        border-radius: var(--tech-radius-md);
        overflow: hidden;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;

        .terminal-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: #161b22;
          border-bottom: 1px solid #30363d;

          .terminal-dots {
            display: flex;
            gap: 8px;

            .dot {
              width: 12px;
              height: 12px;
              border-radius: 50%;

              &.red { background: #ff5f56; }
              &.yellow { background: #ffbd2e; }
              &.green { background: #27c93f; }
            }
          }

          .terminal-title {
            font-size: 13px;
            color: #8b949e;
          }
        }

        .terminal-body {
          height: 400px;
          padding: 16px;
          overflow-y: auto;

          .log-line {
            display: flex;
            gap: 8px;
            margin-bottom: 6px;
            font-size: 13px;
            line-height: 1.6;

            .log-time {
              color: #6e7681;
              flex-shrink: 0;
            }

            .log-level {
              flex-shrink: 0;
              font-weight: 600;
            }

            .log-message {
              color: #c9d1d9;
            }

            &.info .log-level { color: #58a6ff; }
            &.success .log-level { color: #3fb950; }
            &.warning .log-level { color: #d29922; }
            &.error .log-level { color: #f85149; }

            .loading-dots {
              animation: blink 1s step-end infinite;
            }
          }
        }
      }
    }

    .tasks-card {
      .tasks-list {
        margin-bottom: 24px;

        .task-item {
          padding: 16px;
          background: var(--tech-bg-tertiary);
          border-radius: var(--tech-radius-md);
          margin-bottom: 12px;
          border-left: 3px solid transparent;

          &.running {
            border-left-color: var(--tech-cyan);
            background: rgba(0, 212, 255, 0.05);
          }

          &.completed {
            border-left-color: var(--tech-green);
          }

          &.failed {
            border-left-color: var(--tech-pink);
          }

          .task-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;

            .task-info {
              display: flex;
              flex-direction: column;
              gap: 4px;

              .task-type {
                font-size: 14px;
                font-weight: 600;
                color: var(--tech-text-primary);
              }

              .task-time {
                font-size: 12px;
                color: var(--tech-text-muted);
                font-family: var(--tech-font-mono);
              }
            }
          }

          .task-progress {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 12px;

            .progress-bar {
              flex: 1;
              height: 6px;
              background: var(--tech-bg-secondary);
              border-radius: 3px;
              overflow: hidden;

              .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--tech-cyan), var(--tech-green));
                border-radius: 3px;
                transition: width 0.3s ease;
              }
            }

            .progress-text {
              font-size: 12px;
              color: var(--tech-cyan);
              font-family: var(--tech-font-mono);
              min-width: 36px;
            }
          }

          .task-message {
            margin-top: 8px;
            font-size: 12px;
            color: var(--tech-text-muted);
          }
        }
      }

      .sync-settings {
        padding-top: 20px;
        border-top: 1px solid var(--tech-border-secondary);

        h4 {
          font-size: 14px;
          color: var(--tech-text-primary);
          margin: 0 0 16px;
        }

        .setting-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
          font-size: 13px;
          color: var(--tech-text-secondary);
        }
      }
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
