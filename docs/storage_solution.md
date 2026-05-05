# PostgreSQL 存储方案 for LangGraph Checkpointer

## 目录

1. [PostgreSQL 安装部署 (Ubuntu 22.04)](#1-postgresql-安装部署-ubuntu-2204)
2. [数据库初始化](#2-数据库初始化)
3. [LangGraph PostgreSQL Checkpointer 配置](#3-langgraph-postgresql-checkpointer-配置)
4. [deepagents 集成方案](#4-deepagents-集成方案)
5. [验证与测试](#5-验证与测试)
6. [备份与维护](#6-备份与维护)

---

## 1. PostgreSQL 安装部署 (Ubuntu 22.04)

### 1.1 安装 PostgreSQL

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# 验证安装
sudo systemctl status postgresql
psql --version
```

### 1.2 配置端口 5455

```bash
# 编辑 PostgreSQL 配置文件
sudo nano /etc/postgresql/14/main/postgresql.conf

# 找到 #port = 5432，修改为：
port = 5455

# 或者追加到文件末尾：
echo "port = 5455" | sudo tee -a /etc/postgresql/14/main/postgresql.conf
```

### 1.3 配置远程访问

```bash
# 编辑 pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# 添加以下行允许远程连接：
# IPv4 本地连接
host    all     all     127.0.0.1/32    md5
# IPv4 远程连接（根据需要调整 IP 范围）
host    all     all     0.0.0.0/0       md5

# 编辑 postgresql.conf 允许监听所有地址
sudo nano /etc/postgresql/14/main/postgresql.conf

# 找到 listen_addresses，修改为：
listen_addresses = '*'

# 或者追加：
echo "listen_addresses = '*'" | sudo tee -a /etc/postgresql/14/main/postgresql.conf
```

### 1.4 重启服务

```bash
# 重启 PostgreSQL
sudo systemctl restart postgresql

# 验证端口监听
sudo ss -tlnp | grep 5455
```

### 1.5 一键安装脚本

```bash
#!/bin/bash
# install_postgresql.sh

set -e

POSTGRES_PORT=5455
DB_NAME="langgraph"
DB_USER="langgraph_user"
DB_PASS="your_secure_password_here"

echo "=== Installing PostgreSQL on Ubuntu 22.04 ==="

# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Configure port
sudo sed -i "s/#port = 5432/port = ${POSTGRES_PORT}/" /etc/postgresql/14/main/postgresql.conf
echo "Port configured: ${POSTGRES_PORT}"

# Configure remote access
echo "listen_addresses = '*'" | sudo tee -a /etc/postgresql/14/main/postgresql.conf
sudo sed -i 's/127.0.0.1\/32/0.0.0.0\/0/' /etc/postgresql/14/main/pg_hba.conf
sudo sed -i 's/scram-sha-256/md5/' /etc/postgresql/14/main/pg_hba.conf

# Restart PostgreSQL
sudo systemctl restart postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -p ${POSTGRES_PORT} <<EOF
-- Create user
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';

-- Create database
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};

-- Connect to database and create extensions
\c ${DB_NAME}
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO ${DB_USER};
ALTER DATABASE ${DB_NAME} SET jit = off;
EOF

echo "=== PostgreSQL installation complete ==="
echo "Host: localhost"
echo "Port: ${POSTGRES_PORT}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
```

### 1.6 防火墙配置（如需要）

```bash
# 开放 5455 端口
sudo ufw allow 5455/tcp
sudo ufw status
```

---

## 2. 数据库初始化

### 2.1 连接 PostgreSQL

```bash
# 本地连接
psql -h localhost -p 5455 -U langgraph_user -d langgraph

# 或使用 sudo
sudo -u postgres psql -p 5455
```

### 2.2 LangGraph 所需表结构

LangGraph 的 PostgreSQL checkpointer 会自动创建所需的表。以下是手动创建表结构的参考：

```sql
-- 连接到数据库
\c langgraph

-- 创建 LangGraph 所需的表
-- 注意：如果你使用 langgraph-checkpointer-postgres，这些表会自动创建

-- 1. checkpoints 表 - 存储对话状态快照
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id VARCHAR(255) NOT NULL,
    checkpoint_id VARCHAR(255) NOT NULL,
    parent_checkpoint_id VARCHAR(255),
    type VARCHAR(255) NOT NULL,
    checkpoint JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_id)
);

-- 2. checkpoint_writes 表 - 存储检查点写入
CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id VARCHAR(255) NOT NULL,
    checkpoint_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    idx SERIAL,
    type VARCHAR(255) NOT NULL,
    channel VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_id, task_id, idx)
);

-- 3. 索引
CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_parent ON checkpoints(parent_checkpoint_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_writes_thread ON checkpoint_writes(thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_writes_checkpoint ON checkpoint_writes(checkpoint_id);

-- 4. 授权
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO langgraph_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO langgraph_user;
```

---

## 3. LangGraph PostgreSQL Checkpointer 配置

### 3.1 安装依赖包

```bash
# 激活虚拟环境
source /path/to/your/.venv/bin/activate

# 安装 PostgreSQL checkpointer 包
pip install langgraph-checkpointer-postgres

# 或安装 psycopg2（同步版本）
pip install psycopg2-binary

# 或安装 psycopg3（异步版本，推荐）
pip install psycopg
```

### 3.2 同步版本 - PostgresSaver

```python
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg2 import connect

# 创建数据库连接
connection = connect(
    host="localhost",
    port=5455,
    dbname="langgraph",
    user="langgraph_user",
    password="your_secure_password_here"
)

# 创建 PostgresSaver checkpointer
checkpointer = PostgresSaver(connection)

# 可选：初始化数据库表（首次使用）
checkpointer.setup()

# 使用
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    checkpointer=checkpointer,
    # ... 其他参数
)
```

### 3.3 异步版本 - AsyncPostgresSaver（推荐）

```python
from langgraph.checkpoint.postgres import AsyncPostgresSaver
import asyncpg
import psycopg

# 异步连接字符串
DATABASE_URL = "postgresql://langgraph_user:your_secure_password_here@localhost:5455/langgraph"

# 方式1：使用 psycopg
async def create_checkpointer():
    checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
    await checkpointer.setup()  # 初始化表结构
    return checkpointer

# 方式2：使用 asyncpg
async def create_checkpointer_asyncpg():
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5455,
        database="langgraph",
        user="langgraph_user",
        password="your_secure_password_here",
        min_size=5,
        max_size=20
    )
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    return checkpointer
```

---

## 4. deepagents 集成方案

### 4.1 基础集成

```python
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.postgres import AsyncPostgresSaver

# PostgreSQL 配置
DATABASE_URL = "postgresql://langgraph_user:your_secure_password_here@localhost:5455/langgraph"

# 创建 AsyncPostgresSaver
checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)

