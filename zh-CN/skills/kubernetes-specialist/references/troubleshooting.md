# Kubernetes 故障排除

## 基本 kubectl 命令

### Pod 检查

```bash
# Get pods with details
kubectl get pods -n production -o wide
kubectl get pods --all-namespaces
kubectl get pods --field-selector status.phase=Running
kubectl get pods --selector app=web-app

# Describe pod (shows events)
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production

# Get pod logs
kubectl logs web-app-7d5c8b9f4-xk2pm -n production
kubectl logs web-app-7d5c8b9f4-xk2pm -n production --previous  # Previous container
kubectl logs web-app-7d5c8b9f4-xk2pm -n production -c init-container
kubectl logs -f web-app-7d5c8b9f4-xk2pm -n production  # Follow logs
kubectl logs --tail=100 web-app-7d5c8b9f4-xk2pm -n production
kubectl logs --since=1h web-app-7d5c8b9f4-xk2pm -n production

# Get all pod logs from deployment
kubectl logs deployment/web-app -n production --all-containers=true

# Execute commands in pod
kubectl exec -it web-app-7d5c8b9f4-xk2pm -n production -- /bin/sh
kubectl exec web-app-7d5c8b9f4-xk2pm -n production -- env
kubectl exec web-app-7d5c8b9f4-xk2pm -n production -- cat /etc/config/app.yaml

# Copy files to/from pod
kubectl cp web-app-7d5c8b9f4-xk2pm:/app/logs/app.log ./app.log -n production
kubectl cp ./config.yaml web-app-7d5c8b9f4-xk2pm:/tmp/config.yaml -n production

# Port forward
kubectl port-forward web-app-7d5c8b9f4-xk2pm 8080:8080 -n production
kubectl port-forward service/web-app 8080:80 -n production
```

### Deployment 调试

```bash
# Check deployment status
kubectl get deployment web-app -n production
kubectl describe deployment web-app -n production
kubectl rollout status deployment/web-app -n production
kubectl rollout history deployment/web-app -n production

# Check replica sets
kubectl get rs -n production
kubectl describe rs web-app-7d5c8b9f4 -n production

# Scale deployment
kubectl scale deployment web-app --replicas=5 -n production

# Rollback deployment
kubectl rollout undo deployment/web-app -n production
kubectl rollout undo deployment/web-app --to-revision=2 -n production

# Restart deployment (recreate pods)
kubectl rollout restart deployment/web-app -n production
```

### Service 和网络调试

```bash
# Get services
kubectl get svc -n production
kubectl describe svc web-app -n production

# Get endpoints
kubectl get endpoints web-app -n production
kubectl describe endpoints web-app -n production

# Get ingress
kubectl get ingress -n production
kubectl describe ingress web-app -n production

# Get network policies
kubectl get networkpolicy -n production
kubectl describe networkpolicy frontend-to-backend -n production
```

### 资源和配置

```bash
# Get ConfigMaps and Secrets
kubectl get configmap -n production
kubectl describe configmap app-config -n production
kubectl get configmap app-config -n production -o yaml

kubectl get secret -n production
kubectl describe secret app-secrets -n production
kubectl get secret app-secrets -n production -o jsonpath='{.data.password}' | base64 -d

# Get PVCs and PVs
kubectl get pvc -n production
kubectl describe pvc database-pvc -n production
kubectl get pv

# Get events (sorted by timestamp)
kubectl get events -n production --sort-by='.lastTimestamp'
kubectl get events -n production --field-selector involvedObject.name=web-app-7d5c8b9f4-xk2pm
```

## 调试 Pod

### 临时调试容器

```bash
# Attach debug container to running pod
kubectl debug -it web-app-7d5c8b9f4-xk2pm -n production \
  --image=busybox:latest \
  --target=web-app

# Create copy of pod with debug tools
kubectl debug web-app-7d5c8b9f4-xk2pm -n production \
  -it \
  --image=ubuntu:latest \
  --share-processes \
  --copy-to=web-app-debug

# Debug with different image
kubectl debug web-app-7d5c8b9f4-xk2pm -n production \
  -it \
  --image=nicolaka/netshoot:latest \
  --target=web-app
```

### 节点上调试

```bash
# Create privileged pod on specific node
kubectl debug node/node-01 -it --image=ubuntu:latest

# Access node filesystem
kubectl debug node/node-01 -it --image=ubuntu:latest -- chroot /host
```

## 常见问题和解决方案

### 问题 1：Pod 处于 Pending 状态

```bash
# Check pod status and events
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production

# Common causes:
# 1. Insufficient resources
kubectl top nodes
kubectl describe nodes

# 2. PVC not bound
kubectl get pvc -n production
kubectl describe pvc database-pvc -n production

# 3. ImagePullBackOff
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production | grep -A 10 Events

# 4. Node selector/affinity issues
kubectl get pod web-app-7d5c8b9f4-xk2pm -n production -o yaml | grep -A 5 nodeSelector
```

### 问题 2：CrashLoopBackOff

```bash
# Check logs from crashed container
kubectl logs web-app-7d5c8b9f4-xk2pm -n production --previous

# Check if liveness probe is failing
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production | grep -A 10 "Liveness"

# Debug with different command
kubectl run debug-pod --image=myapp:latest -it --rm --restart=Never -- /bin/sh

# Check resource limits
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production | grep -A 10 "Limits"
```

### 问题 3：ImagePullBackOff

