# 实时通信替代方案

## 技术对比

| 特性 | WebSocket | SSE | 长轮询 | HTTP/2 Push | WebRTC |
|------|-----------|-----|--------|-------------|--------|
| 双向通信 | 是 | 否 | 是 | 否 | 是 |
| 实时性 | 是 | 是 | 接近实时 | 是 | 是 |
| 浏览器支持 | 优秀 | 良好 | 通用 | 良好 | 良好 |
| 代理问题 | 一些 | 少见 | 少见 | 一些 | 一些 |
| 开销 | 低 | 低 | 高 | 中等 | 中等 |
| 使用场景 | 聊天、游戏 | 信息流、更新 | 遗留系统 | 资产 | 音视频 |

## 服务器发送事件 (SSE)

### 何时使用 SSE

- 单向服务器到客户端通信
- 实时信息流、通知、股票行情
- 需要自动重连
- 比 WebSocket 更简单
- 更好的防火墙/代理兼容性

### SSE 服务器 (Node.js)

```javascript
const express = require('express');
const app = express();

app.get('/events', (req, res) => {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');

  // Send initial connection message
  res.write('data: {"message": "Connected"}\n\n');

  // Send updates every 5 seconds
  const intervalId = setInterval(() => {
    const data = {
      timestamp: Date.now(),
      value: Math.random()
    };

    res.write(`data: ${JSON.stringify(data)}\n\n`);
  }, 5000);

  // Cleanup on client disconnect
  req.on('close', () => {
    clearInterval(intervalId);
    res.end();
  });
});

app.listen(3000);
```

### SSE 客户端

```javascript
const eventSource = new EventSource('http://localhost:3000/events');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  // Automatically reconnects
};

// Named events
eventSource.addEventListener('update', (event) => {
  console.log('Update:', event.data);
});

// Close connection
eventSource.close();
```

### SSE with Express

```javascript
const express = require('express');
const app = express();

class SSEManager {
  constructor() {
    this.clients = new Set();
  }

  addClient(res) {
    this.clients.add(res);
  }

  removeClient(res) {
    this.clients.delete(res);
  }

  broadcast(event, data) {
    const message = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;

    this.clients.forEach(client => {
      client.write(message);
    });
  }
}

const sseManager = new SSEManager();

app.get('/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  sseManager.addClient(res);

  req.on('close', () => {
    sseManager.removeClient(res);
  });
});

// Broadcast to all clients
setInterval(() => {
  sseManager.broadcast('update', {
    timestamp: Date.now(),
    activeClients: sseManager.clients.size
  });
}, 10000);

app.listen(3000);
```

## 长轮询

### 何时使用长轮询

- 需要支持遗留浏览器
- 防火墙/代理阻止 WebSocket
- 更新频率非常低
- 仅作为回退机制

### 长轮询服务器

```javascript
const express = require('express');
const app = express();

const pendingRequests = new Map();
const messages = [];

app.get('/poll', (req, res) => {
  const clientId = req.query.clientId;

  // If messages available, send immediately
  if (messages.length > 0) {
    res.json({ messages });
    messages.length = 0; // Clear messages
    return;
  }

  // Hold request until timeout or new message
  const timeout = setTimeout(() => {
    pendingRequests.delete(clientId);
    res.json({ messages: [] });
  }, 30000); // 30 second timeout

  pendingRequests.set(clientId, { res, timeout });

  req.on('close', () => {
    clearTimeout(timeout);
    pendingRequests.delete(clientId);
  });
});

app.post('/send', express.json(), (req, res) => {
  messages.push(req.body.message);

  // Respond to all pending requests
  pendingRequests.forEach(({ res, timeout }, clientId) => {
    clearTimeout(timeout);
    res.json({ messages });
    pendingRequests.delete(clientId);
  });

  messages.length = 0; // Clear messages
  res.json({ success: true });
});

app.listen(3000);
```

### 长轮询客户端

```javascript
const clientId = Math.random().toString(36);

async function poll() {
  try {
    const response = await fetch(
      `http://localhost:3000/poll?clientId=${clientId}`,
      { signal: AbortSignal.timeout(35000) }
    );

    const data = await response.json();

    if (data.messages.length > 0) {
      console.log('Received messages:', data.messages);
    }

    // Immediately poll again
    poll();
  } catch (error) {
    console.error('Polling error:', error);
    // Retry after delay
    setTimeout(poll, 5000);
  }
}

