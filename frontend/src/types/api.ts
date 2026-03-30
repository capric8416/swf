// API类型定义

// 通用响应
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

// 角色
export interface Role {
  id: number
  name: string
  description?: string
  permissions: string[]
}

// 用户
export interface User {
  id: number
  username: string
  email: string
  department: string
  isActive: boolean
  roleId?: number
  role?: Role
  avatar?: string
  createdAt?: string
  updatedAt?: string
}

// 项目
export interface Project {
  id: number
  name: string
  description?: string
  repoUrl?: string
  status: 'active' | 'archived' | 'deleted'
  createdAt: string
  updatedAt: string
  members?: ProjectMember[]
}

// 项目成员
export interface ProjectMember {
  id: number
  projectId: number
  userId: number
  role: 'owner' | 'maintainer' | 'developer'
  joinedAt: string
  user?: User
}

// 代码统计
export interface CodeStats {
  id: number
  userId: number
  projectId?: number
  date: string
  additions: number
  deletions: number
  commits: number
  filesChanged: number
  languages: Record<string, number>
}

// Token使用统计
export interface TokenUsage {
  id: number
  userId: number
  date: string
  promptTokens: number
  completionTokens: number
  totalTokens: number
  model: string
  requestCount: number
}

// 会话统计
export interface SessionStats {
  id: number
  userId: number
  date: string
  sessionCount: number
  totalDuration: number // 分钟
  avgDuration: number
  activeHours: number[]
}

// 个人仪表盘数据
export interface PersonalDashboard {
  todayStats: {
    commits: number
    additions: number
    deletions: number
    tokens: number
    sessions: number
  }
  weeklyTrend: {
    dates: string[]
    commits: number[]
    tokens: number[]
  }
  languageStats: {
    language: string
    lines: number
    percentage: number
  }[]
  heatmapData: {
    date: string
    count: number
    level: 0 | 1 | 2 | 3 | 4
  }[]
  ranking: {
    commits: number
    totalUsers: number
  }
}

// 项目仪表盘数据
export interface ProjectDashboard {
  projectId: number
  projectName: string
  totalStats: {
    commits: number
    contributors: number
    linesOfCode: number
    pullRequests: number
  }
  memberStats: {
    userId: number
    username: string
    commits: number
    additions: number
    deletions: number
    tokens: number
  }[]
  languageDistribution: {
    language: string
    percentage: number
  }[]
  commitTrend: {
    dates: string[]
    commits: number[]
  }
}

// 同步任务
export interface SyncTask {
  id: number
  userId: number
  type: 'code' | 'token' | 'session' | 'full'
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message?: string
  startedAt?: string
  completedAt?: string
  createdAt: string
}

// 同步日志
export interface SyncLog {
  id: number
  taskId: number
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
  timestamp: string
}

// 系统设置
export interface SystemSettings {
  syncEnabled: boolean
  autoSyncInterval: number // 分钟
  retentionDays: number
  maxProjectsPerUser: number
  allowedModels: string[]
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  accessToken: string
  refreshToken: string
  user: User
}

// 刷新Token响应
export interface RefreshTokenResponse {
  accessToken: string
}
