# S5-S19 部署架构设计

---

## 元信息

| 属性 | 内容 |
|------|------|
| **Skill 编号** | S5-S19 |
| **Skill 名称** | 部署架构设计 |
| **所属阶段** | S5 - 架构设计阶段 |
| **前置 Skill** | S5-S18 接口架构设计 |
| **后置 Skill** | 无（S5 阶段结束） |
| **执行模式** | 标准模式 |
| **人工评审点** | 部署方案评审（步骤 7） |

---

## 触发条件

当满足以下任一条件时，触发本 Skill：

1. 接口架构设计已完成，需要设计部署方案
2. 需要定义运行环境和基础设施
3. 需要设计 CI/CD 流程
4. 需要输出可指导运维的部署文档

---

## 输入

| 输入项 | 说明 | 来源 |
|--------|------|------|
| 系统架构设计 | 分层架构、技术栈 | S5-S16 产物 |
| 数据架构设计 | 数据库、缓存设计 | S5-S17 产物 |
| 接口架构设计 | API 设计、外部集成 | S5-S18 产物 |
| 非功能需求 | 性能、安全、可用性 | 需求报告 |
| 部署约束 | 内部服务器部署 | 需求报告 |

---

## 输出

| 产物 | 说明 | 存储路径 |
|------|------|----------|
| 部署架构设计文档 | 部署方案、环境配置 | `database/stages/s5/{PlanID}/{PlanID}-S5-S19-001.md` |
| Docker Compose 配置 | 容器编排文件 | 嵌入架构文档 |
| CI/CD 流程设计 | 自动化构建部署 | 嵌入架构文档 |
| 监控告警方案 | 运维监控设计 | 嵌入架构文档 |

---

## 执行流程

### 步骤 1：读取前置产物

读取以下文件获取设计输入：
- 系统架构设计：`database/stages/s5/{PlanID}/{PlanID}-S5-S16-001.md`
- 数据架构设计：`database/stages/s5/{PlanID}/{PlanID}-S5-S17-001.md`
- 接口架构设计：`database/stages/s5/{PlanID}/{PlanID}-S5-S18-001.md`
- 需求报告：`database/plans/{PlanID}-requirements-report.md`

### 步骤 2：设计部署架构

**2.1 部署模式选择**

基于需求选择 Docker Compose 单机部署模式：

| 部署模式 | 适用场景 | 选择理由 |
|----------|----------|----------|
| Docker Compose | 中小型应用、内部部署 | 运维简单、资源占用低、符合需求 |
| Kubernetes | 大型应用、高可用要求 | 过于复杂，当前不需要 |
| 裸机部署 | 传统应用 | 不利于维护和扩展 |

**2.2 部署架构图**

```mermaid
flowchart TB
    subgraph 外部访问
        A[用户浏览器]
    end
    
    subgraph 应用服务器
        B[Nginx<br/>反向代理]
        C[Frontend<br/>Vue3 前端]
        D[Backend<br/>FastAPI 后端]
        E[Celery<br/>任务队列]
        F[Celery Beat<br/>定时任务]
    end
    
    subgraph 数据层
        G[(PostgreSQL<br/>主数据库)]
        H[(Redis<br/>缓存/队列)]
    end
    
    subgraph 外部服务
        I[GitLab API]
        J[禅道 API]
        K[Agent 平台 API]
    end
    
    A -->|HTTPS| B
    B -->|/| C
    B -->|/api| D
    D -->|任务发布| H
    E -->|任务消费| H
    F -->|定时触发| E
    D -->|读写| G
    D -->|缓存| H
    E -->|读写| G
    D -->|REST API| I
    D -->|REST API| J
    E -->|REST API| K
```

### 步骤 3：设计服务划分

**3.1 容器服务清单**

| 服务名 | 镜像 | 端口 | 资源限制 | 说明 |
|--------|------|------|----------|------|
| nginx | nginx:alpine | 80, 443 | 0.5核/512MB | 反向代理、静态资源 |
| frontend | coding-stats-web:latest | 80 | 0.5核/512MB | Vue3 前端应用 |
| backend | coding-stats-api:latest | 8000 | 1核/1GB | FastAPI 后端服务 |
| celery-worker | coding-stats-api:latest | - | 0.5核/512MB | 异步任务处理 |
| celery-beat | coding-stats-api:latest | - | 0.25核/256MB | 定时任务调度 |
| postgres | postgres:15-alpine | 5432 | 1核/2GB | PostgreSQL 数据库 |
| redis | redis:7-alpine | 6379 | 0.5核/512MB | Redis 缓存和队列 |

**3.2 服务依赖关系**

```mermaid
flowchart LR
    A[nginx] --> B[frontend]
    A --> C[backend]
    C --> D[postgres]
    C --> E[redis]
    F[celery-worker] --> D
    F --> E
    G[celery-beat] --> E
```

### 步骤 4：设计环境配置

**4.1 环境变量配置**

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接串 | postgresql://user:pass@postgres:5432/coding_stats |
| `REDIS_URL` | Redis 连接串 | redis://redis:6379/0 |
| `SECRET_KEY` | JWT 密钥 | random-secret-key |
| `GITLAB_TOKEN` | GitLab API Token | glpat-xxx |
| `ZENDAO_TOKEN` | 禅道 API Token | zentao-token |
| `AGENT_API_KEY` | Agent 平台 API Key | agent-api-key |
| `LOG_LEVEL` | 日志级别 | INFO |
| `ENV` | 运行环境 | production |

**4.2 配置文件映射**

