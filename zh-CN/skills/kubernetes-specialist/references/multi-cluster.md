# 多集群管理

---

## Cluster API

### 安装

```bash
# Install clusterctl CLI
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.6.0/clusterctl-linux-amd64 -o clusterctl
chmod +x clusterctl && sudo mv clusterctl /usr/local/bin/

# Initialize management cluster with AWS provider
clusterctl init --infrastructure aws

# Initialize with multiple providers
clusterctl init \
  --infrastructure aws,azure \
  --control-plane kubeadm \
  --bootstrap kubeadm
```

### 集群定义

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: production-cluster
  namespace: clusters
spec:
  clusterNetwork:
    pods:
      cidrBlocks: ["192.168.0.0/16"]
    services:
      cidrBlocks: ["10.96.0.0/12"]
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: production-control-plane
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
    kind: AWSCluster
    name: production-cluster
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
kind: AWSCluster
metadata:
  name: production-cluster
  namespace: clusters
spec:
  region: us-west-2
  sshKeyName: production-key
  network:
    vpc:
      cidrBlock: 10.0.0.0/16
    subnets:
      - availabilityZone: us-west-2a
        cidrBlock: 10.0.1.0/24
        isPublic: true
      - availabilityZone: us-west-2b
        cidrBlock: 10.0.2.0/24
        isPublic: true
```

### 控制平面

```yaml
apiVersion: controlplane.cluster.x-k8s.io/v1beta1
kind: KubeadmControlPlane
metadata:
  name: production-control-plane
  namespace: clusters
spec:
  replicas: 3
  version: v1.28.0
  machineTemplate:
    infrastructureRef:
      apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
      kind: AWSMachineTemplate
      name: production-control-plane
  kubeadmConfigSpec:
    clusterConfiguration:
      apiServer:
        extraArgs:
          cloud-provider: aws
      controllerManager:
        extraArgs:
          cloud-provider: aws
    initConfiguration:
      nodeRegistration:
        kubeletExtraArgs:
          cloud-provider: aws
    joinConfiguration:
      nodeRegistration:
        kubeletExtraArgs:
          cloud-provider: aws
```

### Machine 部署（工作节点）

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: production-workers
  namespace: clusters
spec:
  clusterName: production-cluster
  replicas: 5
  selector:
    matchLabels:
      cluster.x-k8s.io/cluster-name: production-cluster
  template:
    spec:
      clusterName: production-cluster
      version: v1.28.0
      bootstrap:
        configRef:
          apiVersion: bootstrap.cluster.x-k8s.io/v1beta1
          kind: KubeadmConfigTemplate
          name: production-workers
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
        kind: AWSMachineTemplate
        name: production-workers
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
kind: AWSMachineTemplate
metadata:
  name: production-workers
  namespace: clusters
spec:
  template:
    spec:
      instanceType: m5.xlarge
      iamInstanceProfile: nodes.cluster-api-provider-aws.sigs.k8s.io
      sshKeyName: production-key
      rootVolume:
        size: 100
        type: gp3
```

## 跨集群网络

### Submariner 安装

```bash
# Install subctl
curl -Ls https://get.submariner.io | bash

# Join clusters to broker
subctl deploy-broker --kubeconfig kubeconfig-cluster1

# Join workload clusters
subctl join --kubeconfig kubeconfig-cluster1 broker-info.subm --clusterid cluster1
subctl join --kubeconfig kubeconfig-cluster2 broker-info.subm --clusterid cluster2

# Verify connectivity
subctl show all
```

### ServiceExport/ServiceImport

```yaml
# Export service from cluster1
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceExport
metadata:
  name: myapp
  namespace: production
---
# Service is auto-imported to other clusters as:
# myapp.production.svc.clusterset.local
```

### Cilium Cluster Mesh

```bash
# Enable cluster mesh on both clusters
cilium clustermesh enable --context cluster1
cilium clustermesh enable --context cluster2

# Connect clusters
cilium clustermesh connect --context cluster1 --destination-context cluster2

# Verify
cilium clustermesh status --context cluster1
```

```yaml
# Global service accessible from all clusters
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: production
  annotations:
    service.cilium.io/global: "true"
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
    - port: 80
```

## 多集群 DNS

### ExternalDNS with Route53

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: external-dns
  namespace: kube-system
spec:
  template:
    spec:
      containers:
        - name: external-dns
          image: k8s.gcr.io/external-dns/external-dns:v0.14.0
          args:
            - --source=service
            - --source=ingress
            - --provider=aws
            - --aws-zone-type=public
            - --registry=txt
            - --txt-owner-id=my-cluster
            - --domain-filter=example.com
