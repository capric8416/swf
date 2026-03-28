# 研发详细计划 - Coding Agent 绩效统计平台

## 项目概览

**项目名称**: 研发中心 Coding Agent 绩效统计平台 (P000001)
**技术栈**: Vue 3 + TypeScript + FastAPI + PostgreSQL + Redis
**研发阶段**: 代码实现阶段

---

## 一、功能清单与研发顺序

### 核心模块划分

| 模块编号 | 模块名称 | 优先级 | 功能数量 | 预估工时 |
|:--------:|----------|:------:|:--------:|:--------:|
| MOD-007 | 系统基础模块 | P0 | 3个 | 16h |
| MOD-005 | 权限管理模块 | P0 | 3个 | 20h |
| MOD-004 | 配置管理模块 | P0 | 3个 | 24h |
| MOD-006 | 数据同步模块 | P0 | 4个 | 32h |
| MOD-001 | 全局统计模块 | P0 | 3个 | 24h |
| MOD-002 | 项目统计模块 | P0 | 5个 | 32h |
| MOD-003 | 个人统计模块 | P0 | 3个 | 20h |

**总计**: 25个功能，168工时

---

## 二、详细研发计划

### 阶段一：基础框架搭建 (MOD-007)

#### 任务 1.1: 数据库初始化
**功能**: 创建数据库表结构
**文件**:
- `backend/migrations/versions/001_initial_schema.py` - 初始迁移
- `backend/app/db/models.py` - SQLAlchemy 模型定义

**具体表结构**:
```sql
-- 用户表 (users)
-- 角色表 (roles)
-- 项目表 (projects)
-- 项目成员表 (project_members)
-- 用户平台账号表 (user_platform_accounts)
```

**验收标准**:
- [ ] 所有表创建成功
- [ ] 外键约束正确
- [ ] 索引创建完成
- [ ] 初始数据（角色）插入

---

#### 任务 1.2: 后端基础架构
**功能**: 配置日志、异常处理、数据库连接
**文件**:
- `backend/app/core/exceptions.py` - 自定义异常
- `backend/app/core/dependencies.py` - FastAPI 依赖
- `backend/app/middlewares/logging.py` - 请求日志中间件
- `backend/app/middlewares/error_handler.py` - 全局错误处理

**验收标准**:
- [ ] 结构化日志输出
- [ ] 统一异常响应格式
- [ ] 请求日志记录
- [ ] 数据库连接池配置

---

#### 任务 1.3: 前端基础架构
**功能**: 配置路由、状态管理、HTTP客户端
**文件**:
- `frontend/src/router/index.ts` - 路由配置
- `frontend/src/stores/index.ts` - Pinia 配置
- `frontend/src/utils/request.ts` - Axios 封装
- `frontend/src/types/index.ts` - 全局类型定义

**验收标准**:
- [ ] 路由守卫实现
- [ ] 请求拦截器（Token）
- [ ] 响应拦截器（错误处理）
- [ ] 类型定义完整

---

### 阶段二：权限管理模块 (MOD-005)

#### 任务 2.1: 用户认证 - 登录功能
**功能**: F-016 用户认证
**接口**: `POST /api/v1/auth/login`

**后端文件**:
- `backend/app/models/auth.py` - Pydantic 模型
- `backend/app/services/auth_service.py` - 认证服务
- `backend/app/api/v1/auth.py` - 登录接口

**前端文件**:
- `frontend/src/views/login/index.vue` - 登录页面
- `frontend/src/stores/auth.ts` - 认证状态管理

**接口契约**:
```json
// Request
{
  "username": "string",
  "password": "string"
}

// Response
{
  "access_token": "string",
  "refresh_token": "string",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "张三",
    "role": "admin"
  }
}
```

**验收标准**:
- [ ] 密码 BCrypt 加密
- [ ] JWT Token 生成
- [ ] 登录表单验证
- [ ] Token 本地存储

---

#### 任务 2.2: Token 刷新机制
**功能**: Token 自动刷新
**接口**: `POST /api/v1/auth/refresh`

**后端文件**:
- `backend/app/services/auth_service.py` - refresh_token 方法
- `backend/app/api/v1/auth.py` - 刷新接口

