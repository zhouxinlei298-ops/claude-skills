---
name: websocket-engineer
description: Use when building real-time communication systems with WebSockets or Socket.IO. Invoke for bidirectional messaging, horizontal scaling with Redis, presence tracking, room management.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: api-architecture
  triggers: WebSocket, Socket.IO, real-time communication, bidirectional messaging, pub/sub, server push, live updates, chat systems, presence tracking
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fastapi-expert, nestjs-expert, devops-engineer, monitoring-expert, security-reviewer
---

# WebSocket 工程师

## 核心工作流程

1. **分析需求** -- 确定连接规模、消息量、延迟需求
2. **设计架构** -- 规划集群、发布/订阅、状态管理、故障转移
3. **实现** -- 构建带认证、房间、事件的 WebSocket 服务器
4. **本地验证** -- 在扩展之前测试连接处理、认证和房间行为（例如 `npx wscat -c ws://localhost:3000`）；确认缺失/无效令牌的认证拒绝、房间加入/离开事件和消息传递
5. **扩展** -- 在启用适配器之前验证 Redis 连接和发布/订阅往返；配置粘性会话并通过多个实例的测试连接确认；设置负载均衡
6. **监控** -- 跟踪连接数、延迟、吞吐量、错误率；为连接数激增和错误率阈值添加告警

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|-------|-----------|-----------|
| 协议 | `references/protocol.md` | WebSocket 握手、帧、ping/pong、关闭代码 |
| 扩展 | `references/scaling.md` | 水平扩展、Redis 发布/订阅、粘性会话 |
| 模式 | `references/patterns.md` | 房间、命名空间、广播、确认 |
| 安全 | `references/security.md` | 认证、授权、速率限制、CORS |
| 替代方案 | `references/alternatives.md` | SSE、长轮询、何时选择 WebSocket |

## 代码示例

### 服务器设置（Socket.IO 带认证和房间管理）

```js
import { createServer } from "http";
import { Server } from "socket.io";
import { createAdapter } from "@socket.io/redis-adapter";
import { createClient } from "redis";
import jwt from "jsonwebtoken";

const httpServer = createServer();
const io = new Server(httpServer, {
  cors: { origin: process.env.ALLOWED_ORIGIN, credentials: true },
  pingTimeout: 20000,
  pingInterval: 25000,
});

// Authentication middleware — runs before connection is established
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  if (!token) return next(new Error("Authentication required"));
  try {
    socket.data.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch {
    next(new Error("Invalid token"));
  }
});

// Redis adapter for horizontal scaling
const pubClient = createClient({ url: process.env.REDIS_URL });
const subClient = pubClient.duplicate();
await Promise.all([pubClient.connect(), subClient.connect()]);
io.adapter(createAdapter(pubClient, subClient));

io.on("connection", (socket) => {
  const { userId } = socket.data.user;
  console.log(`connected: ${userId} (${socket.id})`);

  // Presence: mark user online
  pubClient.hSet("presence", userId, socket.id);

  socket.on("join-room", (roomId) => {
    socket.join(roomId);
    socket.to(roomId).emit("user-joined", { userId });
  });

  socket.on("message", ({ roomId, text }) => {
    io.to(roomId).emit("message", { userId, text, ts: Date.now() });
  });

  socket.on("disconnect", () => {
    pubClient.hDel("presence", userId);
    console.log(`disconnected: ${userId}`);
  });
});

httpServer.listen(3000);
```

### 客户端指数退避重连

```js
import { io } from "socket.io-client";

const socket = io("wss://api.example.com", {
  auth: { token: getAuthToken() },
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,       // initial delay (ms)
  reconnectionDelayMax: 30000,   // cap at 30 s
  randomizationFactor: 0.5,      // jitter to avoid thundering herd
});

// Queue messages while disconnected
let messageQueue = [];

socket.on("connect", () => {
  console.log("connected:", socket.id);
  // Flush queued messages
  messageQueue.forEach((msg) => socket.emit("message", msg));
  messageQueue = [];
});

socket.on("disconnect", (reason) => {
  console.warn("disconnected:", reason);
  if (reason === "io server disconnect") socket.connect(); // manual reconnect
});

socket.on("connect_error", (err) => {
  console.error("connection error:", err.message);
});

function sendMessage(roomId, text) {
  const msg = { roomId, text };
  if (socket.connected) {
    socket.emit("message", msg);
  } else {
    messageQueue.push(msg); // buffer until reconnected
  }
}
```

## 约束

### 必须做
- 为负载均衡使用粘性会话（WebSocket 连接是有状态的 -- 请求必须路由到同一服务器实例）
- 实现心跳/ping-pong 检测死连接（仅靠 TCP keepalive 是不够的）
- 使用房间/命名空间进行消息范围界定，而非在应用逻辑中过滤
- 在断连期间排队消息以避免静默数据丢失
- 在水平扩展之前规划每实例的连接限制

### 不能做
- 在没有集群策略的情况下在内存中存储大量状态（使用 Redis 或外部存储）
- 在没有显式升级处理的情况下在同一端口混合 WebSocket 和 HTTP
- 忘记处理连接清理（在线状态记录、房间成员、进行中的定时器）
- 在生产前跳过负载测试 -- 连接数激增与 HTTP 流量激增行为不同

## 输出模板

在实现 WebSocket 功能时，提供：
1. 服务器设置（Socket.IO/ws 配置）
2. 事件处理器（连接、消息、断连）
3. 客户端库（连接、事件、重连）
4. 扩展策略的简要说明

## 知识参考

Socket.IO, ws, uWebSockets.js, Redis 适配器, 粘性会话, nginx WebSocket 代理, JWT over WebSocket, 房间/命名空间, 确认机制, 二进制数据, 压缩, 心跳, 背压, 水平 Pod 自动扩展
