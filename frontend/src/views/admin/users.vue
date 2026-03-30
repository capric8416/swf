<template>
  <div class="users-manage-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">用户管理</h1>
        <p class="page-subtitle">管理系统用户，分配角色和权限</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户..."
          style="width: 240px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <tech-button variant="primary" :icon="Plus" @click="showAddDialog">
          添加用户
        </tech-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <data-panel
        label="总用户数"
        :value="stats.total"
        :icon="UserFilled"
        icon-color="#00d4ff"
        :icon-bg-color="'rgba(0, 212, 255, 0.1)'"
      />
      <data-panel
        label="活跃用户"
        :value="stats.active"
        :icon="CircleCheck"
        icon-color="#00ff88"
        :icon-bg-color="'rgba(0, 255, 136, 0.1)'"
      />
      <data-panel
        label="管理员"
        :value="stats.admins"
        :icon="UserIcon"
        icon-color="#ff9500"
        :icon-bg-color="'rgba(255, 149, 0, 0.1)'"
      />
      <data-panel
        label="今日新增"
        :value="stats.todayNew"
        :icon="TrendCharts"
        icon-color="#ff006e"
        :icon-bg-color="'rgba(255, 0, 110, 0.1)'"
      />
    </div>

    <!-- 用户列表 -->
    <tech-card title="用户列表" :icon="List">
      <el-table
        :data="filteredUsers"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column type="index" width="60" align="center" />

        <el-table-column label="用户" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="user-avatar">{{ row.username.slice(0, 2).toUpperCase() }}</div>
              <div class="user-info">
                <div class="user-name">{{ row.username }}</div>
                <div class="user-email">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="角色" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTypes[row.role?.name || '']">{{ roleNames[row.role?.name || ''] }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.isActive"
              @change="toggleUserStatus(row)"
            />
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            <span class="time-cell">{{ row.createdAt }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link :icon="Edit" @click="editUser(row)">编辑</el-button>
            <el-button type="danger" link :icon="Delete" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </tech-card>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '添加用户'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="开发者" value="developer" />
            <el-option label="访客" value="viewer" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-switch v-model="form.isActive" active-text="启用" inactive-text="禁用" />
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
  UserFilled,
  CircleCheck,
  User as UserIcon,
  TrendCharts,
  List,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import TechCard from '@/components/tech/TechCard.vue'
import TechButton from '@/components/tech/TechButton.vue'
import DataPanel from '@/components/tech/DataPanel.vue'
import type { User } from '@/types/api'

const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(100)

// 统计数据
const stats = ref({
  total: 156,
  active: 142,
  admins: 8,
  todayNew: 3,
})

// 角色映射
const roleNames: Record<string, string> = {
  admin: '管理员',
  developer: '开发者',
  viewer: '访客',
}

const roleTypes: Record<string, string> = {
  admin: 'danger',
  developer: 'success',
  viewer: 'info',
}

// 模拟用户数据
const users = ref<User[]>([
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    department: '技术部',
    isActive: true,
    createdAt: '2024-01-01 00:00:00',
    updatedAt: '2024-03-28 12:00:00',
  },
  {
    id: 2,
    username: 'zhangsan',
    email: 'zhangsan@example.com',
    department: '开发部',
    isActive: true,
    createdAt: '2024-01-15 10:30:00',
    updatedAt: '2024-03-28 12:00:00',
  },
  {
    id: 3,
    username: 'lisi',
    email: 'lisi@example.com',
    department: '开发部',
    isActive: true,
    createdAt: '2024-02-01 14:20:00',
    updatedAt: '2024-03-28 12:00:00',
  },
  {
    id: 4,
    username: 'wangwu',
    email: 'wangwu@example.com',
    department: '测试部',
    isActive: false,
    createdAt: '2024-02-15 09:00:00',
    updatedAt: '2024-03-28 12:00:00',
  },
])

// 过滤用户
const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(
    (user) =>
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query)
  )
})

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  id: 0,
  username: '',
  email: '',
  password: '',
  role: 'developer' as 'admin' | 'developer' | 'viewer',
  isActive: true,
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 个字符', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const showAddDialog = () => {
  isEdit.value = false
  form.id = 0
  form.username = ''
  form.email = ''
  form.password = ''
  form.role = 'developer'
  form.isActive = true
  dialogVisible.value = true
}

const editUser = (user: User) => {
  isEdit.value = true
  form.id = user.id
  form.username = user.username
  form.email = user.email
  form.role = (user.role?.name as 'admin' | 'developer' | 'viewer') || 'developer'
  form.isActive = user.isActive
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (valid) {
      submitting.value = true
      setTimeout(() => {
        if (isEdit.value) {
          const index = users.value.findIndex((u) => u.id === form.id)
          if (index > -1) {
            const existing = users.value[index]!
            const updated: User = {
              id: existing.id,
              username: form.username,
              email: form.email,
              department: existing.department,
              isActive: form.isActive,
              createdAt: existing.createdAt,
              updatedAt: new Date().toLocaleString('zh-CN'),
              role: {
                id: form.role === 'admin' ? 1 : form.role === 'developer' ? 2 : 3,
                name: form.role,
                permissions: [],
              },
            }
            users.value[index] = updated
          }
          ElMessage.success('用户更新成功')
        } else {
          const newUser: User = {
            id: users.value.length + 1,
            username: form.username,
            email: form.email,
            department: '未分配',
            isActive: form.isActive,
            createdAt: new Date().toLocaleString('zh-CN'),
            updatedAt: new Date().toLocaleString('zh-CN'),
            role: {
              id: form.role === 'admin' ? 1 : form.role === 'developer' ? 2 : 3,
              name: form.role,
              permissions: [],
            },
          }
          users.value.push(newUser)
          ElMessage.success('用户添加成功')
        }
        submitting.value = false
        dialogVisible.value = false
      }, 500)
    }
  })
}

const deleteUser = (user: User) => {
  ElMessageBox.confirm(
    `确定要删除用户 "${user.username}" 吗？`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    users.value = users.value.filter((u) => u.id !== user.id)
    ElMessage.success('删除成功')
  })
}

const toggleUserStatus = (user: User) => {
  const action = user.isActive ? '启用' : '禁用'
  ElMessage.success(`用户已${action}`)
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}
</script>

<style scoped lang="scss">
.users-manage-page {
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

  .user-cell {
    display: flex;
    align-items: center;
    gap: 12px;

    .user-avatar {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--tech-cyan), var(--tech-purple));
      color: white;
      font-size: 14px;
      font-weight: 600;
      border-radius: 50%;
    }

    .user-info {
      .user-name {
        font-size: 14px;
        font-weight: 500;
        color: var(--tech-text-primary);
        margin-bottom: 2px;
      }

      .user-email {
        font-size: 12px;
        color: var(--tech-text-muted);
      }
    }
  }

  .time-cell {
    font-family: var(--tech-font-mono);
    font-size: 13px;
    color: var(--tech-text-secondary);
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid var(--tech-border-secondary);
  }
}
</style>