```

### CoreDNS Federation

```yaml
# Forward queries for other clusters
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           fallthrough in-addr.arpa ip6.arpa
        }
        # Forward to cluster2 DNS
        cluster2.local:53 {
            forward . 10.0.0.10
        }
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
```

## 工作负载分发

### Kubernetes Federation v2

```yaml
apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: myapp
  namespace: production
spec:
  template:
    metadata:
      labels:
        app: myapp
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: myapp
      template:
        metadata:
          labels:
            app: myapp
        spec:
          containers:
            - name: myapp
              image: myregistry.io/myapp:v1.0.0
  placement:
    clusters:
      - name: cluster-us-west
      - name: cluster-us-east
      - name: cluster-eu-west
  overrides:
    - clusterName: cluster-us-west
      clusterOverrides:
        - path: "/spec/replicas"
          value: 5
    - clusterName: cluster-eu-west
      clusterOverrides:
        - path: "/spec/replicas"
          value: 3
```

### ArgoCD Multi-Cluster

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-global
  namespace: argocd
spec:
  generators:
    - clusters:
        selector:
          matchLabels:
            environment: production
  template:
    metadata:
      name: 'myapp-{{name}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/myapp-manifests.git
        targetRevision: main
        path: overlays/production
      destination:
        server: '{{server}}'
        namespace: production
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

## 灾难恢复

### Velero 备份配置

```bash
# Install Velero with S3
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero-backups \
  --backup-location-config region=us-west-2 \
  --snapshot-location-config region=us-west-2 \
  --secret-file ./credentials-velero
```

```yaml
# Scheduled backup
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
      - production
      - staging
    excludedResources:
      - events
    storageLocation: default
    volumeSnapshotLocations:
      - default
    ttl: 720h  # 30 days
---
# Restore to different cluster
apiVersion: velero.io/v1
kind: Restore
metadata:
  name: restore-production
  namespace: velero
spec:
  backupName: daily-backup-20240115
  includedNamespaces:
    - production
  restorePVs: true
  preserveNodePorts: true
```

### 主动-被动故障转移

```yaml
# Primary cluster ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.example.com
    external-dns.alpha.kubernetes.io/set-identifier: primary
    external-dns.alpha.kubernetes.io/aws-weight: "100"
spec:
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 80
---
# Secondary cluster ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.example.com
    external-dns.alpha.kubernetes.io/set-identifier: secondary
    external-dns.alpha.kubernetes.io/aws-weight: "0"
spec:
  rules:
    - host: myapp.example.com
      # ... same backend config
```

## 集中式管理工具

### Rancher 设置

```bash
# Install Rancher with Helm
helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
helm install rancher rancher-stable/rancher \
  --namespace cattle-system \
  --create-namespace \
  --set hostname=rancher.example.com \
  --set bootstrapPassword=admin
```

### Kubeconfig 管理

```yaml
# Merge multiple kubeconfigs
# ~/.kube/config
apiVersion: v1
kind: Config
clusters:
  - name: cluster-us-west
    cluster:
      server: https://cluster-us-west.example.com
      certificate-authority-data: ...
  - name: cluster-us-east
    cluster:
      server: https://cluster-us-east.example.com
      certificate-authority-data: ...
contexts:
  - name: us-west
    context:
      cluster: cluster-us-west
      user: admin-us-west
      namespace: default
  - name: us-east
    context:
      cluster: cluster-us-east
      user: admin-us-east
      namespace: default
users:
  - name: admin-us-west
    user:
      token: ...
  - name: admin-us-east
    user:
      token: ...
current-context: us-west
```

```bash
# Switch between clusters
kubectl config use-context us-west
kubectl config use-context us-east

# Run command against specific cluster
kubectl --context=us-west get pods
kubectl --context=us-east get pods

# Use kubectx for easier switching
kubectx us-west
```

## 最佳实践

1. **使用 Cluster API** 进行声明式集群生命周期管理
2. **实现 service mesh** 以实现安全的跨集群通信
3. **设置基于 DNS 的路由** 以实现全局服务发现
4. **使用 Velero** 跨集群配置自动化备份
5. **使用 GitOps**（ArgoCD/Flux）进行一致的多集群部署
6. **跨集群一致地实现网络策略**
7. **使用跨集群指标和日志进行集中可观测性**
8. **定期测试故障转移程序**
9. **跨集群一致地使用命名空间**
10. **记录集群拓扑和依赖关系**
11. **实现具有跨集群访问模式的 RBAC**
12. **从集中式仪表板监控集群健康**