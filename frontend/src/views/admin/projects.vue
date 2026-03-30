<template>
  <div class="projects-manage-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">项目管理</h1>
        <p class="page-subtitle">管理系统项目，配置仓库和成员</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索项目..."
          style="width: 240px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <tech-button variant="primary" :icon="Plus" @click="showAddDialog">
          添加项目
        </tech-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <data-panel
        label="总项目数"
        :value="stats.total"
        :icon="FolderOpened"
        icon-color="#00d4ff"
        :icon-bg-color="'rgba(0, 212, 255, 0.1)'"
      />
      <data-panel
        label="活跃项目"
        :value="stats.active"
        :icon="CircleCheck"
        icon-color="#00ff88"
        :icon-bg-color="'rgba(0, 255, 136, 0.1)'"
      />
      <data-panel
        label="总代码行数"
        :value="stats.totalLines"
        suffix="行"
        :icon="Document"
        icon-color="#ff9500"
        :icon-bg-color="'rgba(255, 149, 0, 0.1)'"
      />
      <data-panel
        label="总提交数"
        :value="stats.totalCommits"
        :icon="DocumentChecked"
        icon-color="#ff006e"
        :icon-bg-color="'rgba(255, 0, 110, 0.1)'"
      />
    </div>

    <!-- 项目卡片网格 -->
    <div class="projects-grid">
      <div
        v-for="project in filteredProjects"
        :key="project.id"
        class="project-card"
        :class="{ archived: project.status === 'archived' }"
      >
        <div class="card-header">
          <div class="project-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="project-title">
            <h3>{{ project.name }}</h3>
            <el-tag :type="project.status === 'active' ? 'success' : 'info'" size="small">
              {{ project.status === 'active' ? '活跃' : '归档' }}
            </el-tag>
          </div>
          <el-dropdown trigger="click">
            <button class="more-btn">
              <el-icon><More /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :icon="Edit" @click="editProject(project)">编辑</el-dropdown-item>
                <el-dropdown-item :icon="User" @click="manageMembers(project)">成员管理</el-dropdown-item>
                <el-dropdown-item
                  :icon="project.status === 'active' ? FolderRemove : FolderChecked"
                  @click="toggleProjectStatus(project)"
                >
                  {{ project.status === 'active' ? '归档' : '激活' }}
                </el-dropdown-item>
                <el-dropdown-item :icon="Delete" divided @click="deleteProject(project)">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <p class="project-desc">{{ project.description || '暂无描述' }}</p>

        <div class="project-meta">
          <div class="meta-item">
            <el-icon><Link /></el-icon>
            <a :href="project.repoUrl" target="_blank" class="repo-link">
              {{ project.repoUrl?.replace('https://github.com/', '') || '-' }}
            </a>
          </div>
          <div class="meta-item">
            <el-icon><Calendar /></el-icon>
            <span>创建于 {{ project.createdAt }}</span>
          </div>
        </div>

        <div class="project-stats">
          <div class="stat-item">
            <span class="stat-value">{{ project.commits || 0 }}</span>
            <span class="stat-label">提交</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ project.memberCount || 0 }}</span>
            <span class="stat-label">成员</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatLines(project.lines || 0) }}</span>
            <span class="stat-label">代码</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑项目对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑项目' : '添加项目'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>

        <el-form-item label="项目描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>

        <el-form-item label="仓库地址" prop="repoUrl">
          <el-input v-model="form.repoUrl" placeholder="https://github.com/..." />
        </el-form-item>

        <el-form-item label="项目状态">
          <el-radio-group v-model="form.status">
            <el-radio-button label="active">活跃</el-radio-button>
            <el-radio-button label="archived">归档</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Plus,
  Search,
  FolderOpened,
  CircleCheck,
  Document,
  DocumentChecked,
  Folder,
  FolderRemove,
  FolderChecked,
  Edit,
  Delete,
  User,
  More,
  Link,
  Calendar,
} from '@element-plus/icons-vue'
import TechButton from '@/components/tech/TechButton.vue'
import DataPanel from '@/components/tech/DataPanel.vue'
import type { Project } from '@/types/api'

