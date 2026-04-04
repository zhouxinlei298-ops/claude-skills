# PostgreSQL 复制

## 流复制（物理）

### 主服务器设置

```sql
-- postgresql.conf
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB  # 或旧版本使用 1024MB
hot_standby = on
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'

-- pg_hba.conf（允许复制连接）
host replication replicator 10.0.0.0/24 scram-sha-256
```

```sql
-- 创建复制用户
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'secure_password';

-- 创建复制槽（防止 WAL 删除）
SELECT * FROM pg_create_physical_replication_slot('replica_1');
```

### 备用服务器设置

```bash
# 停止备用服务器上的 PostgreSQL
systemctl stop postgresql

# 移除数据目录
rm -rf /var/lib/postgresql/14/main/*

# 从主服务器进行基本备份
pg_basebackup -h primary-host -D /var/lib/postgresql/14/main \
  -U replicator -P -v -R -X stream -S replica_1

# -R 创建 standby.signal 和恢复配置
# -X stream: 备份期间流式传输 WAL
# -S replica_1: 使用复制槽
```

```sql
-- pg_basebackup -R 创建的 standby.signal 文件
-- postgresql.auto.conf 中的恢复参数：
primary_conninfo = 'host=primary-host port=5432 user=replicator password=secure_password'
primary_slot_name = 'replica_1'
```

### 监控复制

```sql
-- 在主服务器上：检查复制状态
SELECT
  client_addr,
  state,
  sync_state,
  sent_lsn,
  write_lsn,
  flush_lsn,
  replay_lsn,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes
FROM pg_stat_replication;

-- 在备用服务器上：检查回放延迟
SELECT
  now() - pg_last_xact_replay_timestamp() AS replication_lag;

-- 检查复制槽
SELECT
  slot_name,
  slot_type,
  active,
  restart_lsn,
  pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as retained_bytes
FROM pg_replication_slots;
```

### 同步复制

```sql
-- 主服务器上的 postgresql.conf
synchronous_commit = on
synchronous_standby_names = 'FIRST 1 (replica_1, replica_2)'
# 提交前等待 1 个备用服务器确认

# 选项：
# FIRST n (names)：等待 n 个备用服务器
# ANY n (names)：等待任意 n 个备用服务器
# name：等待特定备用服务器

-- 检查同步状态的查询
SELECT
  application_name,
  sync_state,
  state
FROM pg_stat_replication;
-- sync_state: sync（同步）、async、potential
```

## 逻辑复制（行级）

### 发布者设置

```sql
-- postgresql.conf
wal_level = logical
max_replication_slots = 10
max_wal_senders = 10

-- 创建发布（所有表）
CREATE PUBLICATION my_publication FOR ALL TABLES;

-- 或特定表
CREATE PUBLICATION my_publication FOR TABLE users, orders;

-- 或匹配模式的表（PG15+）
CREATE PUBLICATION my_publication FOR TABLES IN SCHEMA public;

-- 带行过滤器（PG15+）
CREATE PUBLICATION active_users FOR TABLE users WHERE (active = true);

-- 查看发布
SELECT * FROM pg_publication;
SELECT * FROM pg_publication_tables;
```

### 订阅者设置

```sql
-- 创建订阅（在发布者上创建复制槽）
CREATE SUBSCRIPTION my_subscription
CONNECTION 'host=publisher-host port=5432 dbname=mydb user=replicator password=pass'
PUBLICATION my_publication;

-- 订阅选项
CREATE SUBSCRIPTION my_subscription
CONNECTION 'host=publisher-host dbname=mydb user=replicator'
PUBLICATION my_publication
WITH (
  copy_data = true,           -- 初始数据复制
  create_slot = true,          -- 创建复制槽
  enabled = true,              -- 立即启动
  slot_name = 'my_sub_slot',
  synchronous_commit = 'off'   -- 性能与持久性
);

-- 查看订阅
SELECT * FROM pg_subscription;
SELECT * FROM pg_stat_subscription;

-- 管理订阅
ALTER SUBSCRIPTION my_subscription DISABLE;
ALTER SUBSCRIPTION my_subscription ENABLE;
ALTER SUBSCRIPTION my_subscription REFRESH PUBLICATION;
DROP SUBSCRIPTION my_subscription;
```

### 逻辑复制监控

```sql
-- 在发布者上：检查复制槽
SELECT
  slot_name,
  plugin,
  slot_type,
  active,
  pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn) as lag_bytes
FROM pg_replication_slots
WHERE slot_type = 'logical';

-- 在订阅者上：检查订阅状态
SELECT
  subname,
  pid,
  received_lsn,
  latest_end_lsn,
  last_msg_send_time,
  last_msg_receipt_time,
  latest_end_time
FROM pg_stat_subscription;
```

## 级联复制

```
Primary -> Standby1 -> Standby2
```

```sql
-- 在 Standby1 上（作为中继）
-- postgresql.conf
hot_standby = on
max_wal_senders = 10
wal_keep_size = 1GB

-- Standby2 连接到 Standby1
-- 与常规备用服务器相同的设置，但 primary_conninfo 指向 Standby1
primary_conninfo = 'host=standby1-host user=replicator...'
```

## 延迟复制（延迟备用）

