# 性能测试

## k6 负载测试

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp up to 20 users
    { duration: '1m', target: 20 },    // Stay at 20 users
    { duration: '30s', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% requests under 500ms
    http_req_failed: ['rate<0.01'],    // <1% errors
  },
};

export default function () {
  const res = http.get('http://localhost:3000/api/users');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1);
}
```

## 压力测试

```javascript
export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp to 100 users
    { duration: '5m', target: 100 },   // Stay at 100
    { duration: '2m', target: 200 },   // Push to 200
    { duration: '5m', target: 200 },   // Stay at 200
    { duration: '2m', target: 0 },     // Ramp down
  ],
};
```

## 尖峰测试

```javascript
export const options = {
  stages: [
    { duration: '10s', target: 10 },   // Normal load
    { duration: '1m', target: 10 },
    { duration: '10s', target: 200 },  // Spike!
    { duration: '3m', target: 200 },
    { duration: '10s', target: 10 },   // Scale down
    { duration: '3m', target: 10 },
    { duration: '10s', target: 0 },
  ],
};
```

## 带认证的 API 测试

```javascript
import http from 'k6/http';

export function setup() {
  const loginRes = http.post('http://localhost:3000/api/login', {
    email: 'test@test.com',
    password: 'password',
  });
  return { token: loginRes.json('token') };
}

export default function (data) {
  const params = {
    headers: { Authorization: `Bearer ${data.token}` },
  };

  http.get('http://localhost:3000/api/protected', params);
}
```

## 阈值参考

```javascript
thresholds: {
  // Response time
  http_req_duration: ['p(95)<500', 'p(99)<1000'],

  // Error rate
  http_req_failed: ['rate<0.01'],

  // Throughput
  http_reqs: ['rate>100'],

  // Custom metrics
  'http_req_duration{name:login}': ['p(95)<200'],
}
```

## 快速参考

| 指标 | 描述 |
|------|------|
| `http_req_duration` | 响应时间 |
| `http_req_failed` | 失败请求率 |
| `http_reqs` | 请求速率 |
| `p(95)` | 第 95 百分位 |
| `rate` | 每秒速率 |

| 测试类型 | 目的 |
|----------|------|
| 负载测试 | 正常预期负载 |
| 压力测试 | 找到断裂点 |
| 尖峰测试 | 突发流量激增 |
| 浸泡测试 | 长时间稳定性 |