| 配置文件 | 容器路径 | 说明 |
|----------|----------|------|
| nginx.conf | /etc/nginx/nginx.conf | Nginx 主配置 |
| default.conf | /etc/nginx/conf.d/default.conf | 站点配置 |
| gunicorn.conf.py | /app/gunicorn.conf.py | Gunicorn 配置 |

### 步骤 5：设计 CI/CD 流程

**5.1 CI/CD 流程图**

```mermaid
flowchart LR
    A[代码提交] --> B[GitLab CI]
    B --> C[代码检查]
    C --> D[单元测试]
    D --> E[构建镜像]
    E --> F[推送镜像]
    F --> G[部署测试环境]
    G --> H[集成测试]
    H -->|通过| I[部署生产环境]
    H -->|失败| J[通知开发者]
```

**5.2 CI/CD 阶段定义**

| 阶段 | 任务 | 说明 |
|------|------|------|
| lint | 代码检查 | flake8, black, eslint |
| test | 单元测试 | pytest, jest |
| build | 构建镜像 | docker build |
| push | 推送镜像 | docker push |
| deploy-staging | 部署测试环境 | docker-compose up |
| integration-test | 集成测试 | API 测试 |
| deploy-prod | 部署生产环境 | docker-compose up |

**5.3 GitLab CI 配置示例**

```yaml
stages:
  - lint
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: registry.company.com/coding-stats

lint-backend:
  stage: lint
  script:
    - flake8 backend/
    - black --check backend/

test-backend:
  stage: test
  script:
    - pytest backend/tests/ -v --cov

build-image:
  stage: build
  script:
    - docker build -t $DOCKER_IMAGE/api:$CI_COMMIT_SHA -f backend/Dockerfile .
    - docker push $DOCKER_IMAGE/api:$CI_COMMIT_SHA

deploy-prod:
  stage: deploy
  script:
    - ssh deploy@prod-server "cd /opt/coding-stats && docker-compose pull && docker-compose up -d"
  only:
    - main
```

### 步骤 6：设计监控告警方案

**6.1 监控指标**

| 层级 | 指标 | 采集方式 |
|------|------|----------|
| 基础设施 | CPU、内存、磁盘、网络 | Node Exporter |
| 容器 | 容器状态、资源使用 | cAdvisor |
| 应用 | QPS、响应时间、错误率 | Prometheus + FastAPI Instrument |
| 业务 | 数据采集成功率、统计任务耗时 | 应用日志 |
| 数据库 | 连接数、慢查询、锁等待 | PostgreSQL Exporter |

**6.2 告警规则**

| 告警项 | 阈值 | 级别 | 通知方式 |
|--------|------|------|----------|
| 服务不可用 | 连续 2 次检测失败 | P0 | 短信+邮件+钉钉 |
| CPU 使用率 | > 80% 持续 5 分钟 | P1 | 邮件+钉钉 |
| 内存使用率 | > 85% 持续 5 分钟 | P1 | 邮件+钉钉 |
| 磁盘使用率 | > 85% | P1 | 邮件+钉钉 |
| API 错误率 | > 5% 持续 5 分钟 | P1 | 邮件+钉钉 |
| API 响应时间 | P99 > 2s 持续 5 分钟 | P2 | 钉钉 |
| 数据同步失败 | 连续 2 次失败 | P1 | 邮件+钉钉 |

**6.3 监控架构**

```mermaid
flowchart LR
    A[应用/容器] -->|指标| B[Prometheus]
    C[Node Exporter] -->|系统指标| B
    D[PostgreSQL Exporter] -->|DB指标| B
    B --> E[Grafana]
    B -->|告警| F[AlertManager]
    F -->|通知| G[钉钉/邮件]
```

### 步骤 7：用户评审

生成部署架构设计初稿后，进入用户评审：

**评审内容**：
1. 部署架构是否满足内部部署需求
2. 资源分配是否合理
3. CI/CD 流程是否符合团队习惯
4. 监控告警是否全面
5. 运维成本是否可接受

**评审选项**：
- **确认** → 进入步骤 8
- **修改：{具体意见}** → 返回步骤 3-6 调整
- **补充：{新增需求}** → 补充分析后重新评审

### 步骤 8：生成产物

评审通过后，生成以下产物：

1. **部署架构设计文档**（Markdown 格式）
2. **更新 Todo-List**：标记 S5-S19 为已完成，S5 阶段结束

---

## 产物模板

### 部署架构设计文档结构

```markdown
# {PlanID}-S5-S19-001 部署架构设计文档

## 1. 部署架构概述
- 部署模式
- 架构图
- 技术选型

## 2. 服务设计
- 服务清单
- 依赖关系
- 资源分配

## 3. 环境配置
- 环境变量
- 配置文件
- 密钥管理

## 4. Docker Compose 配置
- 服务定义
- 网络配置
- 存储配置

## 5. CI/CD 设计
- 流程图
- 阶段定义
- 配置示例

## 6. 监控告警
- 监控指标
- 告警规则
- 监控架构

## 7. 运维手册
- 部署步骤
- 扩容方案
- 备份恢复
- 故障处理
```

---

## 错误处理策略

| 错误场景 | 处理策略 |
|----------|----------|
| 资源不足 | 提供最小资源配置方案，支持渐进式扩容 |
| 网络隔离 | 设计离线部署方案，使用私有镜像仓库 |
| 数据丢失 | 设计自动备份策略，支持时间点恢复 |
| 服务故障 | 设计健康检查和自动重启机制 |

---

## 注意事项

1. 所有敏感信息（密码、Token）通过环境变量注入，不硬编码
2. 数据库数据使用 Docker Volume 持久化，定期备份
3. 日志统一输出到 stdout，便于集中收集
4. 生产环境使用 HTTPS，配置 SSL 证书
5. 预留 30% 的资源余量应对峰值
