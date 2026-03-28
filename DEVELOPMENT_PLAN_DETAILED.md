# 研发详细执行计划 - Coding Agent 绩效统计平台

## 基于 S6-A02 数据库设计 & S6-A03 UI/UX 设计的精确规划

---

## 一、数据库设计要点提炼

### 1.1 核心表结构（12个表）

| 表名 | 类型 | 用途 | 特殊设计 |
|------|------|------|----------|
| `users` | 基础表 | 用户信息 | 角色关联、登录时间 |
| `roles` | 基础表 | 角色权限 | JSONB 权限存储 |
| `projects` | 基础表 | 项目信息 | 枚举类型 stage/status |
| `project_members` | 关联表 | 项目成员 | 角色、时间范围约束 |
| `user_accounts` | 配置表 | 平台账号 | AES-256 加密 token |
| `code_commits` | **分区表** | 代码提交 | 按月分区、全文索引 |
| `token_usage` | **分区表** | Token使用 | 按月分区 |
| `bug_records` | 数据表 | Bug记录 | 全文索引、状态枚举 |
| `ai_suggestions` | 数据表 | AI建议 | 采纳标记 |
| `data_sources` | 配置表 | 数据源 | JSONB 配置 |
| `sync_tasks` | 任务表 | 同步任务 | 状态追踪 |
| `stats_snapshots` | 统计表 | 统计快照 | JSONB 指标 |
| `audit_logs` | 审计表 | 操作审计 | JSONB 变更记录 |

### 1.2 关键技术设计

```sql
-- 枚举类型定义
project_stage: 调研/立项/需求/设计/研发/验收/发布/运维
project_status: active/archived/cancelled
bug_severity: critical/major/normal/minor/trivial
bug_status: new/assigned/active/resolved/closed/rejected
sync_task_status: pending/running/completed/failed/cancelled

-- 分区表（时序数据）
code_commits: PARTITION BY RANGE (commit_time)
token_usage: PARTITION BY RANGE (usage_date)

-- 自动分区函数
create_monthly_partition(table_name, year, month)

-- 审计日志触发器
log_audit_changes() - 记录 INSERT/UPDATE/DELETE
```

### 1.3 索引策略

| 表 | 索引类型 | 字段 | 用途 |
|----|---------|------|------|
| code_commits | B-tree | user_id, commit_time DESC | 用户代码查询 |
| code_commits | B-tree | project_id, commit_time DESC | 项目代码查询 |
| code_commits | GIN | commit_message (全文) | 提交信息搜索 |
| token_usage | B-tree | user_id, usage_date | Token统计 |
| bug_records | B-tree | project_id, status, severity | Bug筛选 |
| bug_records | GIN | title, description (全文) | Bug搜索 |

---

## 二、UI/UX 设计要点提炼

### 2.1 设计系统规范

#### 色彩系统
```css
Primary: #1890FF        /* 主按钮、链接 */
Success: #52C41A        /* 成功状态 */
Warning: #FAAD14        /* 警告提示 */
Error: #F5222D          /* 错误状态 */
Title: #262626          /* 主标题 */
Text: #595959           /* 正文 */
Text Secondary: #8C8C8C /* 次要文本 */
Border: #D9D9D9         /* 边框 */
Background: #F5F5F5     /* 页面背景 */
```

#### 间距系统（8px基准）
```
XS: 4px  | SM: 8px  | MD: 16px | LG: 24px | XL: 32px | XXL: 48px
```

#### 响应式断点
```
XS: <576px  | SM: ≥576px | MD: ≥768px | LG: ≥992px | XL: ≥1200px | XXL: ≥1600px
```

### 2.2 页面清单（9个核心页面）