**前端文件**:
- `frontend/src/utils/request.ts` - 401 拦截刷新

**验收标准**:
- [ ] Access Token 过期前自动刷新
- [ ] Refresh Token 轮换机制
- [ ] 刷新失败跳转登录

---

#### 任务 2.3: 权限控制
**功能**: F-017 数据访问控制 + F-015 角色权限管理
**接口**:
- `GET /api/v1/auth/permissions` - 获取当前用户权限
- `GET /api/v1/auth/roles` - 角色列表
- `POST /api/v1/auth/roles` - 创建角色

**后端文件**:
- `backend/app/core/security.py` - 权限检查装饰器
- `backend/app/services/role_service.py` - 角色服务
- `backend/app/api/v1/roles.py` - 角色接口

**前端文件**:
- `frontend/src/directives/permission.ts` - 权限指令
- `frontend/src/components/Permission/index.vue` - 权限组件
- `frontend/src/views/settings/roles/index.vue` - 角色管理页面

**权限定义**:
```python
PERMISSIONS = [
    "stats:global:view",    # 查看全局统计
    "stats:project:view",   # 查看项目统计
    "stats:personal:view",  # 查看个人统计
    "config:manage",        # 配置管理
    "sync:trigger",         # 触发同步
    "user:manage",          # 用户管理
    "role:manage",          # 角色管理
]
```

**验收标准**:
- [ ] 权限装饰器工作正常
- [ ] 前端权限指令实现
- [ ] 无权限时隐藏菜单/按钮
- [ ] 角色 CRUD 完成

---

### 阶段三：配置管理模块 (MOD-004)

#### 任务 3.1: 项目基础信息管理
**功能**: F-012 项目基础信息管理
**接口**:
- `GET /api/v1/config/projects` - 项目列表
- `POST /api/v1/config/projects` - 创建项目
- `PUT /api/v1/config/projects/{id}` - 更新项目
- `DELETE /api/v1/config/projects/{id}` - 删除项目

**后端文件**:
- `backend/app/models/project.py` - 项目模型
- `backend/app/services/project_service.py` - 项目服务
- `backend/app/api/v1/projects.py` - 项目接口

**前端文件**:
- `frontend/src/views/config/projects/index.vue` - 项目列表
- `frontend/src/views/config/projects/form.vue` - 项目表单

**数据模型**:
```python
class ProjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str]
    stage: ProjectStage
    status: ProjectStatus
    manager_id: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
```

**验收标准**:
- [ ] 项目 CRUD 完成
- [ ] 表单验证
- [ ] 列表分页
- [ ] 搜索过滤

---

#### 任务 3.2: 项目数据源关联配置
**功能**: F-013 项目数据源关联配置
**接口**:
- `GET /api/v1/config/projects/{id}/data-sources` - 获取数据源配置
- `PUT /api/v1/config/projects/{id}/data-sources` - 更新数据源配置

**后端文件**:
- `backend/app/services/data_source_service.py` - 数据源服务
- `backend/app/api/v1/data_sources.py` - 数据源接口

**前端文件**:
- `frontend/src/views/config/projects/data-source.vue` - 数据源配置

**数据源配置**:
```json
{
  "gitlab_repo_id": 123,
  "gitlab_repo_url": "https://gitlab.com/xxx",
  "zendao_project_id": 456,
  "zendao_project_key": "PROJ"
}
```

**验收标准**:
- [ ] 数据源配置表单
- [ ] 配置验证
- [ ] 关联状态显示

---

#### 任务 3.3: 人员平台账号配置
**功能**: F-014 人员平台账号配置
**接口**:
- `GET /api/v1/config/user-accounts` - 用户账号列表
- `POST /api/v1/config/user-accounts` - 配置用户账号

**数据库变更**:
```sql
-- 用户平台账号表
CREATE TABLE user_platform_accounts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    platform VARCHAR(50),  -- 'trae', 'gitlab', 'zendao'
    account VARCHAR(100),
    created_at TIMESTAMP
);
```

**后端文件**:
- `backend/app/db/models.py` - 添加模型
- `backend/app/services/user_account_service.py` - 账号服务
- `backend/app/api/v1/user_accounts.py` - 账号接口

