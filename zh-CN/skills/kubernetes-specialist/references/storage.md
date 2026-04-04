# Kubernetes 存储

## StorageClass 定义

### AWS EBS (gp3)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789012:key/..."
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### GCE Persistent Disk (SSD)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd-gce
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### Azure Disk (Premium SSD)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd-azure
provisioner: disk.csi.azure.com
parameters:
  storageaccounttype: Premium_LRS
  kind: Managed
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### NFS 存储

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server.example.com
  share: /exports/kubernetes
volumeBindingMode: Immediate
reclaimPolicy: Retain
```

## PersistentVolume（静态供应）

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: legacy-database-pv
  labels:
    type: local
    app: legacy-db
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/data/legacy-db
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node-01
```

## PersistentVolumeClaim 模式

### 基本 PVC（动态供应）

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-pvc
  namespace: production
  labels:
    app: postgres
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 50Gi
```

### 共享存储（ReadWriteMany）

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-assets
  namespace: production
spec:
  accessModes:
  - ReadWriteMany
  storageClassName: nfs-storage
  resources:
    requests:
      storage: 100Gi
```

### Block Volume

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: block-storage
  namespace: production
spec:
  accessModes:
  - ReadWriteOnce
  volumeMode: Block
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
```

## 在 Pod 中使用 PVC

### 单个 PVC 挂载

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: database-pod
spec:
  containers:
  - name: postgres
    image: postgres:15
    volumeMounts:
    - name: data
      mountPath: /var/lib/postgresql/data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: database-pvc
```

### 多个 PVC

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
    - name: data
      mountPath: /data
    - name: logs
      mountPath: /var/log/app
    - name: shared
      mountPath: /shared
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-data-pvc
  - name: logs
    persistentVolumeClaim:
      claimName: app-logs-pvc
  - name: shared
    persistentVolumeClaim:
      claimName: shared-assets
```

## 使用 VolumeClaimTemplates 的 StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-cluster
  namespace: database
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        - name: config
          mountPath: /etc/postgresql
      volumes:
      - name: config
        configMap:
          name: postgres-config
  volumeClaimTemplates:
  - metadata:
      name: data
      labels:
        app: postgres
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

## 卷快照

### VolumeSnapshotClass

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete
parameters:
  encrypted: "true"
```

### VolumeSnapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: database-snapshot-20231214
  namespace: production
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: database-pvc
```

### 从快照恢复

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-restored
  namespace: production
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  dataSource:
    name: database-snapshot-20231214
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  resources:
    requests:
      storage: 50Gi
```

## 卷扩容

```yaml
# 1. Ensure StorageClass allows expansion
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
allowVolumeExpansion: true
# ... rest of config

---
# 2. Expand PVC by updating size
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi  # Increased from 50Gi
```

## EmptyDir 卷

### 内存支持的 EmptyDir

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cache-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: cache
      mountPath: /cache
  volumes:
  - name: cache
    emptyDir:
      medium: Memory
      sizeLimit: 1Gi
```

### 磁盘支持的 EmptyDir

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: worker-pod
spec:
  containers:
  - name: worker
    image: worker:latest
    volumeMounts:
    - name: scratch
      mountPath: /tmp/scratch
  volumes:
  - name: scratch
    emptyDir:
      sizeLimit: 10Gi
```

## ConfigMap 和 Secret 卷

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
    - name: config
      mountPath: /etc/config
      readOnly: true
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: app-config
      items:
      - key: app.yaml
        path: config.yaml
        mode: 0644
  - name: secrets
    secret:
      secretName: app-secrets
      defaultMode: 0400
      items:
      - key: db-password
        path: database/password
```

## Projected 卷

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: projected-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: combined
      mountPath: /combined
      readOnly: true
  volumes:
  - name: combined
    projected:
      sources:
      - secret:
          name: app-secrets
          items:
          - key: password
            path: secrets/password
      - configMap:
          name: app-config
          items:
          - key: config.yaml
            path: config/app.yaml
      - downwardAPI:
          items:
          - path: pod/labels
            fieldRef:
              fieldPath: metadata.labels
          - path: pod/annotations
            fieldRef:
              fieldPath: metadata.annotations
```

## CSI Driver 示例

### AWS EBS CSI Driver

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
    - name: data
      mountPath: /data
  volumes:
  - name: data
    csi:
      driver: ebs.csi.aws.com
      volumeAttributes:
        type: gp3
        iops: "3000"
        encrypted: "true"
```

### Secrets Store CSI Driver

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secrets-pod
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: secrets-store
      mountPath: /mnt/secrets
      readOnly: true
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: aws-secrets
```

## HostPath 卷（谨慎使用）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: host-data
      mountPath: /host-data
    securityContext:
      privileged: true
  volumes:
  - name: host-data
    hostPath:
      path: /data
      type: DirectoryOrCreate
```

## 最佳实践

1. **动态供应**：优先使用 StorageClasses 进行动态供应
2. **访问模式**：使用正确的访问模式（RWO 用于单节点，RWX 用于多节点）
3. **回收策略**：关键数据使用 Retain，临时数据使用 Delete
4. **备份**：定期快照和异地备份
5. **监控**：监控磁盘使用率和性能指标
6. **扩容**：在 StorageClass 中启用卷扩容
7. **性能**：为工作负载选择适当的存储类型
8. **安全**：静态加密和传输中加密
9. **限制**：对 emptyDir 卷设置大小限制
10. **标签**：标记 PVC 以便组织和备份策略