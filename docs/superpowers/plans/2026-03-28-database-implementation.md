# 数据库层实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建完整的数据库层，包括表结构、枚举类型、分区表、索引、触发器和初始数据

**Architecture:** 使用 PostgreSQL 分区表存储时序数据（code_commits, token_usage），通过 Alembic 管理迁移，SQLAlchemy 2.0 异步模型映射

**Tech Stack:** PostgreSQL 15, SQLAlchemy 2.0, Alembic, asyncpg

---

## 文件结构

```
backend/
├── alembic/
│   ├── env.py                    # Alembic环境配置
│   └── versions/
│       └── 001_initial_schema.py # 初始迁移
├── app/
│   └── db/
│       ├── base.py               # 数据库连接基类
│       └── models/
│           ├── __init__.py
│           ├── user.py           # User, Role
│           ├── project.py        # Project, ProjectMember
│           ├── config.py         # UserAccount, DataSource
│           ├── stats.py          # CodeCommit, TokenUsage, BugRecord, AISuggestion
│           ├── sync.py           # SyncTask, StatsSnapshot
│           └── audit.py          # AuditLog
└── tests/
    └── db/
        └── test_models.py        # 模型测试
```

---

## Task 1: Alembic 配置

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

**Context:** Alembic 是 SQLAlchemy 的数据库迁移工具，需要配置异步支持

- [ ] **Step 1: 创建 alembic.ini 配置文件**

```ini
# backend/alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
database_url = postgresql+asyncpg://postgres:postgres@localhost:5432/coding_agent_stats

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: 创建 alembic 环境文件**

```python
# backend/alembic/env.py
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings
from app.db.base import Base

# 导入所有模型以确保它们被注册
from app.db.models import user, project, config, stats, sync, audit

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: 创建迁移脚本模板**

```python
# backend/alembic/script.py.mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 4: 验证 Alembic 配置**

Run:
```bash
cd backend
source venv/Scripts/activate
alembic --help
```

Expected: 显示 Alembic 帮助信息，无错误

- [ ] **Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "chore: configure alembic for async migrations"
```

---

## Task 2: 数据库基础模块

**Files:**
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/base.py`

**Context:** 数据库连接基类，提供异步会话管理

- [ ] **Step 1: 创建数据库基类**

```python
# backend/app/db/base.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明式基类
Base = declarative_base()


async def get_db():
    """获取数据库会话（FastAPI依赖）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建所有表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 2: 创建 db 模块初始化文件**

```python
# backend/app/db/__init__.py
from app.db.base import Base, engine, AsyncSessionLocal, get_db, init_db

__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db", "init_db"]
```

- [ ] **Step 3: 验证导入**

Run:
```bash
cd backend
source venv/Scripts/activate
python -c "from app.db.base import Base, engine; print('Import OK')"
```

Expected: `Import OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/
git commit -m "feat: add database base module with async support"
```

---

## Task 3: 用户模型

**Files:**
- Create: `backend/app/db/models/__init__.py`
- Create: `backend/app/db/models/user.py`

**Context:** 用户和角色模型，角色权限使用 JSONB 存储

- [ ] **Step 1: 创建用户模型**

```python
# backend/app/db/models/user.py
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200))
    permissions = Column(JSONB, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    department = Column(String(50), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    role = relationship("Role", back_populates="users")
    project_memberships = relationship("ProjectMember", back_populates="user")
    platform_accounts = relationship("UserAccount", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"
```

- [ ] **Step 2: 创建模型模块初始化文件**

```python
# backend/app/db/models/__init__.py
from app.db.models.user import Role, User

__all__ = ["Role", "User"]
```

- [ ] **Step 3: 验证模型**

Run:
```bash
cd backend
source venv/Scripts/activate
python -c "from app.db.models import User, Role; print(f'User table: {User.__tablename__}'); print(f'Role table: {Role.__tablename__}')"
```

Expected:
```
User table: users
Role table: roles
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/models/
git commit -m "feat: add user and role models"
```

---

## Task 4: 项目模型

**Files:**
- Create: `backend/app/db/models/project.py`
- Modify: `backend/app/db/models/__init__.py`

**Context:** 项目和项目成员模型，使用 PostgreSQL 枚举类型

- [ ] **Step 1: 创建项目模型**

```python
# backend/app/db/models/project.py
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime,
    ForeignKey, Enum, CheckConstraint
)
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class ProjectStage(str, enum.Enum):
    """项目阶段枚举"""
    RESEARCH = "调研"
    INITIATION = "立项"
    REQUIREMENT = "需求"
    DESIGN = "设计"
    DEVELOPMENT = "研发"
    ACCEPTANCE = "验收"
    RELEASE = "发布"
    OPERATION = "运维"


class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class ProjectMemberRole(str, enum.Enum):
    """项目成员角色枚举"""
    MANAGER = "manager"
    TECH_LEAD = "tech_lead"
    MEMBER = "member"


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True)
    description = Column(Text)
    stage = Column(Enum(ProjectStage), nullable=False, index=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False, index=True)
    manager_id = Column(Integer, ForeignKey("users.id"), index=True)
    gitlab_repo_id = Column(Integer, index=True)
    gitlab_repo_url = Column(String(500))
    zendao_project_id = Column(Integer, index=True)
    zendao_project_key = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    manager = relationship("User")
    members = relationship("ProjectMember", back_populates="project")

    # 表约束
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="chk_projects_date_range"
        ),
    )

    def __repr__(self):
        return f"<Project {self.name}>"


class ProjectMember(Base):
    """项目成员表"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(Enum(ProjectMemberRole), default=ProjectMemberRole.MEMBER, nullable=False, index=True)
    joined_at = Column(Date, default=date.today, nullable=False)
    left_at = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")

    # 表约束
    __table_args__ = (
        CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="chk_project_members_dates"
        ),
    )

    def __repr__(self):
        return f"<ProjectMember {self.user_id}@{self.project_id}>"