const searchQuery = ref('')
const loading = ref(false)

// 统计数据
const stats = ref({
  total: 12,
  active: 10,
  totalLines: 1256800,
  totalCommits: 5680,
})

// 模拟项目数据
interface ProjectWithStats extends Project {
  commits?: number
  memberCount?: number
  lines?: number
}

const projects = ref<ProjectWithStats[]>([
  {
    id: 1,
    name: 'DevMetrics Platform',
    description: '开发者绩效统计平台，提供代码统计、Token使用分析等功能',
    repoUrl: 'https://github.com/example/devmetrics',
    status: 'active',
    createdAt: '2024-01-15',
    updatedAt: '2024-03-28',
    commits: 1258,
    memberCount: 8,
    lines: 45680,
  },
  {
    id: 2,
    name: 'AI Assistant Core',
    description: 'AI助手核心服务，处理自然语言理解和生成',
    repoUrl: 'https://github.com/example/ai-core',
    status: 'active',
    createdAt: '2024-02-20',
    updatedAt: '2024-03-28',
    commits: 890,
    memberCount: 5,
    lines: 32500,
  },
  {
    id: 3,
    name: 'Data Sync Service',
    description: '数据同步服务，负责各数据源的同步任务',
    repoUrl: 'https://github.com/example/data-sync',
    status: 'archived',
    createdAt: '2023-11-10',
    updatedAt: '2024-03-28',
    commits: 456,
    memberCount: 3,
    lines: 12800,
  },
  {
    id: 4,
    name: 'Web Dashboard',
    description: '数据可视化仪表盘前端项目',
    repoUrl: 'https://github.com/example/dashboard',
    status: 'active',
    createdAt: '2024-03-01',
    updatedAt: '2024-03-28',
    commits: 234,
    memberCount: 4,
    lines: 18600,
  },
])

// 过滤项目
const filteredProjects = computed(() => {
  if (!searchQuery.value) return projects.value
  const query = searchQuery.value.toLowerCase()
  return projects.value.filter(
    (project) =>
      project.name.toLowerCase().includes(query) ||
      project.description?.toLowerCase().includes(query)
  )
})

// 格式化代码行数
const formatLines = (lines: number): string => {
  if (lines >= 10000) {
    return `${(lines / 10000).toFixed(1)}w`
  }
  if (lines >= 1000) {
    return `${(lines / 1000).toFixed(1)}k`
  }
  return lines.toString()
}

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  id: 0,
  name: '',
  description: '',
  repoUrl: '',
  status: 'active' as Project['status'],
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  repoUrl: [
    { type: 'url', message: '请输入正确的URL地址', trigger: 'blur' },
  ],
}

const showAddDialog = () => {
  isEdit.value = false
  form.id = 0
  form.name = ''
  form.description = ''
  form.repoUrl = ''
  form.status = 'active'
  dialogVisible.value = true
}