```sql
-- 在备用服务器上：postgresql.conf
recovery_min_apply_delay = '4h'

-- 适用于：
-- - 防止意外数据删除
-- - 滚回到特定时间点
-- - 可以提升延迟备用服务器以恢复删除的表

-- 检查延迟
SELECT now() - pg_last_xact_replay_timestamp() AS current_delay;
```

## 故障转移和提升

### 手动故障转移

```bash
# 在备用服务器上
# 将备用服务器提升为主服务器
pg_ctl promote -D /var/lib/postgresql/14/main

# 或使用 SQL
SELECT pg_promote();

# 验证提升
SELECT pg_is_in_recovery();  -- 应返回 false
```

### 使用 pg_auto_failover 自动故障转移

```bash
# 安装 pg_auto_failover
apt-get install pg-auto-failover

# 设置监控节点
pg_autoctl create monitor --hostname monitor-host --pgdata /var/lib/monitor

# 设置主服务器
pg_autoctl create postgres \
  --hostname primary-host \
  --pgdata /var/lib/postgresql/14/main \
  --monitor postgres://monitor-host/pg_auto_failover

# 设置备用服务器
pg_autoctl create postgres \
  --hostname standby-host \
  --pgdata /var/lib/postgresql/14/main \
  --monitor postgres://monitor-host/pg_auto_failover

# 检查状态
pg_autoctl show state
```

### Patroni（生产 HA 解决方案）

```yaml
# patroni.yml
scope: postgres-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: node1:8008

etcd:
  hosts: etcd1:2379,etcd2:2379,etcd3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 100
        max_wal_senders: 10
        wal_level: replica

postgresql:
  listen: 0.0.0.0:5432
  connect_address: node1:5432
  data_dir: /var/lib/postgresql/14/main
  authentication:
    replication:
      username: replicator
      password: repl_password
    superuser:
      username: postgres
      password: postgres_password
```

## HA 的连接池

### PgBouncer 配置

```ini
# pgbouncer.ini
[databases]
mydb = host=primary-host port=5432 dbname=mydb

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
```

### HAProxy 负载均衡

```
# haproxy.cfg
frontend postgres_frontend
    bind *:5432
    mode tcp
    default_backend postgres_backend

backend postgres_backend
    mode tcp
    option tcp-check
    tcp-check expect string is_master:true

    server primary primary-host:5432 check
    server standby1 standby1-host:5432 check backup
    server standby2 standby2-host:5432 check backup
```

## 备份和时点恢复（PITR）

### WAL 归档设置

```sql
-- postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /backup/wal/%f && cp %p /backup/wal/%f'
archive_timeout = 300  # 每 5 分钟强制归档

-- 或使用 pg_archivecleanup
archive_command = 'pgbackrest --stanza=main archive-push %p'
```

### 使用 pg_basebackup 进行基本备份

```bash
# 完整备份
pg_basebackup -h localhost -U postgres \
  -D /backup/base/$(date +%Y%m%d) \
  -Ft -z -P -X fetch

# -Ft: tar 格式
# -z: gzip 压缩
# -P: 进度
# -X fetch: 包含 WAL 文件
```

### 时点恢复

```bash
# 停止 PostgreSQL
systemctl stop postgresql

# 恢复基本备份
rm -rf /var/lib/postgresql/14/main/*
tar -xzf /backup/base/20241201/base.tar.gz -C /var/lib/postgresql/14/main

# 创建 recovery.signal
touch /var/lib/postgresql/14/main/recovery.signal

# 配置恢复
# postgresql.conf 或 postgresql.auto.conf：
restore_command = 'cp /backup/wal/%f %p'
recovery_target_time = '2024-12-01 14:30:00'
# 或：recovery_target_xid, recovery_target_name, recovery_target_lsn

# 启动 PostgreSQL（将恢复到目标）
systemctl start postgresql

# 恢复完成后检查
SELECT pg_is_in_recovery();  # 恢复完成后应为 false
```

## 监控最佳实践

```sql
-- 创建监控视图
CREATE VIEW replication_status AS
SELECT
  client_addr,
  application_name,
  state,
  sync_state,
  pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) / 1024 / 1024 AS lag_mb,
  (pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)::float /
   (1024 * 1024 * 16))::int AS estimated_wal_segments_behind
FROM pg_stat_replication;

-- 如果延迟 > 100MB 则告警
SELECT * FROM replication_status WHERE lag_mb > 100;

-- 检查复制槽磁盘使用
SELECT
  slot_name,
  pg_size_pretty(
    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)
  ) as retained_wal
FROM pg_replication_slots;
```

## 故障排除

```sql
-- 复制中断？
-- 1. 在主服务器上检查 pg_stat_replication
SELECT * FROM pg_stat_replication;

-- 2. 在备用服务器上检查日志
-- tail -f /var/log/postgresql/postgresql-14-main.log

-- 3. 检查复制槽是否存在
SELECT * FROM pg_replication_slots WHERE slot_name = 'replica_1';

-- 4. 如果缺失则重新创建槽
SELECT pg_create_physical_replication_slot('replica_1');

-- 5. 检查 WAL 文件是否可用
-- ls -lh /var/lib/postgresql/14/main/pg_wal/

-- 备用服务器落后太多？
-- 选项 1：增加 wal_keep_size
-- 选项 2：使用复制槽
-- 选项 3：重新运行 pg_basebackup
```