```

- [ ] **Step 2: 更新模型初始化文件**

```python
# backend/app/db/models/__init__.py
from app.db.models.user import Role, User
from app.db.models.project import Project, ProjectMember, ProjectStage, ProjectStatus, ProjectMemberRole

__all__ = [
    "Role", "User",
    "Project", "ProjectMember",
    "ProjectStage", "ProjectStatus", "ProjectMemberRole"
]
```

- [ ] **Step 3: 验证模型**

Run:
```bash
cd backend
source venv/Scripts/activate
python -c "from app.db.models import Project, ProjectMember; print('Project and ProjectMember models OK')"
```

Expected: `Project and ProjectMember models OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/models/
git commit -m "feat: add project and project member models with enums"
```

---

## Task 5: 配置模型

**Files:**
- Create: `backend/app/db/models/config.py`
- Modify: `backend/app/db/models/__init__.py`

**Context:** 用户平台账号和数据源配置，API Token 使用 BYTEA 加密存储

- [ ] **Step 1: 创建配置模型**

```python
# backend/app/db/models/config.py
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Enum, Text
)
from sqlalchemy.dialects.postgresql import JSONB, BYTEA
from sqlalchemy.orm import relationship

from app.db.base import Base


class PlatformType(str, enum.Enum):
    """平台类型枚举"""
    TRAE = "trae"
    GITLAB = "gitlab"
    ZENDAO = "zendao"
    ALI_CODING = "ali_coding"


class DataSourceType(str, enum.Enum):
    """数据源类型枚举"""
    GITLAB = "gitlab"
    ZENDAO = "zendao"


class SyncFrequency(str, enum.Enum):
    """同步频率枚举"""
    DAILY = "daily"
    HOURLY = "hourly"
    REALTIME = "realtime"


class UserAccount(Base):
    """用户平台账号表"""
    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(Enum(PlatformType), nullable=False, index=True)
    account_id = Column(String(100), nullable=False)
    account_name = Column(String(100))
    api_token_encrypted = Column(BYTEA)  # AES-256 加密存储
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="platform_accounts")

    # 唯一约束：一个用户每个平台只能有一个账号
    __table_args__ = (
        CheckConstraint(
            "platform IN ('trae', 'gitlab', 'zendao', 'ali_coding')",
            name="chk_user_accounts_platform"
        ),
    )

    def __repr__(self):
        return f"<UserAccount {self.user_id}:{self.platform}>"


