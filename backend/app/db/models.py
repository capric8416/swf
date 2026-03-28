"""Database models for Coding Agent Stats Platform.

TDD Green Phase: Implement models to make tests pass.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """User model for system authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    department = Column(String(50), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    role = relationship("Role", back_populates="users")
    project_memberships = relationship("ProjectMember", back_populates="user")
    platform_accounts = relationship("UserPlatformAccount", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class Role(Base):
    """Role model for permission management."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True)
    permissions = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class Project(Base):
    """Project model for project management."""

    __tablename__ = "projects"

    # Project stage enum values
    STAGE_ENUM = ["调研", "立项", "需求", "设计", "研发", "验收", "发布", "运维"]
    STATUS_ENUM = ["active", "archived", "cancelled"]

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    stage = Column(String(20), nullable=False, default="研发")
    status = Column(String(20), nullable=False, default="active")
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("ProjectMember", back_populates="project")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, code={self.code}, name={self.name})>"


class ProjectMember(Base):
    """Project membership model linking users to projects."""

    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    role = Column(String(50), nullable=False, default="developer")
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="project_memberships")
    project = relationship("Project", back_populates="members")

    # Indexes
    __table_args__ = (
        Index("idx_project_member_user_project", "user_id", "project_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ProjectMember(id={self.id}, user_id={self.user_id}, project_id={self.project_id})>"


class UserPlatformAccount(Base):
    """User platform account mapping for external systems."""

    __tablename__ = "user_platform_accounts"

    # Platform enum values
    PLATFORM_ENUM = ["trae", "gitlab", "zendao"]

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    account = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="platform_accounts")

    # Indexes
    __table_args__ = (
        Index("idx_platform_account_user_platform", "user_id", "platform", unique=True),
    )

    def __repr__(self) -> str:
        return f"<UserPlatformAccount(id={self.id}, platform={self.platform}, account={self.account})>"
