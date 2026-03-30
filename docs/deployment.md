# Coding Agent 绩效统计平台 - 生产环境部署指南

## 系统要求

### 硬件要求
- **CPU**: 2核+
- **内存**: 4GB+
- **磁盘**: 20GB+
- **网络**: 可访问互联网

### 软件要求
- **操作系统**: Linux (Ubuntu 20.04+ / CentOS 8+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **PostgreSQL**: 15+
- **Redis**: 7+ (可选，用于缓存和token黑名单)

---

## 快速部署

### 1. 环境准备

```bash
# 克隆代码
git clone <repository-url>
cd swf

# 切换到生产分支
git checkout main
```

### 2. 配置环境变量

```bash
# 后端配置
cp backend/.env.example backend/.env

# 编辑 backend/.env
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/coding_stats
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-super-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**重要**:
- 生产环境必须修改 `SECRET_KEY`
- 使用强密码（至少32位随机字符）
- 不要提交 `.env` 文件到版本控制

### 3. 使用 Docker Compose 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 手动部署

### 后端部署

#### 1. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

#### 2. 数据库初始化

```bash
# 创建数据库
createdb coding_stats

# 运行迁移
alembic upgrade head

# 或使用 SQL 脚本
psql -U postgres -d coding_stats -f app/db/sql/001_create_extensions.sql
psql -U postgres -d coding_stats -f app/db/sql/002_create_schema.sql
psql -U postgres -d coding_stats -f app/db/sql/003_create_tables.sql
psql -U postgres -d coding_stats -f app/db/sql/004_create_indexes.sql
psql -U postgres -d coding_stats -f app/db/sql/005_create_functions.sql
psql -U postgres -d coding_stats -f app/db/sql/006_seed_data.sql
```

#### 3. 启动服务

```bash
# 开发模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 前端部署

```bash
cd frontend
npm install
npm run build

# 使用 nginx 托管
cp -r dist/* /var/www/html/
```

---

## 生产环境配置

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 前端静态文件
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### systemd 服务配置

创建 `/etc/systemd/system/coding-stats.service`:

```ini
[Unit]
Description=Coding Agent Stats API
After=network.target

[Service]
Type=simple
User=coding-stats
WorkingDirectory=/opt/coding-stats/backend
Environment=PATH=/opt/coding-stats/backend/venv/bin
EnvironmentFile=/opt/coding-stats/backend/.env
ExecStart=/opt/coding-stats/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable coding-stats
sudo systemctl start coding-stats
sudo systemctl status coding-stats
```

---

## 安全配置

### 1. 修改默认密钥

```bash
# 生成随机密钥
openssl rand -hex 32

# 更新 .env 文件
SECRET_KEY=your-generated-key-here
```

### 2. 配置防火墙

```bash
# 允许必要端口
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. 数据库安全

- 使用强密码
- 限制数据库访问（只允许应用服务器连接）
- 定期备份
- 启用 SSL 连接

### 4. 定期更新

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 更新依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## 监控和日志

### 日志位置

- **应用日志**: `backend/logs/`
- **Nginx 日志**: `/var/log/nginx/`
- **系统日志**: `/var/log/syslog`

### 健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# 预期响应
{"status": "healthy", "version": "0.1.0"}
```

### 性能监控

建议安装:
- Prometheus + Grafana
- 或 DataDog / New Relic

---

## 备份和恢复

### 数据库备份

```bash
# 备份
pg_dump -U postgres coding_stats > backup_$(date +%Y%m%d).sql

# 恢复
psql -U postgres coding_stats < backup_20240329.sql
```

### 自动备份脚本

```bash
#!/bin/bash
# /opt/coding-stats/backup.sh

BACKUP_DIR="/backups/coding-stats"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -U postgres coding_stats | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 保留最近 7 天的备份
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
```

添加到 crontab:

```bash
0 2 * * * /opt/coding-stats/backup.sh
```

---

## 故障排除

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 检查连接
psql -U postgres -h localhost -d coding_stats
```

#### 2. Redis 连接失败

```bash
# 检查 Redis 状态
sudo systemctl status redis

# 应用会优雅降级（不使用缓存）
```

#### 3. 端口占用

```bash
# 检查端口
sudo lsof -i :8000

# 释放端口
sudo kill -9 <PID>
```

#### 4. 权限问题

```bash
# 修复文件权限
sudo chown -R coding-stats:coding-stats /opt/coding-stats
```

---

## 升级指南

### 小版本升级

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 运行迁移
alembic upgrade head

# 重启服务
sudo systemctl restart coding-stats
```

### 大版本升级

1. 阅读 CHANGELOG
2. 在测试环境验证
3. 备份数据库
4. 按小版本升级步骤操作
5. 验证功能

---

## 支持

如有问题，请:
1. 查看日志文件
2. 检查健康端点
3. 联系开发团队

---

**文档版本**: v1.0.0
**最后更新**: 2026-03-29