const editProject = (project: ProjectWithStats) => {
  isEdit.value = true
  form.id = project.id
  form.name = project.name
  form.description = project.description || ''
  form.repoUrl = project.repoUrl || ''
  form.status = project.status
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (valid) {
      submitting.value = true
      setTimeout(() => {
        if (isEdit.value) {
          const index = projects.value.findIndex((p) => p.id === form.id)
          if (index > -1) {
            const existing = projects.value[index]!
            const updated: ProjectWithStats = {
              id: existing.id,
              name: form.name,
              description: form.description,
              repoUrl: form.repoUrl,
              status: form.status,
              createdAt: existing.createdAt,
              updatedAt: new Date().toISOString(),
              commits: existing.commits,
              memberCount: existing.memberCount,
              lines: existing.lines,
            }
            projects.value[index] = updated
          }
          ElMessage.success('项目更新成功')
        } else {
          const dateStr = new Date().toISOString()
          const createdAtStr = dateStr.split('T')[0] || dateStr
          const newProject: ProjectWithStats = {
            id: projects.value.length + 1,
            name: form.name,
            description: form.description,
            repoUrl: form.repoUrl,
            status: form.status,
            createdAt: createdAtStr,
            updatedAt: dateStr,
            commits: 0,
            memberCount: 0,
            lines: 0,
          }
          projects.value.push(newProject)
          stats.value.total++
          if (form.status === 'active') {
            stats.value.active++
          }
          ElMessage.success('项目添加成功')
        }
        submitting.value = false
        dialogVisible.value = false
      }, 500)
    }
  })
}

const deleteProject = (project: ProjectWithStats) => {
  ElMessageBox.confirm(
    `确定要删除项目 "${project.name}" 吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    projects.value = projects.value.filter((p) => p.id !== project.id)
    stats.value.total--
    if (project.status === 'active') {
      stats.value.active--
    }
    ElMessage.success('删除成功')
  })
}

const toggleProjectStatus = (project: ProjectWithStats) => {
  const newStatus = project.status === 'active' ? 'archived' : 'active'
  const action = newStatus === 'active' ? '激活' : '归档'

  project.status = newStatus
  if (newStatus === 'active') {
    stats.value.active++
  } else {
    stats.value.active--
  }
  ElMessage.success(`项目已${action}`)
}

const manageMembers = (project: ProjectWithStats) => {
  ElMessage.info(`管理项目 "${project.name}" 的成员`)
}
</script>

<style scoped lang="scss">
.projects-manage-page {
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

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;
  }

  .projects-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;

    .project-card {
      background: var(--tech-bg-card);
      border: 1px solid var(--tech-border-secondary);
      border-radius: var(--tech-radius-lg);
      padding: 20px;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-4px);
        box-shadow: var(--tech-glow-cyan-sm);
        border-color: var(--tech-border-primary);
      }

      &.archived {
        opacity: 0.7;
        border-color: var(--tech-border-secondary);
      }

      .card-header {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 12px;

        .project-icon {
          width: 44px;
          height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(0, 212, 255, 0.1);
          border-radius: var(--tech-radius-md);
          color: var(--tech-cyan);
          font-size: 22px;
        }

        .project-title {
          flex: 1;

          h3 {
            font-size: 16px;
            font-weight: 600;
            color: var(--tech-text-primary);
            margin: 0 0 6px;
          }
        }

        .more-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: none;
          color: var(--tech-text-muted);
          cursor: pointer;
          border-radius: var(--tech-radius-sm);
          transition: all 0.3s ease;

          &:hover {
            background: rgba(0, 212, 255, 0.1);
            color: var(--tech-cyan);
          }
        }
      }

      .project-desc {
        font-size: 13px;
        color: var(--tech-text-muted);
        line-height: 1.6;
        margin: 0 0 16px;
        height: 40px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }

      .project-meta {
        margin-bottom: 16px;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: var(--tech-text-muted);
          margin-bottom: 6px;

          .el-icon {
            font-size: 14px;
          }

          .repo-link {
            color: var(--tech-cyan);
            text-decoration: none;

            &:hover {
              text-decoration: underline;
            }
          }
        }
      }

      .project-stats {
        display: flex;
        gap: 24px;
        padding-top: 16px;
        border-top: 1px solid var(--tech-border-secondary);

        .stat-item {
          display: flex;
          flex-direction: column;
          gap: 2px;

          .stat-value {
            font-size: 18px;
            font-weight: 700;
            color: var(--tech-text-primary);
            font-family: var(--tech-font-mono);
          }

          .stat-label {
            font-size: 12px;
            color: var(--tech-text-muted);
          }
        }
      }
    }
  }
}
</style>