**前端文件**:
- `frontend/src/views/config/users/accounts.vue` - 账号配置页面

**验收标准**:
- [ ] 账号绑定功能
- [ ] 多平台账号管理
- [ ] 账号格式验证

---

### 阶段四：数据同步模块 (MOD-006)

#### 任务 4.1: 数据库表 - 同步相关表
**功能**: 创建同步相关数据表
**迁移文件**: `backend/migrations/versions/002_sync_tables.py`

**新增表**:
```sql
-- 代码提交记录表 (code_commits)
-- Token 使用记录表 (token_usage)
-- Bug 记录表 (bugs)
-- AI 建议记录表 (ai_suggestions)
-- 同步任务表 (sync_tasks)
-- 同步日志表 (sync_logs)
```

**验收标准**:
- [ ] 所有表创建成功
- [ ] 分区表配置（token_usage）
- [ ] 索引优化

---

#### 任务 4.2: GitLab 数据同步
**功能**: F-019 GitLab 数据同步
**接口**: `POST /api/v1/sync/gitlab` - 手动触发同步

**后端文件**:
- `backend/app/services/sync/gitlab_sync.py` - GitLab 同步器
- `backend/app/services/sync/base.py` - 同步基类
- `backend/app/api/v1/sync.py` - 同步接口

**核心逻辑**:
```python
class GitLabSync(BaseSync):
    async def sync_commits(self, project_id: int, since: date, until: date):
        # 1. 获取项目 GitLab 配置
        # 2. 调用 GitLab API 获取 commits
        # 3. 解析代码行数变化
        # 4. 匹配用户账号
        # 5. 批量写入数据库
```

**验收标准**:
- [ ] GitLab API 调用
- [ ] Commit 数据解析
- [ ] 代码行数统计
- [ ] 增量同步支持

---

#### 任务 4.3: Trae 数据同步
**功能**: F-018 Trae 数据同步
**接口**: `POST /api/v1/sync/trae`

**后端文件**:
- `backend/app/services/sync/trae_sync.py` - Trae 同步器

**核心逻辑**:
```python
class TraeSync(BaseSync):
    async def sync_token_usage(self, since: date, until: date):
        # 1. 调用 Trae API 获取 Token 使用记录
        # 2. 数据转换
        # 3. 批量写入 token_usage 表
```

**验收标准**:
- [ ] Trae API 调用
- [ ] Token 数据解析
- [ ] 用户账号映射

---

#### 任务 4.4: 禅道数据同步
**功能**: F-020 禅道数据同步
**接口**: `POST /api/v1/sync/zendao`

**后端文件**:
- `backend/app/services/sync/zendao_sync.py` - 禅道同步器

**验收标准**:
- [ ] 禅道 API 调用
- [ ] Bug 数据解析
- [ ] 状态映射

---

#### 任务 4.5: 定时任务调度
**功能**: F-021 定时任务调度
**方案**: 使用 pg_cron (PostgreSQL 扩展)

**后端文件**:
- `backend/app/services/sync/scheduler.py` - 调度器
- `backend/app/celery_app.py` - Celery 配置（备用）

**定时任务**:
```sql
-- 每天凌晨 2 点执行全量同步
SELECT cron.schedule('daily-sync', '0 2 * * *',
  'SELECT sync_all_data()');
```

**验收标准**:
- [ ] 定时任务配置
- [ ] 同步状态查询
- [ ] 同步日志记录

---

### 阶段五：全局统计模块 (MOD-001)

#### 任务 5.1: Token 使用趋势看板
**功能**: F-001 全局 Token 使用趋势看板
**接口**: `GET /api/v1/stats/global/token-trend`

**后端文件**:
- `backend/app/services/stats/global_stats.py` - 全局统计服务
- `backend/app/api/v1/stats/global.py` - 全局统计接口

**前端文件**:
- `frontend/src/views/dashboard/global/token-trend.vue` - Token 趋势页面
- `frontend/src/components/charts/line-chart.vue` - 折线图组件