```bash
# Check image pull secret
kubectl get secret registry-credentials -n production -o yaml

# Test image pull manually
kubectl run test-pull --image=myregistry.io/myapp:v1.2.0 \
  --image-pull-policy=Always \
  --restart=Never \
  -n production

# Create/update image pull secret
kubectl create secret docker-registry registry-credentials \
  --docker-server=myregistry.io \
  --docker-username=myuser \
  --docker-password=mypassword \
  --docker-email=user@example.com \
  -n production
```

### 问题 4：Service 不可访问

```bash
# Check service endpoints
kubectl get endpoints web-app -n production
kubectl describe endpoints web-app -n production

# Verify pod labels match service selector
kubectl get pod web-app-7d5c8b9f4-xk2pm -n production --show-labels
kubectl get service web-app -n production -o yaml | grep -A 3 selector

# Test service connectivity from debug pod
kubectl run debug --image=nicolaka/netshoot:latest -it --rm -n production -- bash
# Inside pod:
curl http://web-app.production.svc.cluster.local
nslookup web-app.production.svc.cluster.local
telnet web-app.production.svc.cluster.local 80
```

### 问题 5：DNS 解析问题

```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns

# Test DNS resolution
kubectl run dnsutils --image=tutum/dnsutils -it --rm -- bash
# Inside pod:
nslookup kubernetes.default
nslookup web-app.production.svc.cluster.local
dig web-app.production.svc.cluster.local

# Check DNS config in pod
kubectl exec web-app-7d5c8b9f4-xk2pm -n production -- cat /etc/resolv.conf
```

### 问题 6：NetworkPolicy 阻止流量

```bash
# List network policies
kubectl get networkpolicy -n production
kubectl describe networkpolicy default-deny-all -n production

# Test connectivity
kubectl run test-connectivity --image=nicolaka/netshoot:latest -it --rm -n production -- bash
# Inside pod:
curl -v http://web-app:80
nc -zv web-app 80

# Temporarily allow all traffic (testing only)
kubectl delete networkpolicy --all -n production
```

### 问题 7：高资源使用

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n production
kubectl top pod web-app-7d5c8b9f4-xk2pm -n production --containers

# Check resource requests and limits
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production | grep -A 10 "Limits"

# Get pods sorted by CPU/memory usage
kubectl top pods -n production --sort-by=cpu
kubectl top pods -n production --sort-by=memory

# Check node capacity
kubectl describe node node-01 | grep -A 10 "Allocated resources"
```

### 问题 8：PersistentVolumeClaim 问题

```bash
# Check PVC status
kubectl get pvc -n production
kubectl describe pvc database-pvc -n production

# Check PV status
kubectl get pv
kubectl describe pv pvc-abc123

# Check storage class
kubectl get storageclass
kubectl describe storageclass fast-ssd

# Events related to PVC
kubectl get events -n production --field-selector involvedObject.name=database-pvc
```

## 高级调试

### API Server 调试

```bash
# Enable verbose output
kubectl get pods -n production -v=9

# Check API server logs (on master node)
journalctl -u kube-apiserver -f

# Check cluster info
kubectl cluster-info
kubectl cluster-info dump > cluster-dump.txt
```

### RBAC 调试

```bash
# Check if ServiceAccount can perform action
kubectl auth can-i get pods --as=system:serviceaccount:production:web-app-sa -n production

# List permissions for ServiceAccount
kubectl describe sa web-app-sa -n production
kubectl describe role web-app-role -n production
kubectl describe rolebinding web-app-rolebinding -n production

# Check all permissions
kubectl auth can-i --list --as=system:serviceaccount:production:web-app-sa -n production
```

### 性能调试

```bash
# Get resource metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods

# Check pod overhead
kubectl get pod web-app-7d5c8b9f4-xk2pm -n production -o json | jq '.spec.overhead'

# Check priority classes
kubectl get priorityclasses
kubectl describe priorityclass high-priority
```

## 诊断工具

### 网络工具容器

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: netshoot
  namespace: production
spec:
  containers:
  - name: netshoot
    image: nicolaka/netshoot:latest
    command: ["/bin/sleep", "3600"]
  restartPolicy: Never
```

### 数据库客户端容器

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: postgres-client
  namespace: production
spec:
  containers:
  - name: postgres
    image: postgres:15-alpine
    command: ["/bin/sleep", "3600"]
    env:
    - name: PGHOST
      value: postgres-service
    - name: PGUSER
      value: myapp
    - name: PGPASSWORD
      valueFrom:
        secretKeyRef:
          name: postgres-secrets
          key: password
  restartPolicy: Never
```

## 快速参考

### Pod 状态
- **Pending**：等待调度
- **ContainerCreating**：拉取镜像 / 创建容器
- **Running**：Pod 正在运行
- **Succeeded**：所有容器成功退出
- **Failed**：至少一个容器失败
- **CrashLoopBackOff**：容器不断崩溃
- **ImagePullBackOff**：无法拉取镜像
- **ErrImagePull**：镜像拉取错误
- **Unknown**：无法获取 pod 状态

### 常见退出代码
- **0**：成功
- **1**：一般错误
- **137**：SIGKILL（OOMKilled - 内存不足）
- **139**：SIGSEGV（段错误）
- **143**：SIGTERM（优雅终止）

## 最佳实践

1. **日志**：始终先用 `kubectl logs` 检查日志
2. **事件**：使用 `kubectl describe` 查看事件
3. **标签**：使用一致的标签以便于调试
4. **资源**：设置适当的请求和限制
5. **健康检查**：实现适当的 liveness 和 readiness 探针
6. **监控**：设置全面的监控和警报
7. **调试工具**：保持调试容器就绪
8. **文档**：记录常见问题和解决方案