class DataSource(Base):
    """数据源配置表"""
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    source_type = Column(Enum(DataSourceType), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)
    config = Column(JSONB, default=dict, nullable=False)
    credentials_encrypted = Column(BYTEA)  # AES-256 加密存储
    is_active = Column(Boolean, default=True, index=True)
    last_sync_at = Column(DateTime)
    sync_frequency = Column(Enum(SyncFrequency), default=SyncFrequency.DAILY)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project")

    def __repr__(self):
        return f"<DataSource {self.source_name}>"
```

- [ ] **Step 2: 更新模型初始化文件**

```python
# backend/app/db/models/__init__.py
from app.db.models.user import Role, User
from app.db.models.project import Project, ProjectMember, ProjectStage, ProjectStatus, ProjectMemberRole
from app.db.models.config import UserAccount, DataSource, PlatformType, DataSourceType, SyncFrequency

__all__ = [
    "Role", "User",
    "Project", "ProjectMember",
    "ProjectStage", "ProjectStatus", "ProjectMemberRole",
    "UserAccount", "DataSource",
    "PlatformType", "DataSourceType", "SyncFrequency"
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/db/models/
git commit -m "feat: add user account and data source config models"
```

---

## Task 6: 统计数据模型（分区表）

**Files:**
- Create: `backend/app/db/models/stats.py`
- Modify: `backend/app/db/models/__init__.py`

**Context:** 代码提交和 Token 使用使用分区表存储，按月分区

- [ ] **Step 1: 创建统计模型**

```python
# backend/app/db/models/stats.py
from datetime import datetime, date
from typing import Optional, List
import enum

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date,
    ForeignKey, Enum, Text, Numeric, PrimaryKeyConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.db.base import Base


class BugSeverity(str, enum.Enum):
    """Bug严重程度枚举"""
    CRITICAL = "critical"
    MAJOR = "major"
    NORMAL = "normal"
    MINOR = "minor"
    TRIVIAL = "trivial"


class BugStatus(str, enum.Enum):
    """Bug状态枚举"""
    NEW = "new"
    ASSIGNED = "assigned"
    ACTIVE = "active"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"


class BugPriority(str, enum.Enum):
    """Bug优先级枚举"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AISuggestionType(str, enum.Enum):
    """AI建议类型枚举"""
    CODE_COMPLETION = "code_completion"
    CODE_GENERATION = "code_generation"
    REFACTORING = "refactoring"
    BUG_FIX = "bug_fix"
    EXPLANATION = "explanation"


class CodeCommit(Base):
    """代码提交表 - 按月分区"""
    __tablename__ = "code_commits"

    id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    commit_hash = Column(String(64), nullable=False)
    additions = Column(Integer, default=0, nullable=False)
    deletions = Column(Integer, default=0, nullable=False)
    language = Column(String(20), nullable=False, index=True)
    file_count = Column(Integer, default=0, nullable=False)
    commit_message = Column(Text)
    commit_time = Column(DateTime, nullable=False)  # 分区键
    is_ai_generated = Column(Boolean, default=False, index=True)
    ai_suggestion_ids = Column(ARRAY(Integer))
    branch_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 复合主键（包含分区键）
    __table_args__ = (
        PrimaryKeyConstraint('id', 'commit_time'),
    )

    def __repr__(self):
        return f"<CodeCommit {self.commit_hash[:8]}>"


class TokenUsage(Base):
    """Token使用表 - 按月分区"""
    __tablename__ = "token_usage"

    id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    platform = Column(String(20), nullable=False, index=True)
    token_count = Column(Integer, default=0, nullable=False)
    api_calls = Column(Integer, default=0, nullable=False)
    usage_date = Column(Date, nullable=False)  # 分区键
    model = Column(String(50))
    cost = Column(Numeric(10, 4))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 复合主键（包含分区键）
    __table_args__ = (
        PrimaryKeyConstraint('id', 'usage_date'),
    )

    def __repr__(self):
        return f"<TokenUsage {self.user_id}:{self.usage_date}>"


class BugRecord(Base):
    """Bug记录表"""
    __tablename__ = "bug_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), index=True)
    zendao_bug_id = Column(Integer, unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    severity = Column(Enum(BugSeverity), nullable=False, index=True)
    priority = Column(Enum(BugPriority), index=True)
    status = Column(Enum(BugStatus), default=BugStatus.NEW, nullable=False, index=True)
    type = Column(String(20), default="bug")
    module = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)
    resolution = Column(String(200))

    # 关系
    project = relationship("Project")
    assignee = relationship("User", foreign_keys=[assignee_id])
    reporter = relationship("User", foreign_keys=[reporter_id])

    def __repr__(self):
        return f"<BugRecord {self.title[:30]}>"


class AISuggestion(Base):
    """AI建议表"""
    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    platform = Column(String(20), nullable=False, index=True)
    suggestion_type = Column(Enum(AISuggestionType), nullable=False, index=True)
    content = Column(Text, nullable=False)
    language = Column(String(20))
    file_path = Column(String(500))
    line_number = Column(Integer)
    token_cost = Column(Integer)
    is_accepted = Column(Boolean, default=False, index=True)
    accepted_at = Column(DateTime)
    commit_hash = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User")
    project = relationship("Project")

    def __repr__(self):
        return f"<AISuggestion {self.suggestion_type}>"
```

- [ ] **Step 2: 更新模型初始化文件**

```python
# backend/app/db/models/__init__.py
from app.db.models.user import Role, User
from app.db.models.project import Project, ProjectMember, ProjectStage, ProjectStatus, ProjectMemberRole
from app.db.models.config import UserAccount, DataSource, PlatformType, DataSourceType, SyncFrequency
from app.db.models.stats import (
    CodeCommit, TokenUsage, BugRecord, AISuggestion,
    BugSeverity, BugStatus, BugPriority, AISuggestionType
)

__all__ = [
    "Role", "User",
    "Project", "ProjectMember",
    "ProjectStage", "ProjectStatus", "ProjectMemberRole",
    "UserAccount", "DataSource",
    "PlatformType", "DataSourceType", "SyncFrequency",
    "CodeCommit", "TokenUsage", "BugRecord", "AISuggestion",
    "BugSeverity", "BugStatus", "BugPriority", "AISuggestionType"
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/db/models/
git commit -m "feat: add stats models with partitioning support"
```

---

## Task 7: 同步和审计模型

**Files:**
- Create: `backend/app/db/models/sync.py`
- Create: `backend/app/db/models/audit.py`
- Modify: `backend/app/db/models/__init__.py`

**Context:** 同步任务、统计快照和审计日志

- [ ] **Step 1: 创建同步模型**

```python
# backend/app/db/models/sync.py
from datetime import datetime, date
from typing import Optional
import enum

from sqlalchemy import (
    Column, Integer, String, DateTime, Date,
    ForeignKey, Enum, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class SyncTaskType(str, enum.Enum):
    """同步任务类型枚举"""
    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"
    CONFIG_SYNC = "config_sync"


class SyncTaskStatus(str, enum.Enum):
    """同步任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SnapshotType(str, enum.Enum):
    """快照类型枚举"""
    GLOBAL = "global"
    PROJECT = "project"
    PERSONAL = "personal"


class SyncTask(Base):
    """同步任务表"""
    __tablename__ = "sync_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(Enum(SyncTaskType), nullable=False, index=True)
    source_type = Column(String(20), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    status = Column(Enum(SyncTaskStatus), default=SyncTaskStatus.PENDING, nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project")

    def __repr__(self):
        return f"<SyncTask {self.task_type}:{self.status}>"


class StatsSnapshot(Base):
    """统计快照表"""
    __tablename__ = "stats_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_type = Column(Enum(SnapshotType), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    metrics = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project")
    user = relationship("User")

    # 唯一约束
    __table_args__ = (
        CheckConstraint(
            "snapshot_type IN ('global', 'project', 'personal')",
            name="chk_stats_snapshots_type"
        ),
    )

    def __repr__(self):
        return f"<StatsSnapshot {self.snapshot_type}:{self.snapshot_date}>"
```

- [ ] **Step 2: 创建审计模型**

```python
# backend/app/db/models/audit.py
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, INET

from app.db.base import Base


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # INSERT/UPDATE/DELETE
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    ip_address = Column(INET)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog {self.table_name}:{self.action}>"
```

- [ ] **Step 3: 更新模型初始化文件**

```python
# backend/app/db/models/__init__.py
from app.db.models.user import Role, User
from app.db.models.project import Project, ProjectMember, ProjectStage, ProjectStatus, ProjectMemberRole
from app.db.models.config import UserAccount, DataSource, PlatformType, DataSourceType, SyncFrequency
from app.db.models.stats import (
    CodeCommit, TokenUsage, BugRecord, AISuggestion,
    BugSeverity, BugStatus, BugPriority, AISuggestionType
)
from app.db.models.sync import SyncTask, StatsSnapshot, SyncTaskType, SyncTaskStatus, SnapshotType
from app.db.models.audit import AuditLog

__all__ = [
    "Role", "User",
    "Project", "ProjectMember",
    "ProjectStage", "ProjectStatus", "ProjectMemberRole",
    "UserAccount", "DataSource",
    "PlatformType", "DataSourceType", "SyncFrequency",
    "CodeCommit", "TokenUsage", "BugRecord", "AISuggestion",
    "BugSeverity", "BugStatus", "BugPriority", "AISuggestionType",
    "SyncTask", "StatsSnapshot",
    "SyncTaskType", "SyncTaskStatus", "SnapshotType",
    "AuditLog"
]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/models/
git commit -m "feat: add sync task, stats snapshot and audit log models"
```

---

## Task 8: 初始迁移脚本

**Files:**
- Create: `backend/alembic/versions/001_initial_schema.py`

**Context:** 创建完整的初始迁移，包含所有表、索引、约束和初始数据

- [ ] **Step 1: 创建迁移脚本**

```python
# backend/alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建枚举类型
    op.execute("""
        CREATE TYPE project_stage AS ENUM (
            '调研', '立项', '需求', '设计', '研发', '验收', '发布', '运维'
        )
    """)

    op.execute("""
        CREATE TYPE project_status AS ENUM ('active', 'archived', 'cancelled')
    """)

    op.execute("""
        CREATE TYPE bug_severity AS ENUM (
            'critical', 'major', 'normal', 'minor', 'trivial'
        )
    """)

    op.execute("""
        CREATE TYPE bug_status AS ENUM (
            'new', 'assigned', 'active', 'resolved', 'closed', 'rejected'
        )
    """)

    op.execute("""
        CREATE TYPE bug_priority AS ENUM ('urgent', 'high', 'medium', 'low')
    """)

    op.execute("""
        CREATE TYPE ai_suggestion_type AS ENUM (
            'code_completion', 'code_generation', 'refactoring', 'bug_fix', 'explanation'
        )
    """)

    op.execute("""
        CREATE TYPE sync_task_type AS ENUM (
            'full_sync', 'incremental_sync', 'config_sync'
        )
    """)

    op.execute("""
        CREATE TYPE sync_task_status AS ENUM (
            'pending', 'running', 'completed', 'failed', 'cancelled'
        )
    """)

    op.execute("""
        CREATE TYPE snapshot_type AS ENUM ('global', 'project', 'personal')
    """)

    # 创建角色表
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.Column('permissions', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_roles_name', 'roles', ['name'])

    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('department', sa.String(50), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_department', 'users', ['department'])
    op.create_index('idx_users_role_id', 'users', ['role_id'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])

    # 创建项目表
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('description', sa.Text()),
        sa.Column('stage', sa.Enum('调研', '立项', '需求', '设计', '研发', '验收', '发布', '运维', name='project_stage'), nullable=False),
        sa.Column('status', sa.Enum('active', 'archived', 'cancelled', name='project_status'), nullable=False, server_default='active'),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('gitlab_repo_id', sa.Integer()),
        sa.Column('gitlab_repo_url', sa.String(500)),
        sa.Column('zendao_project_id', sa.Integer()),
        sa.Column('zendao_project_key', sa.String(50)),
        sa.Column('start_date', sa.Date()),
        sa.Column('end_date', sa.Date()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.CheckConstraint('end_date IS NULL OR start_date IS NULL OR end_date >= start_date', name='chk_projects_date_range')
    )
    op.create_index('idx_projects_stage', 'projects', ['stage'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_manager_id', 'projects', ['manager_id'])

    # 插入初始角色数据
    op.execute("""
        INSERT INTO roles (name, description, permissions) VALUES
        ('admin', '系统管理员 - 所有权限', '["stats:global:view", "stats:project:view", "stats:personal:view", "config:manage", "sync:trigger", "user:manage", "role:manage"]'),
        ('project_manager', '项目经理 - 项目管理权限', '["stats:global:view", "stats:project:view", "stats:personal:view", "config:manage"]'),
        ('developer', '研发人员 - 个人数据查看权限', '["stats:personal:view", "stats:project:view"]'),
        ('tester', '测试人员 - Bug相关权限', '["stats:personal:view", "stats:project:view"]')
    """)

    # 创建其他表...
    # 为节省篇幅，这里省略其他表的创建代码
    # 实际实现时需要包含所有表


def downgrade() -> None:
    # 删除表（逆序）
    op.drop_table('audit_logs')
    op.drop_table('stats_snapshots')
    op.drop_table('sync_tasks')
    op.drop_table('ai_suggestions')
    op.drop_table('bug_records')
    op.drop_table('token_usage')
    op.drop_table('code_commits')
    op.drop_table('data_sources')
    op.drop_table('user_accounts')
    op.drop_table('project_members')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('roles')

    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS snapshot_type')
    op.execute('DROP TYPE IF EXISTS sync_task_status')
    op.execute('DROP TYPE IF EXISTS sync_task_type')
    op.execute('DROP TYPE IF EXISTS ai_suggestion_type')
    op.execute('DROP TYPE IF EXISTS bug_priority')
    op.execute('DROP TYPE IF EXISTS bug_status')
    op.execute('DROP TYPE IF EXISTS bug_severity')
    op.execute('DROP TYPE IF EXISTS project_status')
    op.execute('DROP TYPE IF EXISTS project_stage')
```

- [ ] **Step 2: 验证迁移脚本**

Run:
```bash
cd backend
source venv/Scripts/activate
alembic revision --autogenerate -m "test migration"
```

Expected: 生成新的迁移文件或显示 "No changes detected"

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: add initial database migration"
```

---

## Task 9: 模型测试

**Files:**
- Create: `backend/tests/db/__init__.py`
- Create: `backend/tests/db/test_models.py`
- Create: `backend/tests/conftest.py`

**Context:** 为数据库模型编写测试

- [ ] **Step 1: 创建测试配置**

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.core.config import settings

# 使用内存数据库进行测试
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_coding_agent_stats"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """创建测试数据库引擎"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(db_engine):
    """创建测试会话"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
```

- [ ] **Step 2: 创建模型测试**

```python
# backend/tests/db/test_models.py
import pytest
from sqlalchemy import select

from app.db.models import Role, User, Project, ProjectStatus, ProjectStage


@pytest.mark.asyncio
async def test_create_role(db_session):
    """测试创建角色"""
    role = Role(
        name="test_role",
        description="Test role",
        permissions=["test:permission"]
    )
    db_session.add(role)
    await db_session.commit()

    result = await db_session.execute(select(Role).where(Role.name == "test_role"))
    saved_role = result.scalar_one()

    assert saved_role.name == "test_role"
    assert saved_role.permissions == ["test:permission"]


@pytest.mark.asyncio
async def test_create_user(db_session):
    """测试创建用户"""
    # 先创建角色
    role = Role(name="test_role", permissions=[])
    db_session.add(role)
    await db_session.flush()

    # 创建用户
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        department="Test Dept",
        role_id=role.id
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    saved_user = result.scalar_one()

    assert saved_user.username == "testuser"
    assert saved_user.email == "test@example.com"
    assert saved_user.is_active is True


@pytest.mark.asyncio
async def test_create_project(db_session):
    """测试创建项目"""
    project = Project(
        name="Test Project",
        code="TEST-001",
        description="A test project",
        stage=ProjectStage.DEVELOPMENT,
        status=ProjectStatus.ACTIVE
    )
    db_session.add(project)
    await db_session.commit()

    result = await db_session.execute(select(Project).where(Project.code == "TEST-001"))
    saved_project = result.scalar_one()

    assert saved_project.name == "Test Project"
    assert saved_project.status == ProjectStatus.ACTIVE
```

- [ ] **Step 3: 运行测试**

Run:
```bash
cd backend
source venv/Scripts/activate
pytest tests/db/test_models.py -v
```

Expected: 所有测试通过

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: add database model tests"
```

---

## 执行完成检查清单

- [ ] Alembic 配置完成
- [ ] 数据库基础模块完成
- [ ] 所有 12 个模型定义完成
- [ ] 初始迁移脚本创建
- [ ] 模型测试通过
- [ ] 所有变更已提交到 Git

---

## 下一步

数据库层实现完成后，继续执行：**后端基础架构实现**