**接口响应**:
```json
{
  "period": "daily",
  "data_points": [
    {
      "date": "2026-03-27",
      "token_count": 150000,
      "api_calls": 3500,
      "mom_change": 0.15
    }
  ],
  "summary": {
    "total_tokens": 4500000,
    "total_calls": 105000,
    "avg_daily_tokens": 150000
  }
}
```

**验收标准**:
- [ ] 日/周/月维度切换
- [ ] 环比计算
- [ ] 缓存实现 (Redis)
- [ ] ECharts 折线图

---

#### 任务 5.2: 活跃度趋势
**功能**: F-002 全中心活跃度趋势
**接口**: `GET /api/v1/stats/global/activity-trend`

**前端文件**:
- `frontend/src/views/dashboard/global/activity-trend.vue`

**验收标准**:
- [ ] 活跃用户数统计
- [ ] 活跃项目数统计
- [ ] 双轴折线图

---

#### 任务 5.3: 高频使用人员 TOP 20
**功能**: F-003 高频使用人员 TOP 20
**接口**: `GET /api/v1/stats/global/top-users`

**前端文件**:
- `frontend/src/views/dashboard/global/top-users.vue`
- `frontend/src/components/charts/ranking-list.vue` - 排行榜组件

**验收标准**:
- [ ] TOP 20 排名
- [ ] 部门筛选
- [ ] 排行榜表格

---

### 阶段六：项目统计模块 (MOD-002)

#### 任务 6.1: 项目维度统计视图
**功能**: F-004 项目维度统计视图
**接口**: `GET /api/v1/stats/projects/{id}`

**后端文件**:
- `backend/app/services/stats/project_stats.py` - 项目统计服务
- `backend/app/api/v1/stats/projects.py` - 项目统计接口

**前端文件**:
- `frontend/src/views/dashboard/project/overview.vue` - 项目概览

**接口响应**:
```json
{
  "project_id": 1001,
  "project_name": "项目管理平台",
  "code_stats": {
    "total_commits": 350,
    "total_additions": 15000,
    "total_deletions": 5000
  },
  "token_stats": {
    "total_tokens": 800000,
    "total_calls": 20000
  },
  "bug_stats": {
    "new_bugs": 25,
    "resolved_bugs": 20,
    "bug_rate": 0.0025
  },
  "ai_adoption": {
    "ai_commits": 120,
    "adoption_rate": 0.34
  }
}
```

**验收标准**:
- [ ] 项目数据卡片
- [ ] 权限验证
- [ ] 时间范围筛选

---

#### 任务 6.2: 项目代码行排名
**功能**: F-005 项目代码行排名
**接口**: `GET /api/v1/stats/projects/{id}/code-rank`

**前端文件**:
- `frontend/src/views/dashboard/project/code-rank.vue`

**验收标准**:
- [ ] 新增/删除/净增切换
- [ ] 排行榜展示
- [ ] 堆叠柱状图

---

#### 任务 6.3: 项目 Bug 趋势看板
**功能**: F-006 项目 Bug 趋势看板
**接口**: `GET /api/v1/stats/projects/{id}/bug-trend`

**前端文件**:
- `frontend/src/views/dashboard/project/bug-trend.vue`

**验收标准**:
- [ ] Bug 趋势图
- [ ] 解决率计算
- [ ] Bug 率仪表盘

---

#### 任务 6.4: 项目 AI 代码采纳率
**功能**: F-007 项目 AI 代码采纳率
**接口**: `GET /api/v1/stats/projects/{id}/ai-adoption`

**前端文件**:
- `frontend/src/views/dashboard/project/ai-adoption.vue`

**验收标准**:
- [ ] 采纳率仪表盘
- [ ] 用户采纳率分布
- [ ] 饼图展示

---

#### 任务 6.5: 项目代码提交量排行
**功能**: F-008 项目代码提交量排行
**接口**: `GET /api/v1/stats/projects/{id}/commit-rank`

**前端文件**:
- `frontend/src/views/dashboard/project/commit-rank.vue`

**验收标准**:
- [ ] 提交次数排名
- [ ] 平均代码行数

---

### 阶段七：个人统计模块 (MOD-003)