poll();
```

## HTTP/2 Server Push（已弃用）

注意：HTTP/2 Server Push 已被弃用并从 Chrome 中移除。改用 103 Early Hints。

```javascript
// Example for historical context only
const http2 = require('http2');
const fs = require('fs');

const server = http2.createSecureServer({
  key: fs.readFileSync('server.key'),
  cert: fs.readFileSync('server.crt')
});

server.on('stream', (stream, headers) => {
  if (headers[':path'] === '/') {
    // Push assets before HTML response
    stream.pushStream({ ':path': '/style.css' }, (err, pushStream) => {
      if (!err) {
        pushStream.respondWithFile('style.css');
      }
    });

    stream.respondWithFile('index.html');
  }
});

server.listen(3000);
```

## 决策矩阵

### 选择 WebSocket 时：

- 需要双向通信
- 低延迟至关重要（< 50ms）
- 高消息频率（> 1 msg/sec）
- 游戏、聊天、协作编辑
- 二进制数据传输
- 需要自定义协议

### 选择 SSE 时：

- 仅需要单向服务器到客户端通信
- 股票行情、实时信息流
- 新闻/通知
- 偏好更简单的实现
- 需要更好的代理兼容性
- 自动重连很重要

### 选择长轮询时：

- 需要支持遗留浏览器（IE8/9）
- WebSocket 被防火墙阻止
- 更新频率非常低
- 仅作为回退机制

### 选择 HTTP 流式传输时：

- 大数据传输
- 带进度条的上传
- 视频/音频流
- 单向数据流

### 选择 WebRTC 时：

- 点对点通信
- 音视频通话
- 屏幕共享
- 点对点文件传输
- 需要低延迟 P2P

## 混合方法

```javascript
// Socket.IO with automatic fallback
const io = require('socket.io')(3000, {
  transports: ['websocket', 'polling'], // Try WebSocket first
  upgrade: true,
  allowUpgrades: true
});

io.on('connection', (socket) => {
  console.log('Connected via:', socket.conn.transport.name);

  socket.conn.on('upgrade', () => {
    console.log('Upgraded to:', socket.conn.transport.name);
  });
});
```

## 性能特征

### 延迟 (p99)

- WebSocket: 5-20ms
- SSE: 10-50ms
- 长轮询: 100-500ms
- HTTP/2: 20-100ms

### 吞吐量（消息/秒）

- WebSocket: 每连接 10,000+
- SSE: 每连接 1,000+
- 长轮询: 每连接 1-10

### 连接限制（每服务器）

- WebSocket: 50,000-100,000
- SSE: 50,000-100,000
- 长轮询: 10,000-20,000

### 开销（每消息）

- WebSocket: 2-6 字节
- SSE: ~20 字节
- 长轮询: 500-2000 字节（HTTP 头）

## 迁移路径

### 从轮询到 WebSocket

```javascript
// Step 1: Support both
app.get('/api/messages', (req, res) => {
  // Legacy polling endpoint
  res.json({ messages: getRecentMessages() });
});

io.on('connection', (socket) => {
  // New WebSocket endpoint
  socket.on('subscribe', (channel) => {
    socket.join(channel);
  });
});

// Step 2: Gradually migrate clients
// Step 3: Deprecate polling endpoint
```

### 从 SSE 到 WebSocket

```javascript
// SSE provides read-only, add WebSocket for writes
app.get('/events', sseHandler);  // Keep for reads

io.on('connection', (socket) => {
  socket.on('action', (data) => {
    // Handle writes via WebSocket
    processAction(data);
  });
});

// Eventually migrate reads to WebSocket too
```

## 最佳实践

1. 从最简单的解决方案开始（单向使用 SSE）
2. 使用 Socket.IO 实现自动回退
3. 在过度工程化之前监控实际需求
4. 考虑移动设备/网络限制
5. 实现优雅降级
6. 上线前进行负载测试
7. 有回退策略
8. 监控连接成功率