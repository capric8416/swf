## 项目概述

这是一个基于 Vue 3 + FastAPI 的全栈应用。
## 项目结构

```
my-project/
├── database/                 # 需求、设计和原型
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── api/             # API 接口定义
│   │   ├── components/      # 公共组件
│   │   ├── composables/     # 组合式函数
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── styles/          # 全局样式
│   │   ├── types/           # TypeScript 类型
│   │   ├── utils/           # 工具函数
│   │   └── views/           # 页面视图
│   ├── package.json
│   └── vite.config.ts
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # 核心配置
│   │   ├── db/              # 数据库模型和连接
│   │   ├── models/          # Pydantic 模型
│   │   ├── schemas/         # 数据验证模式
│   │   ├── services/        # 业务逻辑
│   │   └── utils/           # 工具函数
│   ├── migrations/          # 数据库迁移
│   ├── tests/               # 测试文件
│   ├── pyproject.toml
│   └── main.py
├── docker-compose.yml        # 本地开发环境
└── CLAUDE.md                 # Claude Code 项目配置
```

## 技术栈规范

### 前端 (frontend/)
- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript (严格模式)
- **UI库**: Element Plus
- **图表**: ECharts 5
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **构建工具**: Vite 5
- **HTTP客户端**: Axios

### 后端 (backend/)
- **框架**: FastAPI
- **语言**: Python 3.11+
- **ORM**: SQLAlchemy 2.0 (异步)
- **迁移**: Alembic
- **缓存**: Redis (aioredis)
- **验证**: Pydantic v2
- **测试**: pytest + pytest-asyncio
- **代码质量**: ruff, mypy

### 数据库
- **主库**: PostgreSQL 15
- **缓存**: Redis 7

## 代码规范

### 前端规范
1. **组件命名**: PascalCase (如 `UserProfile.vue`)
2. **组合式函数**: use 前缀 (如 `useAuth.ts`)
3. **类型定义**: 接口用 I 前缀 (如 `IUser`)
4. **API 函数**: 模块组织，统一错误处理
5. **样式**: 使用 Element Plus 变量，避免硬编码

### 后端规范
1. **路由**: 按资源分组，版本控制 (`/api/v1/...`)
2. **依赖注入**: 使用 FastAPI Depends
3. **数据库**: 异步会话管理
4. **错误处理**: 统一异常处理器
5. **日志**: 结构化日志输出

## 常用命令

### 前端
```bash
cd frontend
npm install
npm run dev      # 开发服务器
npm run build    # 生产构建
npm run lint     # ESLint 检查
npm run type-check  # TypeScript 检查
```

### 后端
```bash
cd backend
pip install -e ".[dev]"
python main.py           # 启动开发服务器
pytest                   # 运行测试
alembic revision --autogenerate -m "描述"  # 创建迁移
alembic upgrade head     # 执行迁移
ruff check .             # 代码检查
mypy app                 # 类型检查
```

### Docker
```bash
docker-compose up -d     # 启动数据库服务
docker-compose down      # 停止服务
```

### 数据库
- **主库**: PostgreSQL 路径“D:\Program Files\PostgreSQL”
- **缓存**: Redis 7
## 开发流程

1. 启动本地数据库: `docker-compose up -d`
2. 后端开发: `cd backend && python main.py`
3. 前端开发: `cd frontend && npm run dev`
4. 数据库变更: 修改模型 → 生成迁移 → 执行迁移
5. API 开发: 先定义 schema → 实现路由 → 前端对接

## 注意事项

- 所有 API 调用需处理 loading 和错误状态
- 使用环境变量管理配置，不提交敏感信息
- 数据库查询使用异步 ORM
- Redis 用于缓存和会话存储
```