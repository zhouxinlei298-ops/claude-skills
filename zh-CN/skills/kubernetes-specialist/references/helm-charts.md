# Helm Charts

## Chart 结构

```
mychart/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default values
├── values.schema.json      # Values validation schema
├── charts/                 # Dependency charts
├── templates/              # Template files
│   ├── NOTES.txt          # Post-install notes
│   ├── _helpers.tpl       # Template helpers
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── serviceaccount.yaml
│   ├── hpa.yaml
│   └── tests/
│       └── test-connection.yaml
├── .helmignore            # Ignore patterns
└── README.md              # Chart documentation
```

## Chart.yaml

```yaml
apiVersion: v2
name: myapp
description: A Helm chart for MyApp on Kubernetes
type: application
version: 1.2.0
appVersion: "2.5.0"

keywords:
  - web
  - application
  - microservice

home: https://example.com
sources:
  - https://github.com/example/myapp

maintainers:
  - name: DevOps Team
    email: devops@example.com
    url: https://example.com/team

icon: https://example.com/logo.png

dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
    tags:
      - database

  - name: redis
    version: "17.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
    tags:
      - cache

annotations:
  category: Application
```

## values.yaml

```yaml
# Default values for myapp
replicaCount: 3

image:
  repository: myregistry.io/myapp
  pullPolicy: IfNotPresent
  tag: ""  # Overrides the image tag (default is .Chart.AppVersion)

imagePullSecrets:
  - name: registry-credentials

nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true

service:
  type: ClusterIP
  port: 80
  targetPort: 8080
  annotations: {}

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: myapp.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: myapp-tls
      hosts:
        - myapp.example.com

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

nodeSelector: {}

tolerations: []

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app.kubernetes.io/name
                operator: In
                values:
                  - myapp
          topologyKey: kubernetes.io/hostname

livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2

env:
  - name: ENVIRONMENT
    value: production
  - name: LOG_LEVEL
    value: info

envFrom: []

volumeMounts: []
volumes: []

# PostgreSQL dependency
postgresql:
  enabled: true
  auth:
    username: myapp
    password: ""  # Set via --set or separate secret
    database: myapp
  primary:
    persistence:
      enabled: true
      size: 10Gi

# Redis dependency
redis:
  enabled: true
  architecture: standalone
  auth:
    enabled: true
    password: ""
  master:
    persistence:
      enabled: true
      size: 5Gi
```