# 项目路径
PROJECT_ROOT = Path(__file__).parent
SKILLS_DIR = PROJECT_ROOT / "skills"

# 初始化 backend
backend = FilesystemBackend(root_dir=str(PROJECT_ROOT))

# 创建 Agent（仅同步版本示例）
agent = create_deep_agent(
    name="car-sales-agent",
    model="anthropic:claude-sonnet-4-6",
    backend=backend,
    skills=[str(SKILLS_DIR)],
    system_prompt="你是一个专业的二手车销售顾问。",
    checkpointer=checkpointer,  # 直接传入 checkpointer
)
```

### 4.2 完整集成示例（带连接池管理）

```python
# storage.py
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from langgraph.checkpoint.postgres import AsyncPostgresSaver

# 数据库配置
DATABASE_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5455")),
    "database": os.getenv("PG_DATABASE", "langgraph"),
    "user": os.getenv("PG_USER", "langgraph_user"),
    "password": os.getenv("PG_PASSWORD"),
    "min_size": 5,
    "max_size": 20,
}

# 全局连接池
_pool: asyncpg.Pool | None = None


async def get_connection_pool() -> asyncpg.Pool:
    """获取或创建数据库连接池（单例模式）"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(**DATABASE_CONFIG)
    return _pool


async def close_connection_pool() -> None:
    """关闭数据库连接池"""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def create_postgres_checkpointer() -> AsyncPostgresSaver:
    """创建 PostgreSQL checkpointer"""
    pool = await get_connection_pool()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    return checkpointer


# agent.py
import asyncio
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from storage import create_postgres_checkpointer, close_connection_pool

PROJECT_ROOT = Path(__file__).parent


async def initialize_agent():
    """初始化 Agent"""
    # 创建 checkpointer
    checkpointer = await create_postgres_checkpointer()

    # 创建 backend
    backend = FilesystemBackend(root_dir=str(PROJECT_ROOT))

    # 创建 Agent
    agent = create_deep_agent(
        name="car-sales-agent",
        model="anthropic:claude-sonnet-4-6",
        backend=backend,
        skills=[str(PROJECT_ROOT / "skills")],
        system_prompt="你是一个专业的二手车销售顾问。",
        checkpointer=checkpointer,
    )

    return agent


async def main():
    # 初始化
    agent = await initialize_agent()

    # 对话
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "推荐一款15万左右的家用车"}]},
        config={"configurable": {"thread_id": "user_123_session_1"}}
    )

    print(response["messages"][-1].content)

    # 关闭连接池
    await close_connection_pool()


if __name__ == "__main__":
    asyncio.run(main())
```

### 4.3 同步版本集成

```python
# storage_sync.py
import os
from psycopg2 import connect
from langgraph.checkpoint.postgres import PostgresSaver

DATABASE_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5455")),
    "database": os.getenv("PG_DATABASE", "langgraph"),
    "user": os.getenv("PG_USER", "langgraph_user"),
    "password": os.getenv("PG_PASSWORD"),
}


def create_postgres_checkpointer() -> PostgresSaver:
    """创建同步 PostgreSQL checkpointer"""
    connection = connect(**DATABASE_CONFIG)
    checkpointer = PostgresSaver(connection)
    checkpointer.setup()
    return checkpointer


# agent.py (同步版本)
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from storage_sync import create_postgres_checkpointer

PROJECT_ROOT = Path(__file__).parent

checkpointer = create_postgres_checkpointer()

agent = create_deep_agent(
    name="car-sales-agent",
    model="anthropic:claude-sonnet-4-6",
    backend=FilesystemBackend(root_dir=str(PROJECT_ROOT)),
    skills=[str(PROJECT_ROOT / "skills")],
    system_prompt="你是一个专业的二手车销售顾问。",
    checkpointer=checkpointer,
)

# 对话
response = agent.invoke(
    {"messages": [{"role": "user", "content": "推荐一款15万左右的家用车"}]},
    config={"configurable": {"thread_id": "user_123_session_1"}}
)
```

### 4.4 使用环境变量配置

```bash
# .env
PG_HOST=localhost
PG_PORT=5455
PG_DATABASE=langgraph
PG_USER=langgraph_user
PG_PASSWORD=your_secure_password_here
```

```python
# config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    host: str = os.getenv("PG_HOST", "localhost")
    port: int = int(os.getenv("PG_PORT", "5455"))
    database: str = os.getenv("PG_DATABASE", "langgraph")
    user: str = os.getenv("PG_USER", "langgraph_user")
    password: str = os.getenv("PG_PASSWORD", "")

    @property
    def conn_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


db_config = DatabaseConfig()
```

---

## 5. 验证与测试

### 5.1 测试数据库连接

```python
import asyncpg


async def test_connection():
    try:
        pool = await asyncpg.create_pool(
            host="localhost",
            port=5455,
            database="langgraph",
            user="langgraph_user",
            password="your_password",
            command_timeout=5,
        )
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            print(f"Connection successful: {result}")
        await pool.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
```

### 5.2 测试 Checkpointer

```python
import asyncio
from langgraph.checkpoint.postgres import AsyncPostgresSaver


async def test_checkpointer():
    # 创建 checkpointer
    checkpointer = AsyncPostgresSaver.from_conn_string(
        "postgresql://langgraph_user:your_password@localhost:5455/langgraph"
    )

    # 初始化表结构
    await checkpointer.setup()

    # 准备测试数据
    test_config = {"configurable": {"thread_id": "test_thread"}}

    # 存储检查点
    test_state = {"messages": [{"role": "user", "content": "hello"}]}
    await checkpointer.aput(
        test_config,
        test_state,
        {"source": "test", "step": 1}
    )

    # 读取检查点
    saved = await checkpointer.aget(test_config)
    print(f"Saved state: {saved}")

    # 获取历史记录
    history = await checkpointer.aget_list({"thread_id": "test_thread"})
    print(f"History length: {len(history)}")

    print("Checkpointer test passed!")


if __name__ == "__main__":
    asyncio.run(test_checkpointer())
```

### 5.3 测试 Agent 状态持久化

```python
import asyncio
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.postgres import AsyncPostgresSaver
from pathlib import Path


async def test_agent_persistence():
    # 创建 checkpointer
    checkpointer = AsyncPostgresSaver.from_conn_string(
        "postgresql://langgraph_user:your_password@localhost:5455/langgraph"
    )
    await checkpointer.setup()

    # 创建 agent
    agent = create_deep_agent(
        name="test-agent",
        model="anthropic:claude-sonnet-4-6",
        backend=FilesystemBackend(root_dir=str(Path(__file__).parent)),
        checkpointer=checkpointer,
    )

    thread_id = "user_456_session_1"

    # 第一次对话
    response1 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我叫张三"}]},
        config={"configurable": {"thread_id": thread_id}}
    )

    # 第二次对话（应该记得张三）
    response2 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我叫什么名字？"}]},
        config={"configurable": {"thread_id": thread_id}}
    )

    print(f"Response 2: {response2['messages'][-1].content}")
    # 期望输出：我叫张三


if __name__ == "__main__":
    asyncio.run(test_agent_persistence())
```

---

## 6. 备份与维护

### 6.1 数据库备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="langgraph"
DB_USER="langgraph_user"
PG_PORT="5455"

mkdir -p $BACKUP_DIR

# 全量备份
pg_dump -h localhost -p $PG_PORT -U $DB_USER -F c -f "$BACKUP_DIR/langgraph_$DATE.dump" $DB_NAME

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/langgraph_$DATE.dump"
```

### 6.2 定时备份 Cron

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 3 点备份
0 3 * * * /path/to/backup.sh >> /var/log/pg_backup.log 2>&1
```

### 6.3 表空间和性能优化

```sql
-- 分析表统计信息
ANALYZE checkpoints;
ANALYZE checkpoint_writes;

-- 检查表大小
SELECT
    pg_size_pretty(pg_total_relation_size('checkpoints')) as total_size,
    pg_size_pretty(pg_relation_size('checkpoints')) as table_size,
    pg_size_pretty(pg_indexes_size('checkpoints')) as index_size
FROM pg_tables
WHERE tablename = 'checkpoints';

-- 清理历史数据（根据业务需求）
-- 删除 30 天前的检查点
DELETE FROM checkpoints
WHERE created_at < NOW() - INTERVAL '30 days';

-- 重新索引
REINDEX TABLE checkpoints;
REINDEX TABLE checkpoint_writes;
```

### 6.4 连接池监控

```python
import asyncpg
import asyncio


async def monitor_connections():
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5455,
        database="langgraph",
        user="langgraph_user",
        password="your_password",
        min_size=5,
        max_size=20,
    )

    # 获取池状态
    print(f"Pool size: {pool.get_size()}")
    print(f"Free connections: {pool.get_idle_size()}")

    # 获取当前连接数
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = 'langgraph'"
        )
        print(f"Active connections: {result}")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(monitor_connections())
```

---

## 附录：常见问题

### Q1: 连接被拒绝

```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 检查端口监听
sudo ss -tlnp | grep 5455

# 检查防火墙
sudo ufw status
```

### Q2: 认证失败

```sql
-- 修改用户密码
sudo -u postgres psql -p 5455
ALTER USER langgraph_user WITH PASSWORD 'new_password';
```

### Q3: 表已存在错误

```python
# 使用 setup() 前先检查
from langgraph.checkpoint.postgres import AsyncPostgresSaver

checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
# setup() 会在表已存在时忽略错误
```

### Q4: 连接池耗尽

```python
# 增加连接池大小
pool = await asyncpg.create_pool(
    host="localhost",
    port=5455,
    database="langgraph",
    user="langgraph_user",
    password="your_password",
    min_size=10,  # 增加
    max_size=50,  # 增加
)
```

---

*文档生成时间：2026-04-24*
