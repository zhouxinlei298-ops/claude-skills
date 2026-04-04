# Kubernetes 配置管理

## ConfigMap 模式

### 基本 ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  # Simple key-value pairs
  database.host: "postgres-service.database.svc.cluster.local"
  database.port: "5432"
  database.name: "appdb"

  # Multi-line configuration
  app.properties: |
    server.port=8080
    logging.level=INFO
    cache.enabled=true
    cache.ttl=3600

  # JSON configuration
  features.json: |
    {
      "featureA": true,
      "featureB": false,
      "maxConnections": 100
    }

  # YAML configuration
  config.yaml: |
    server:
      port: 8080
      timeout: 30s
    database:
      pool_size: 20
      max_connections: 100
```

### 从文件创建 ConfigMap

```bash
# Create from literal values
kubectl create configmap app-config \
  --from-literal=database.host=postgres \
  --from-literal=database.port=5432

# Create from file
kubectl create configmap nginx-config \
  --from-file=nginx.conf

# Create from directory
kubectl create configmap app-configs \
  --from-file=configs/
```

## Secret 模式

### 不透明 Secret（通用）

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
stringData:
  # Plain text (will be base64 encoded)
  db-password: "MySecurePassword123!"
  api-key: "sk-1234567890abcdef"
  jwt-secret: "super-secret-jwt-key"
data:
  # Already base64 encoded
  tls.crt: LS0tLS1CRUdJTi...
  tls.key: LS0tLS1CRUdJTi...
```

### TLS Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: example-tls
  namespace: production
type: kubernetes.io/tls
stringData:
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    MIIDXTCCAkWgAwIBAgIJAKZ...
    -----END CERTIFICATE-----
  tls.key: |
    -----BEGIN PRIVATE KEY-----
    MIIEvQIBADANBgkqhkiG9w0B...
    -----END PRIVATE KEY-----
```

### Docker Registry Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: registry-credentials
  namespace: production
type: kubernetes.io/dockerconfigjson
stringData:
  .dockerconfigjson: |
    {
      "auths": {
        "myregistry.io": {
          "username": "myuser",
          "password": "mypassword",
          "email": "user@example.com",
          "auth": "bXl1c2VyOm15cGFzc3dvcmQ="
        }
      }
    }
```

### 基本认证 Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: basic-auth
  namespace: production
type: kubernetes.io/basic-auth
stringData:
  username: admin
  password: super-secret-password
```

### SSH 认证 Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ssh-key
  namespace: production
type: kubernetes.io/ssh-auth
stringData:
  ssh-privatekey: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    b3BlbnNzaC1rZXktdjEAAAAABG5vbmUA...
    -----END OPENSSH PRIVATE KEY-----
```

## 使用 ConfigMap 和 Secret

### 环境变量

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    # Single value from ConfigMap
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host

    # Single value from Secret
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-password

    # All keys from ConfigMap as env vars
    envFrom:
    - configMapRef:
        name: app-config
      prefix: CONFIG_

    # All keys from Secret as env vars
    - secretRef:
        name: app-secrets
      prefix: SECRET_
```

### 卷挂载

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    # Mount entire ConfigMap as directory
    - name: config-volume
      mountPath: /etc/config
      readOnly: true

    # Mount specific key as file
    - name: app-properties
      mountPath: /etc/app/app.properties
      subPath: app.properties
      readOnly: true

    # Mount Secret as files
    - name: secrets-volume
      mountPath: /etc/secrets
      readOnly: true

    # Mount TLS certificates
    - name: tls-certs
      mountPath: /etc/tls
      readOnly: true

  volumes:
  - name: config-volume
    configMap:
      name: app-config

  - name: app-properties
    configMap:
      name: app-config
      items:
      - key: app.properties
        path: app.properties

  - name: secrets-volume
    secret:
      secretName: app-secrets
      defaultMode: 0400  # Read-only for owner

  - name: tls-certs
    secret:
      secretName: example-tls
```

## 不可变 ConfigMap 和 Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: immutable-config
  namespace: production
immutable: true
data:
  key: value
---
apiVersion: v1
kind: Secret
metadata:
  name: immutable-secret
  namespace: production
type: Opaque
immutable: true
stringData:
  password: "MyPassword123"
```

## External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
  - secretKey: db-password
    remoteRef:
      key: prod/database/password
  - secretKey: api-key
    remoteRef:
      key: prod/api/key
---
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
```

## Sealed Secrets（GitOps）

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  encryptedData:
    db-password: AgBj8xK5...encrypted...base64
    api-key: AgCY9mL2...encrypted...base64
  template:
    metadata:
      name: app-secrets
      namespace: production
    type: Opaque
```

## 环境变量最佳实践

### 结构化环境变量

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    # Application settings
    - name: APP_NAME
      value: "my-application"
    - name: APP_ENV
      value: "production"
    - name: APP_VERSION
      value: "v1.2.0"

    # Database configuration
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host
    - name: DB_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.port
    - name: DB_NAME
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.name
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-password

    # Kubernetes metadata
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: POD_IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName

    # Resource limits
    - name: MEMORY_LIMIT
      valueFrom:
        resourceFieldRef:
          containerName: app
          resource: limits.memory
    - name: CPU_REQUEST
      valueFrom:
        resourceFieldRef:
          containerName: app
          resource: requests.cpu
```

## 动态配置更新

```yaml
apiVersion: v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    metadata:
      annotations:
        # Force pod restart on config change
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
    spec:
      containers:
      - name: app
        image: myapp:latest
        volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: app-config
```

## 最佳实践

1. **分离**：使用 ConfigMap 存储非敏感数据，使用 Secret 存储凭证
2. **不可变性**：将生产配置标记为不可变以确保安全
3. **版本管理**：在 ConfigMap/Secret 名称中包含版本以进行更新
4. **最小权限**：以限制性权限（0400）将 Secret 挂载为文件
5. **外部 Secret**：使用 External Secrets Operator 连接云密钥管理器
6. **禁止硬编码**：永远不要在容器镜像中硬编码密钥
7. **加密**：在 etcd 中启用 Secret 的静态加密
8. **GitOps**：使用 Sealed Secrets 实现安全的 GitOps 工作流
9. **轮换**：实施密钥轮换策略
10. **验证**：在部署前验证配置