| 页面 | 路径 | 核心组件 | 数据来源 |
|------|------|----------|----------|
| 登录页 | /login | 登录表单卡片 | auth/login API |
| 首页Dashboard | /dashboard | 数据卡片、趋势图、排名 | stats/global/* API |
| 全局统计 | /stats/global | 多系列折线图、双轴图、排行榜 | stats/global/* API |
| 项目列表 | /projects | 表格/卡片视图、筛选器 | projects API |
| 项目详情 | /projects/:id | 选项卡、数据卡片、图表 | stats/projects/:id/* API |
| 个人统计 | /stats/personal | 日历热力图、对比图 | stats/personal/* API |
| 项目配置 | /config/projects | 表格、编辑弹窗 | config/projects API |
| 权限管理 | /config/permissions | 角色表格、权限树 | auth/roles API |
| 数据源配置 | /config/data-sources | 状态卡片、配置表单 | config/data-sources API |
| 同步任务 | /sync/tasks | 状态表格、进度条 | sync/tasks API |

### 2.3 核心组件规格

#### 数据卡片
- 尺寸: 280px × 120px
- 内边距: 24px
- 圆角: 8px
- 阴影: shadow
- 结构: 标题(14px灰色) + 数值(32px粗体) + 趋势指示器

#### 图表规格
```
Token趋势图: 平滑折线图, 高300px, 多系列(按平台)
活跃度图: 双轴图, 左Y轴柱状(用户数), 右Y轴折线(项目数)
Bug趋势图: 堆叠面积图, 系列: 新增(绿)/解决(蓝)/未解决(红)
代码提交图: 堆叠面积图, 系列: 新增(绿)/删除(红)
AI采纳率: 仪表盘 + 饼图
```

#### 表格规格
```
排名表格: 排名(1-3名带奖牌图标) + 用户 + 部门 + 指标 + 趋势
项目表格: 名称 + 阶段 + 状态(彩色圆点) + 成员数 + Bug数 + 进度
任务表格: 类型 + 数据源 + 状态(图标+文字) + 进度条 + 时间
```

#### 弹窗规格
```
表单弹窗: 宽600px, 内边距24px, 圆角12px, 阴影shadow-lg
登录卡片: 宽400px, 内边距48px, 圆角12px
```

---

## 三、精确研发计划

### 阶段一：数据库层实现（Week 1 Day 1-2）

#### 任务 1.1: 数据库初始化脚本
**设计输入**: S6-A02 第2-3章

**文件清单**:
```
backend/app/db/migrations/001_initial_schema.py
backend/app/db/init_scripts/01_create_database.sql
backend/app/db/init_scripts/02_create_enums.sql
backend/app/db/init_scripts/03_create_tables.sql
backend/app/db/init_scripts/04_create_indexes.sql
backend/app/db/init_scripts/05_create_functions.sql
backend/app/db/init_scripts/06_create_triggers.sql
backend/app/db/init_scripts/07_insert_initial_data.sql
```

**具体实现内容**:

```python
# 001_initial_schema.py - Alembic迁移
# 按依赖顺序创建表

# 1. 枚举类型 (02_create_enums.sql)
- project_stage ENUM
- project_status ENUM
- bug_severity ENUM
- bug_status ENUM
- bug_priority ENUM
- ai_suggestion_type ENUM
- sync_task_status ENUM
- sync_task_type ENUM

# 2. 基础表 (03_create_tables.sql)
- roles (id, name, description, permissions JSONB)
- users (id, username, email, password_hash, department, role_id)
- projects (id, name, code, description, stage, status, manager_id, gitlab_repo_id, zendao_project_id)
- project_members (id, project_id, user_id, role, joined_at, left_at)
- user_accounts (id, user_id, platform, account_id, api_token_encrypted)

# 3. 数据表 (03_create_tables.sql)
- code_commits - 分区表设计
- token_usage - 分区表设计
- bug_records
- ai_suggestions
- data_sources (config JSONB)
- sync_tasks
- stats_snapshots (metrics JSONB)
- audit_logs

# 4. 索引 (04_create_indexes.sql)
# 按S6-A02设计创建所有B-tree和GIN索引

# 5. 函数和触发器 (05-06)
- update_updated_at_column()
- log_audit_changes()
- create_monthly_partition()
- calculate_project_stats()
```

**验收标准**:
- [ ] 所有12个表创建成功
- [ ] 8个枚举类型定义完成
- [ ] 分区表按月分区（2026年12个月）
- [ ] 所有索引创建完成
- [ ] 触发器工作正常（updated_at自动更新）
- [ ] 初始角色数据插入
- [ ] Alembic迁移可正常升级/降级

---

#### 任务 1.2: SQLAlchemy模型定义
**设计输入**: S6-A02 表结构

**文件清单**:
```
backend/app/db/models/__init__.py
backend/app/db/models/base.py          # 基础模型
backend/app/db/models/user.py          # User, Role
backend/app/db/models/project.py       # Project, ProjectMember
backend/app/db/models/config.py        # UserAccount, DataSource
backend/app/db/models/stats.py         # CodeCommit, TokenUsage, BugRecord, AISuggestion
backend/app/db/models/sync.py          # SyncTask, StatsSnapshot
backend/app/db/models/audit.py         # AuditLog
```

**模型实现要点**:

```python
# backend/app/db/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    permissions = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    department = Column(String(50), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="users")

# backend/app/db/models/stats.py
# 分区表特殊处理
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY

class CodeCommit(Base):
    __tablename__ = "code_commits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    commit_hash = Column(String(64), nullable=False)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    language = Column(String(20), nullable=False)
    file_count = Column(Integer, default=0)
    commit_message = Column(Text)
    commit_time = Column(DateTime, nullable=False, primary_key=True)  # 分区键
    is_ai_generated = Column(Boolean, default=False)
    ai_suggestion_ids = Column(ARRAY(Integer))
    branch_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 复合主键: (id, commit_time) for partitioning
    __table_args__ = (
        PrimaryKeyConstraint('id', 'commit_time'),
    )
```

**验收标准**:
- [ ] 所有模型与数据库表结构一致
- [ ] 关系定义正确（relationship）
- [ ] 分区表模型正确处理复合主键
- [ ] JSONB字段类型正确
- [ ] 枚举类型使用SQLAlchemy Enum

---

### 阶段二：后端基础架构（Week 1 Day 3-4）

#### 任务 2.1: 核心配置与依赖
**文件清单**:
```
backend/app/core/config.py          # 扩展配置
backend/app/core/security.py        # 安全工具
backend/app/core/exceptions.py      # 自定义异常
backend/app/core/dependencies.py    # FastAPI依赖
backend/app/core/logging.py         # 结构化日志
backend/app/core/audit.py           # 审计上下文
```

**实现要点**:

```python
# backend/app/core/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# backend/app/core/audit.py
# 审计上下文管理器，用于传递当前用户ID到数据库触发器
from contextvars import ContextVar

audit_user_id: ContextVar[int] = ContextVar("audit_user_id", default=None)

@contextmanager
def set_audit_user(user_id: int):
    token = audit_user_id.set(user_id)
    try:
        yield
    finally:
        audit_user_id.reset(token)
```

---

#### 任务 2.2: 中间件与异常处理
**文件清单**:
```
backend/app/middlewares/__init__.py
backend/app/middlewares/logging.py      # 请求日志
backend/app/middlewares/audit.py        # 审计上下文
backend/app/middlewares/error_handler.py # 全局错误处理
```

**实现要点**:

```python
# backend/app/middlewares/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail, "code": exc.status_code}
            )
        except Exception as exc:
            logger.exception("Unhandled exception")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "code": 500}
            )
```

---

#### 任务 2.3: Pydantic模型定义
**文件清单**:
```
backend/app/schemas/__init__.py
backend/app/schemas/base.py           # 基础响应
backend/app/schemas/auth.py           # 认证相关
backend/app/schemas/user.py           # 用户相关
backend/app/schemas/project.py        # 项目相关
backend/app/schemas/stats.py          # 统计相关
backend/app/schemas/config.py         # 配置相关
backend/app/schemas/sync.py           # 同步相关
```

**实现要点**:

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: "UserInfo"

class UserInfo(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True

# backend/app/schemas/stats.py
from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class TokenTrendPoint(BaseModel):
    date: date
    token_count: int
    api_calls: int
    mom_change: Optional[float] = None  # 环比
    yoy_change: Optional[float] = None  # 同比

class TokenTrendResponse(BaseModel):
    period: str  # daily/weekly/monthly
    data_points: List[TokenTrendPoint]
    summary: dict

class ProjectStatsResponse(BaseModel):
    project_id: int
    project_name: str
    period: dict
    code_stats: dict
    token_stats: dict
    bug_stats: dict
    ai_adoption: dict
    team_stats: dict
```

---

### 阶段三：前端基础架构（Week 1 Day 5）

#### 任务 3.1: 项目结构与配置
**文件清单**:
```
frontend/src/styles/variables.scss    # SCSS变量
frontend/src/styles/element-plus.scss # Element Plus主题覆盖
frontend/src/types/api.ts             # API类型定义
frontend/src/types/components.ts      # 组件类型定义
```

**实现要点**:

```scss
// frontend/src/styles/variables.scss
// 与S6-A03设计系统一致

// Colors
$primary: #1890FF;
$primary-hover: #40A9FF;
$primary-active: #096DD9;
$success: #52C41A;
$warning: #FAAD14;
$error: #F5222D;
$title: #262626;
$text: #595959;
$text-secondary: #8C8C8C;
$border: #D9D9D9;
$bg: #F5F5F5;

// Spacing
$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 16px;
$spacing-lg: 24px;
$spacing-xl: 32px;
$spacing-xxl: 48px;

// Border Radius
$radius-sm: 4px;
$radius-md: 6px;
$radius-lg: 8px;
$radius-xl: 12px;
```

---

#### 任务 3.2: 路由与状态管理
**文件清单**:
```
frontend/src/router/index.ts          # 路由配置
frontend/src/router/guards.ts         # 路由守卫
frontend/src/stores/auth.ts           # 认证状态
frontend/src/stores/app.ts            # 应用状态
frontend/src/stores/permission.ts     # 权限状态
```

**实现要点**:

```typescript
// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('@/views/dashboard/index.vue') },
      {
        path: 'stats',
        children: [
          { path: 'global', component: () => import('@/views/stats/global/index.vue') },
          { path: 'projects/:id', component: () => import('@/views/stats/project/index.vue') },
          { path: 'personal', component: () => import('@/views/stats/personal/index.vue') }
        ]
      },
      {
        path: 'config',
        children: [
          { path: 'projects', component: () => import('@/views/config/projects/index.vue') },
          { path: 'permissions', component: () => import('@/views/config/permissions/index.vue') },
          { path: 'data-sources', component: () => import('@/views/config/data-sources/index.vue') }
        ]
      },
      { path: 'sync/tasks', component: () => import('@/views/sync/tasks/index.vue') }
    ]
  }
]
```

---

#### 任务 3.3: HTTP客户端与工具
**文件清单**:
```
frontend/src/utils/request.ts         # Axios封装
frontend/src/utils/permission.ts      # 权限检查
frontend/src/utils/format.ts          # 格式化工具
frontend/src/utils/date.ts            # 日期工具
```

**实现要点**:

```typescript
// frontend/src/utils/request.ts
import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// 请求拦截器 - 添加Token
request.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器 - Token刷新
request.interceptors.response.use(
  response => response.data,
  async error => {
    if (error.response?.status === 401) {
      // 尝试刷新Token
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post('/auth/refresh', { refresh_token: refreshToken })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          // 重试原请求
          return request(error.config)
        } catch {
          // 刷新失败，跳转登录
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
```

---

### 阶段四：认证与权限模块（Week 2 Day 1-2）

#### 任务 4.1: 后端认证API
**文件清单**:
```
backend/app/api/v1/auth.py            # 认证路由
backend/app/services/auth_service.py  # 认证服务
```

**接口实现**:

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    auth_service = AuthService(db)
    return await auth_service.authenticate(form_data.username, form_data.password)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """刷新Token"""
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(refresh_token)

@router.get("/permissions", response_model=list[str])
async def get_permissions(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户权限"""
    return current_user.role.permissions
```

---

#### 任务 4.2: 前端登录页面
**文件清单**:
```
frontend/src/views/login/index.vue    # 登录页面
```

**实现规格**（按S6-A03 4.1设计）:

```vue
<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="title">Coding Agent Stats</h1>
      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.remember">记住我</el-checkbox>
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          @click="handleLogin"
          style="width: 100%"
        >
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg;
}

.login-card {
  width: 400px;
  padding: 48px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.title {
  text-align: center;
  font-size: 24px;
  margin-bottom: 32px;
  color: $title;
}
</style>
```

---

### 阶段五：配置管理模块（Week 2 Day 3-5）

#### 任务 5.1: 项目配置后端
**文件清单**:
```
backend/app/api/v1/projects.py
backend/app/services/project_service.py
```

**接口实现**:

```python
# backend/app/api/v1/projects.py
@router.get("/config/projects", response_model=PageResponse[ProjectListItem])
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表"""
    service = ProjectService(db)
    return await service.list_projects(
        page=page,
        page_size=page_size,
        filters={"stage": stage, "status": status, "keyword": keyword}
    )

@router.post("/config/projects", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("config:manage"))
):
    """创建项目"""
    service = ProjectService(db)
    return await service.create_project(data)
```

---

#### 任务 5.2: 项目配置前端
**文件清单**:
```
frontend/src/views/config/projects/index.vue      # 项目列表
frontend/src/views/config/projects/form.vue       # 项目表单弹窗
```

**实现规格**（按S6-A03 4.7设计）:

```vue
<!-- 项目列表 -->
<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>项目配置</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>新建项目
      </el-button>
    </div>

    <!-- 筛选器 -->
    <el-form :inline="true" class="filter-form">
      <el-form-item>
        <el-select v-model="filters.stage" placeholder="全部阶段" clearable>
          <el-option
            v-for="stage in stages"
            :key="stage.value"
            :label="stage.label"
            :value="stage.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="filters.status" placeholder="全部状态" clearable>
          <el-option label="Active" value="active" />
          <el-option label="Archived" value="archived" />
        </el-select>
      </el-form-item>
    </el-form>

    <!-- 项目表格 -->
    <el-table :data="projects" v-loading="loading">
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="stage" label="阶段" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.stage }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <span class="status-dot" :class="row.status"></span>
          {{ row.status }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link @click="handleEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}
.status-dot.active { background: #52C41A; }
.status-dot.archived { background: #FAAD14; }
.status-dot.cancelled { background: #F5222D; }
</style>
```

---

### 阶段六：数据同步模块（Week 3）

#### 任务 6.1: 同步服务实现
**文件清单**:
```
backend/app/services/sync/base.py           # 同步基类
backend/app/services/sync/gitlab_sync.py    # GitLab同步
backend/app/services/sync/trae_sync.py      # Trae同步
backend/app/services/sync/zendao_sync.py    # 禅道同步
backend/app/services/sync/scheduler.py      # 调度器
```

**实现要点**:

```python
# backend/app/services/sync/base.py
from abc import ABC, abstractmethod
from datetime import date
from typing import List

class BaseSync(ABC):
    """数据同步基类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = structlog.get_logger()

    @abstractmethod
    async def sync(self, start_date: date, end_date: date) -> SyncResult:
        """执行同步"""
        pass

    async def record_sync_task(
        self,
        task_type: str,
        status: str,
        records_processed: int = 0,
        records_failed: int = 0,
        error_message: str = None
    ):
        """记录同步任务"""
        task = SyncTask(
            task_type=task_type,
            source_type=self.source_type,
            status=status,
            records_processed=records_processed,
            records_failed=records_failed,
            error_message=error_message
        )
        self.db.add(task)
        await self.db.commit()

# backend/app/services/sync/gitlab_sync.py
class GitLabSync(BaseSync):
    source_type = "gitlab"

    async def sync(self, start_date: date, end_date: date) -> SyncResult:
        """同步GitLab代码提交数据"""
        self.logger.info("Starting GitLab sync", start_date=start_date, end_date=end_date)

        # 1. 获取所有配置了GitLab的项目
        projects = await self.get_gitlab_projects()

        total_commits = 0
        for project in projects:
            # 2. 调用GitLab API获取commits
            commits = await self.fetch_commits(
                project.gitlab_repo_id,
                start_date,
                end_date
            )

            # 3. 转换并保存
            for commit_data in commits:
                commit = await self.transform_commit(commit_data, project.id)
                self.db.add(commit)
                total_commits += 1

            await self.db.commit()

        return SyncResult(
            records_processed=total_commits,
            records_failed=0
        )

    async def fetch_commits(self, repo_id: int, since: date, until: date) -> List[dict]:
        """调用GitLab API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITLAB_URL}/api/v4/projects/{repo_id}/repository/commits",
                headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
                params={"since": since.isoformat(), "until": until.isoformat()}
            )
            response.raise_for_status()
            return response.json()
```

---

### 阶段七：统计模块（Week 4-5）

#### 任务 7.1: 全局统计后端
**文件清单**:
```
backend/app/services/stats/global_stats.py
backend/app/api/v1/stats/global.py
```

**实现要点**:

```python
# backend/app/services/stats/global_stats.py
class GlobalStatsService:
    """全局统计服务"""

    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.cache_ttl = 3600  # 1小时缓存

    async def get_token_trend(
        self,
        start_date: date,
        end_date: date,
        period: str = "daily",
        platform: Optional[str] = None
    ) -> TokenTrendResponse:
        """获取Token使用趋势"""
        # 1. 生成缓存key
        cache_key = f"stats:token_trend:{start_date}:{end_date}:{period}:{platform}"

        # 2. 尝试从缓存获取
        cached = await self.redis.get(cache_key)
        if cached:
            return TokenTrendResponse.parse_raw(cached)

        # 3. 查询数据库
        query = """
            SELECT
                usage_date,
                SUM(token_count) as total_tokens,
                SUM(api_calls) as total_calls
            FROM token_usage
            WHERE usage_date BETWEEN :start_date AND :end_date
              AND (:platform IS NULL OR platform = :platform)
            GROUP BY usage_date
            ORDER BY usage_date
        """
        result = await self.db.execute(
            text(query),
            {"start_date": start_date, "end_date": end_date, "platform": platform}
        )
        rows = result.fetchall()

        # 4. 按period聚合数据
        data_points = self.aggregate_by_period(rows, period)

        # 5. 计算汇总
        summary = {
            "total_tokens": sum(r.total_tokens for r in rows),
            "total_calls": sum(r.total_calls for r in rows),
            "avg_daily_tokens": sum(r.total_tokens for r in rows) / len(rows) if rows else 0
        }

        response = TokenTrendResponse(
            period=period,
            data_points=data_points,
            summary=summary
        )

        # 6. 写入缓存
        await self.redis.setex(cache_key, self.cache_ttl, response.json())

        return response
```

---

#### 任务 7.2: 全局统计前端
**文件清单**:
```
frontend/src/views/stats/global/index.vue
frontend/src/components/charts/line-chart.vue
frontend/src/components/charts/bar-chart.vue
frontend/src/components/charts/ranking-table.vue
```

**实现规格**（按S6-A03 4.3设计）:

```vue
<template>
  <div class="global-stats-page">
    <div class="page-header">
      <h2>全局统计</h2>
      <time-range-picker v-model="timeRange" />
    </div>

    <!-- 选项卡 -->
    <el-tabs v-model="activeTab">
      <el-tab-pane label="Token 使用趋势" name="token">
        <line-chart
          :data="tokenTrendData"
          :series="platformSeries"
          height="300px"
        />
      </el-tab-pane>

      <el-tab-pane label="活跃度趋势" name="activity">
        <dual-axis-chart
          :bar-data="activeUsersData"
          :line-data="activeProjectsData"
          height="300px"
        />
      </el-tab-pane>

      <el-tab-pane label="人员排名" name="ranking">
        <ranking-table :data="topUsers" :columns="rankingColumns" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useGlobalStats } from './composables/useGlobalStats'

const activeTab = ref('token')
const timeRange = ref({ start: null, end: null })

const { tokenTrendData, topUsers, loading, fetchData } = useGlobalStats()

watch(timeRange, fetchData, { immediate: true })
</script>
```

---

#### 任务 7.3: 图表组件库
**文件清单**:
```
frontend/src/components/charts/line-chart.vue       # 折线图
frontend/src/components/charts/bar-chart.vue        # 柱状图
frontend/src/components/charts/pie-chart.vue        # 饼图
frontend/src/components/charts/dual-axis-chart.vue  # 双轴图
frontend/src/components/charts/heatmap-chart.vue    # 热力图
frontend/src/components/charts/gauge-chart.vue      # 仪表盘
```

**实现要点**:

```vue
<!-- line-chart.vue -->
<template>
  <div ref="chartRef" :style="{ height }"></div>
</template>

<script setup>
import * as echarts from 'echarts'
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  data: Array,
  series: Array,
  height: { type: String, default: '300px' }
})

const chartRef = ref()
let chart = null

onMounted(() => {
  chart = echarts.init(chartRef.value)
  updateChart()
})

watch(() => props.data, updateChart, { deep: true })

function updateChart() {
  const option = {
    color: ['#1890FF', '#52C41A', '#FAAD14'],
    tooltip: { trigger: 'axis' },
    legend: { data: props.series.map(s => s.name) },
    xAxis: {
      type: 'category',
      data: props.data.map(d => d.date)
    },
    yAxis: { type: 'value' },
    series: props.series.map(s => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: props.data.map(d => d[s.field])
    }))
  }
  chart.setOption(option)
}
</script>
```

---

### 阶段八：项目统计模块（Week 5）

#### 任务 8.1: 项目统计后端
**文件清单**:
```
backend/app/services/stats/project_stats.py
backend/app/api/v1/stats/projects.py
```

**接口实现**:

```python
# backend/app/api/v1/stats/projects.py
@router.get("/stats/projects/{project_id}", response_model=ProjectStatsResponse)
async def get_project_stats(
    project_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目综合统计"""
    # 检查权限
    await check_project_permission(current_user, project_id, db)

    service = ProjectStatsService(db)
    return await service.get_project_overview(project_id, start_date, end_date)

@router.get("/stats/projects/{project_id}/bug-trend")
async def get_project_bug_trend(
    project_id: int,
    start_date: date,
    end_date: date,
    period: str = "daily",
    db: AsyncSession = Depends(get_db)
):
    """获取项目Bug趋势"""
    service = ProjectStatsService(db)
    return await service.get_bug_trend(project_id, start_date, end_date, period)
```

---

#### 任务 8.2: 项目统计前端
**文件清单**:
```
frontend/src/views/stats/project/index.vue      # 项目详情页
frontend/src/views/stats/project/overview.vue   # 概览选项卡
frontend/src/views/stats/project/bug-trend.vue  # Bug趋势选项卡
frontend/src/views/stats/project/ai-adoption.vue # AI采纳率选项卡
```

**实现规格**（按S6-A03 4.5设计）:

```vue
<template>
  <div class="project-stats-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-button link @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>返回
      </el-button>
      <h2>{{ projectName }}</h2>
      <el-button v-permission="'config:manage'">编辑</el-button>
    </div>

    <!-- 选项卡 -->
    <el-tabs v-model="activeTab" class="project-tabs">
      <el-tab-pane label="概览" name="overview">
        <project-overview :project-id="projectId" />
      </el-tab-pane>
      <el-tab-pane label="代码统计" name="code">
        <project-code-stats :project-id="projectId" />
      </el-tab-pane>
      <el-tab-pane label="Bug 趋势" name="bugs">
        <project-bug-trend :project-id="projectId" />
      </el-tab-pane>
      <el-tab-pane label="AI 采纳" name="ai">
        <project-ai-adoption :project-id="projectId" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.project-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.project-tabs :deep(.el-tabs__item) {
  height: 48px;
  font-size: 14px;
}

.project-tabs :deep(.el-tabs__active-bar) {
  height: 2px;
}
</style>
```

---

### 阶段九：个人统计模块（Week 5）

#### 任务 9.1: 个人统计后端
**文件清单**:
```
backend/app/services/stats/personal_stats.py
backend/app/api/v1/stats/personal.py
```

**接口实现**:

```python
# backend/app/api/v1/stats/personal.py
@router.get("/stats/personal/code")
async def get_personal_code_stats(
    user_id: Optional[int] = None,  # 不传则查当前用户
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取个人代码统计"""
    target_user_id = user_id or current_user.id

    # 权限检查：只能查看自己或下属
    if target_user_id != current_user.id:
        await check_subordinate_permission(current_user, target_user_id, db)

    service = PersonalStatsService(db)
    return await service.get_code_stats(target_user_id, start_date, end_date)
```

---

#### 任务 9.2: 个人统计前端
**文件清单**:
```
frontend/src/views/stats/personal/index.vue
frontend/src/components/charts/calendar-heatmap.vue
```

**实现规格**（按S6-A03 4.6设计）:

```vue
<template>
  <div class="personal-stats-page">
    <div class="page-header">
      <h2>个人统计</h2>
      <time-range-picker v-model="timeRange" />
    </div>

    <!-- 数据概览卡片 -->
    <el-row :gutter="16" class="stats-cards">
      <el-col :span="6">
        <stat-card title="提交次数" :value="codeStats.total_commits" />
      </el-col>
      <el-col :span="6">
        <stat-card title="代码行数" :value="codeStats.net_additions" />
      </el-col>
      <el-col :span="6">
        <stat-card title="Token 用量" :value="tokenStats.total_tokens" />
      </el-col>
      <el-col :span="6">
        <stat-card title="Bug 率" :value="bugStats.bug_rate" suffix="%" />
      </el-col>
    </el-row>

    <!-- 代码提交日历热力图 -->
    <el-card class="heatmap-card">
      <template #header>代码提交日历</template>
      <calendar-heatmap
        :data="commitCalendarData"
        :end-date="new Date()"
        :days="365"
      />
    </el-card>
  </div>
</template>
```

---

## 四、开发顺序与依赖关系

```
Week 1:
  Day 1-2: [DB] 数据库初始化 → [DB] SQLAlchemy模型
  Day 3-4: [BE] 后端基础架构 → [BE] Pydantic模型
  Day 5:   [FE] 前端基础架构

Week 2:
  Day 1-2: [BE+FE] 认证与权限模块
  Day 3-5: [BE+FE] 配置管理模块（项目、数据源、账号）

Week 3:
  Day 1-5: [BE+FE] 数据同步模块（GitLab、Trae、禅道、调度）

Week 4:
  Day 1-2: [BE+FE] 全局统计模块
  Day 3-5: [BE+FE] 项目统计模块

Week 5:
  Day 1-2: [BE+FE] 个人统计模块
  Day 3-5: 集成测试、Bug修复、性能优化
```

---

## 五、验收检查清单

### 功能验收
- [ ] 25个功能全部实现
- [ ] 所有API接口测试通过
- [ ] 前端页面与设计稿一致
- [ ] 权限控制正确

### 性能验收
- [ ] 页面加载 < 2s
- [ ] API响应 < 500ms（缓存命中）
- [ ] 数据库查询优化（EXPLAIN检查）
- [ ] 分区表查询性能达标

### UI验收
- [ ] 色彩与设计系统一致
- [ ] 间距符合8px网格
- [ ] 响应式布局正常
- [ ] 图表交互流畅

### 代码质量
- [ ] 单元测试覆盖率 > 80%
- [ ] ruff检查通过
- [ ] mypy类型检查通过
- [ ] 前端TypeScript无错误