#### 任务 7.1: 个人代码统计
**功能**: F-009 个人代码统计
**接口**: `GET /api/v1/stats/personal/code`

**后端文件**:
- `backend/app/services/stats/personal_stats.py` - 个人统计服务
- `backend/app/api/v1/stats/personal.py` - 个人统计接口

**前端文件**:
- `frontend/src/views/dashboard/personal/code-stats.vue`

**验收标准**:
- [ ] 代码提交统计
- [ ] 项目分布
- [ ] 日历热力图

---

#### 任务 7.2: 个人 Token 使用统计
**功能**: F-010 个人 Token 使用统计
**接口**: `GET /api/v1/stats/personal/token`

**前端文件**:
- `frontend/src/views/dashboard/personal/token-stats.vue`

**验收标准**:
- [ ] Token 使用量
- [ ] 平台分布
- [ ] 团队对比

---

#### 任务 7.3: 个人 Bug 率统计
**功能**: F-011 个人 Bug 率统计
**接口**: `GET /api/v1/stats/personal/bug-rate`

**前端文件**:
- `frontend/src/views/dashboard/personal/bug-stats.vue`

**验收标准**:
- [ ] Bug 统计
- [ ] 解决率
- [ ] Bug 率计算

---

## 三、文件结构规范

### 后端结构
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── projects.py
│   │       ├── roles.py
│   │       ├── sync.py
│   │       └── stats/
│   │           ├── global.py
│   │           ├── projects.py
│   │           └── personal.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   ├── db/
│   │   ├── base.py
│   │   └── models.py
│   ├── models/
│   │   ├── auth.py
│   │   ├── project.py
│   │   └── stats.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── project_service.py
│   │   ├── sync/
│   │   │   ├── base.py
│   │   │   ├── gitlab_sync.py
│   │   │   ├── trae_sync.py
│   │   │   └── zendao_sync.py
│   │   └── stats/
│   │       ├── global_stats.py
│   │       ├── project_stats.py
│   │       └── personal_stats.py
│   └── main.py
├── migrations/
├── tests/
└── pyproject.toml
```

### 前端结构
```
frontend/
├── src/
│   ├── api/
│   │   ├── auth.ts
│   │   ├── projects.ts
│   │   ├── sync.ts
│   │   └── stats.ts
│   ├── components/
│   │   ├── charts/
│   │   │   ├── line-chart.vue
│   │   │   ├── bar-chart.vue
│   │   │   └── pie-chart.vue
│   │   └── common/
│   ├── router/
│   │   └── index.ts
│   ├── stores/
│   │   ├── auth.ts
│   │   └── app.ts
│   ├── views/
│   │   ├── login/
│   │   ├── dashboard/
│   │   │   ├── global/
│   │   │   ├── project/
│   │   │   └── personal/
│   │   └── config/
│   │       ├── projects/
│   │       └── users/
│   └── utils/
│       └── request.ts
└── package.json
```

---

## 四、开发顺序建议

### 迭代一：基础框架 (Week 1)
1. 数据库初始化
2. 后端基础架构
3. 前端基础架构
4. 用户认证

### 迭代二：配置管理 (Week 2)
5. 项目基础信息管理
6. 数据源配置
7. 人员账号配置
8. 权限控制

### 迭代三：数据同步 (Week 3)
9. 同步相关表
10. GitLab 同步
11. Trae 同步
12. 禅道同步
13. 定时任务

### 迭代四：统计功能 (Week 4-5)
14. 全局统计模块
15. 项目统计模块
16. 个人统计模块

---

## 五、验收标准汇总

### 功能验收
- [ ] 所有 25 个功能开发完成
- [ ] 接口测试通过
- [ ] 前端页面可正常访问

### 性能验收
- [ ] 页面加载 < 2s
- [ ] API 响应 < 500ms (缓存命中)
- [ ] 数据库查询优化

### 安全验收
- [ ] 密码加密存储
- [ ] JWT Token 安全
- [ ] 权限控制完整
- [ ] SQL 注入防护

### 代码质量
- [ ] 单元测试覆盖率 > 80%
- [ ] ruff 检查通过
- [ ] mypy 类型检查通过
- [ ] 代码注释完整