## templates/_helpers.tpl

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "myapp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "myapp.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "myapp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "myapp.labels" -}}
helm.sh/chart: {{ include "myapp.chart" . }}
{{ include "myapp.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "myapp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "myapp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "myapp.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "myapp.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
```

## templates/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "myapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "myapp.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "myapp.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
      - name: {{ .Chart.Name }}
        securityContext:
          {{- toYaml .Values.securityContext | nindent 12 }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.service.targetPort }}
          protocol: TCP
        {{- with .Values.env }}
        env:
          {{- toYaml . | nindent 12 }}
        {{- end }}
        {{- with .Values.envFrom }}
        envFrom:
          {{- toYaml . | nindent 12 }}
        {{- end }}
        livenessProbe:
          {{- toYaml .Values.livenessProbe | nindent 12 }}
        readinessProbe:
          {{- toYaml .Values.readinessProbe | nindent 12 }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        {{- with .Values.volumeMounts }}
        volumeMounts:
          {{- toYaml . | nindent 12 }}
        {{- end }}
      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

## templates/hpa.yaml

```yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "myapp.fullname" . }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "myapp.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
  {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
  {{- end }}
  {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
  {{- end }}
{{- end }}
```

## Helm Hooks

### 安装前 Hook（数据库迁移）

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "myapp.fullname" . }}-migration
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  backoffLimit: 3
  template:
    metadata:
      labels:
        app: migration
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        command: ["/app/migrate", "up"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {{ include "myapp.fullname" . }}-secrets
              key: database-url
```

### 安装后 Hook（测试）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: {{ include "myapp.fullname" . }}-test
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  restartPolicy: Never
  containers:
  - name: test
    image: curlimages/curl:latest
    command: ['sh', '-c']
    args:
    - |
      curl -f http://{{ include "myapp.fullname" . }}:{{ .Values.service.port }}/health || exit 1
```

## Helm 命令

```bash
# Create new chart
helm create myapp

# Lint chart
helm lint myapp/

# Template rendering (dry-run)
helm template myapp ./myapp -f values-prod.yaml

# Install chart
helm install myapp ./myapp \
  --namespace production \
  --create-namespace \
  --values values-prod.yaml \
  --set image.tag=v1.2.0

# Upgrade chart
helm upgrade myapp ./myapp \
  --namespace production \
  --values values-prod.yaml \
  --set image.tag=v1.3.0 \
  --atomic \
  --timeout 5m

# Rollback
helm rollback myapp 1 --namespace production

# List releases
helm list --namespace production

# Get values
helm get values myapp --namespace production

# Get manifest
helm get manifest myapp --namespace production

# Uninstall
helm uninstall myapp --namespace production

# Test
helm test myapp --namespace production

# Package chart
helm package myapp/ --version 1.2.0

# Dependency update
helm dependency update myapp/
```

## values-prod.yaml（环境覆盖）

```yaml
replicaCount: 5

image:
  tag: v1.2.0

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20

ingress:
  hosts:
    - host: app.production.example.com
      paths:
        - path: /
          pathType: Prefix

postgresql:
  enabled: true
  primary:
    persistence:
      size: 100Gi
    resources:
      limits:
        cpu: 2000m
        memory: 4Gi
      requests:
        cpu: 500m
        memory: 1Gi

redis:
  enabled: true
  master:
    persistence:
      size: 20Gi
```

## Chart 测试

### Helm Test 命令

```bash
# Run chart tests after installation
helm test myapp --namespace production

# Run tests with logs
helm test myapp --namespace production --logs

# Run tests with timeout
helm test myapp --namespace production --timeout 5m
```

### Chart Testing 工具 (ct)

```bash
# Install chart-testing
brew install chart-testing

# Lint charts
ct lint --config ct.yaml

# Lint and install (CI/CD)
ct lint-and-install --config ct.yaml

# Test changed charts only
ct lint-and-install --target-branch main --config ct.yaml
```

```yaml
# ct.yaml - Chart Testing configuration
remote: origin
target-branch: main
chart-dirs:
  - charts
chart-repos:
  - bitnami=https://charts.bitnami.com/bitnami
helm-extra-args: --timeout 600s
validate-maintainers: true
check-version-increment: true
```

### 使用 helm-unittest 进行单元测试

```bash
# Install plugin
helm plugin install https://github.com/helm-unittest/helm-unittest

# Run tests
helm unittest ./mychart
```

```yaml
# tests/deployment_test.yaml
suite: deployment tests
templates:
  - templates/deployment.yaml
tests:
  - it: should create deployment with correct replicas
    set:
      replicaCount: 5
    asserts:
      - isKind:
          of: Deployment
      - equal:
          path: spec.replicas
          value: 5

  - it: should set resource limits
    set:
      resources:
        limits:
          cpu: 500m
          memory: 256Mi
    asserts:
      - equal:
          path: spec.template.spec.containers[0].resources.limits.cpu
          value: 500m

  - it: should not create HPA when autoscaling disabled
    set:
      autoscaling:
        enabled: false
    template: templates/hpa.yaml
    asserts:
      - hasDocuments:
          count: 0
```

## Values Schema 验证

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["image", "service"],
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 1
    },
    "image": {
      "type": "object",
      "required": ["repository"],
      "properties": {
        "repository": {
          "type": "string",
          "pattern": "^[a-z0-9.-/]+$"
        },
        "tag": {
          "type": "string"
        },
        "pullPolicy": {
          "type": "string",
          "enum": ["Always", "IfNotPresent", "Never"]
        }
      }
    },
    "service": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["ClusterIP", "NodePort", "LoadBalancer"]
        },
        "port": {
          "type": "integer",
          "minimum": 1,
          "maximum": 65535
        }
      }
    },
    "resources": {
      "type": "object",
      "properties": {
        "limits": {
          "$ref": "#/definitions/resourceRequirements"
        },
        "requests": {
          "$ref": "#/definitions/resourceRequirements"
        }
      }
    }
  },
  "definitions": {
    "resourceRequirements": {
      "type": "object",
      "properties": {
        "cpu": {
          "type": "string",
          "pattern": "^[0-9]+m?$"
        },
        "memory": {
          "type": "string",
          "pattern": "^[0-9]+(Mi|Gi)$"
        }
      }
    }
  }
}
```

## Chart 仓库

### 创建仓库

```bash
# Package chart
helm package mychart/ --version 1.2.0 --destination ./repo

# Generate index
helm repo index ./repo --url https://charts.example.com

# Update index with new chart
helm repo index ./repo --url https://charts.example.com --merge ./repo/index.yaml
```

### GitHub Pages 仓库

```yaml
# .github/workflows/release.yaml
name: Release Charts
on:
  push:
    branches: [main]
    paths: ['charts/**']
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Configure Git
        run: |
          git config user.name "$GITHUB_ACTOR"
          git config user.email "$GITHUB_ACTOR@users.noreply.github.com"
      - name: Install Helm
        uses: azure/setup-helm@v3
      - name: Run chart-releaser
        uses: helm/chart-releaser-action@v1.6.0
        env:
          CR_TOKEN: "${{ secrets.GITHUB_TOKEN }}"
```

### OCI Registry

```bash
# Login to registry
helm registry login myregistry.io -u user -p token

# Push chart to OCI registry
helm push mychart-1.2.0.tgz oci://myregistry.io/charts

# Pull from OCI
helm pull oci://myregistry.io/charts/mychart --version 1.2.0

# Install from OCI
helm install myapp oci://myregistry.io/charts/mychart --version 1.2.0
```

## Helm 插件

```bash
# helm-diff - preview upgrades
helm plugin install https://github.com/databus23/helm-diff
helm diff upgrade myapp ./mychart -f values-prod.yaml

# helm-secrets - manage encrypted secrets
helm plugin install https://github.com/jkroepke/helm-secrets
helm secrets encrypt secrets.yaml
helm secrets decrypt secrets.yaml.enc
helm secrets install myapp ./mychart -f secrets.yaml.enc

# helm-git - use git repos as chart sources
helm plugin install https://github.com/aslafy-z/helm-git
helm repo add mycharts git+https://github.com/myorg/charts@charts?ref=main

# helm-s3 - S3 as chart repository
helm plugin install https://github.com/hypnoglow/helm-s3
helm s3 init s3://my-bucket/charts
helm s3 push mychart-1.2.0.tgz my-s3-repo
```

## 复杂的升级/回滚

```bash
# Upgrade with atomic (rollback on failure)
helm upgrade myapp ./mychart \
  --namespace production \
  --atomic \
  --timeout 10m \
  --wait

# Upgrade with cleanup on failure
helm upgrade myapp ./mychart \
  --namespace production \
  --cleanup-on-fail

# Force resource update (recreate)
helm upgrade myapp ./mychart \
  --namespace production \
  --force

# Dry run before upgrade
helm upgrade myapp ./mychart \
  --namespace production \
  --dry-run \
  --debug

# Compare current vs new
helm get manifest myapp -n production > current.yaml
helm template myapp ./mychart -f values-prod.yaml > new.yaml
diff current.yaml new.yaml

# Rollback to specific revision
helm rollback myapp 3 --namespace production

# Rollback with wait
helm rollback myapp 3 --namespace production --wait --timeout 5m

# View revision history
helm history myapp --namespace production
```

## Library Charts

```yaml
# Chart.yaml for library chart
apiVersion: v2
name: mylib
type: library
version: 1.0.0
```

```yaml
# templates/_deployment.tpl in library
{{- define "mylib.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "mylib.fullname" . }}
  labels:
    {{- include "mylib.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "mylib.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "mylib.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
{{- end }}
```

```yaml
# Using library chart
# Chart.yaml
dependencies:
  - name: mylib
    version: "1.x.x"
    repository: https://charts.example.com

# templates/deployment.yaml
{{- include "mylib.deployment" . }}
```

## 最佳实践

1. **版本控制**：为 charts 遵循语义化版本控制
2. **Values**：提供合理的默认值，允许覆盖
3. **文档**：在 README 中记录所有 values
4. **测试**：在 templates/tests/ 中包含测试
5. **助手**：使用 _helpers.tpl 进行可重用模板
6. **标签**：包含标准 Kubernetes 标签
7. **注解**：使用注解为元数据和工具
8. **Hooks**：为迁移、清理使用 hooks
9. **依赖**：固定依赖版本
10. **Schema**：使用 values.schema.json 验证 values
11. **在 CI 中使用 ct** 进行全面的 chart 测试
12. **生产升级前使用 helm-diff**
13. **使用 helm-secrets 或 sealed-secrets 加密 secrets
14. **为共享模式使用 library charts**
15. **推送到 OCI registries 以获得更好的制品管理**