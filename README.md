<img width="1515" height="813" alt="image" src="https://github.com/user-attachments/assets/c9e5fde3-0bd4-4784-9291-6dc44387a87e" />

# 🚀 Automation Platform — Production-Grade DevOps on AWS EKS

[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.30-blue?logo=kubernetes)](https://kubernetes.io)
[![Terraform](https://img.shields.io/badge/Terraform-1.7-purple?logo=terraform)](https://terraform.io)
[![AWS](https://img.shields.io/badge/AWS-EKS-orange?logo=amazonaws)](https://aws.amazon.com)
[![ArgoCD](https://img.shields.io/badge/GitOps-ArgoCD-red?logo=argo)](https://argoproj.github.io)
[![Jenkins](https://img.shields.io/badge/CI-Jenkins-yellow?logo=jenkins)](https://jenkins.io)

A production-grade DevOps platform built on AWS EKS demonstrating end-to-end GitOps — from infrastructure provisioning via Terraform to automated deployments via ArgoCD, with full observability via Prometheus and Grafana.

---

## 📐 Architecture

```
Developer pushes code to GitHub
        ↓
Jenkins detects via webhook
        ↓
Builds Docker image (linux/amd64) → pushes to AWS ECR
        ↓
Updates image tag in Helm values.yaml → commits to GitHub
        ↓
ArgoCD detects values.yaml change → auto-syncs
        ↓
Deploys Helm chart to AWS EKS cluster
        ↓
Prometheus + Grafana monitors everything
```

### Infrastructure Architecture

```
AWS (ap-south-1)
└── VPC (10.0.0.0/16)
    ├── Public Subnet 1 (10.0.1.0/24) — ap-south-1a  → Load Balancer
    ├── Public Subnet 2 (10.0.2.0/24) — ap-south-1b  → Load Balancer
    ├── Private Subnet 1 (10.0.3.0/24) — ap-south-1a → EKS Worker Nodes
    ├── Private Subnet 2 (10.0.4.0/24) — ap-south-1b → EKS Worker Nodes
    ├── Internet Gateway
    ├── NAT Gateway (outbound for private subnets)
    └── EKS Cluster (1.30)
        ├── Node Group (2x t3.small — across 2 AZs)
        └── ECR (private container registry)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Infrastructure** | Terraform, AWS EKS, VPC, ECR, IAM |
| **Container** | Docker (linux/amd64) |
| **Orchestration** | Kubernetes 1.30, Helm |
| **CI Pipeline** | Jenkins (Docker socket + AWS CLI) |
| **CD / GitOps** | ArgoCD |
| **Monitoring** | Prometheus, Grafana, Alertmanager |
| **App** | Python FastAPI |
| **Registry** | AWS ECR (private) |

---

## 📁 Project Structure

```
automation-platform/
├── app/                          # FastAPI application
│   ├── main.py
│   └── requirements.txt
├── docker/
│   └── Dockerfile                # Multi-stage, linux/amd64
├── helm/
│   └── automation-platform-chart/
│       ├── Chart.yaml
│       ├── values.yaml           # Jenkins updates image tag here
│       └── templates/
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── configmap.yaml
│           ├── secret.yaml
│           ├── hpa.yaml
│           └── ingress.yaml
├── k8s/                          # Raw K8s manifests (dev/testing)
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── secret.yaml
├── jenkins/
│   ├── Dockerfile                # Custom Jenkins with AWS CLI + kubectl
│   └── Jenkinsfile               # 4-stage CI pipeline
├── terraform/
│   ├── modules/
│   │   ├── vpc/                  # VPC, subnets, IGW, NAT Gateway
│   │   ├── eks/                  # EKS cluster, node group, IAM roles
│   │   └── ecr/                  # ECR repository + lifecycle policy
│   └── environments/
│       └── dev/
│           └── main.tf           # Entry point — calls all modules
└── README.md
```

---

## ⚙️ Infrastructure (Terraform)

### Modules

**VPC Module** — creates:
- VPC with DNS hostnames enabled (required for EKS)
- 2 public + 2 private subnets across 2 AZs
- Internet Gateway for public subnets
- NAT Gateway for private subnet outbound access
- Route tables with proper associations
- ELB tags on subnets for AWS Load Balancer Controller

**EKS Module** — creates:
- EKS control plane (v1.30) with private + public endpoint access
- IAM role for control plane (`AmazonEKSClusterPolicy`)
- Managed node group (2x t3.small in private subnets)
- IAM role for worker nodes with 3 policies:
  - `AmazonEKSWorkerNodePolicy`
  - `AmazonEKS_CNI_Policy`
  - `AmazonEC2ContainerRegistryReadOnly`

**ECR Module** — creates:
- Private container registry
- Lifecycle policy (keep last 10 images)
- Image scanning on push (`scan_on_push = true`)

### Deploy Infrastructure

```bash
cd terraform/environments/dev

# Initialize
terraform init

# Preview
terraform plan

# Apply
terraform apply

# Connect kubectl to EKS
aws eks update-kubeconfig --region ap-south-1 --name automation-platform-cluster

# Verify
kubectl get nodes

# Destroy when done (saves cost)
terraform destroy
```

---

## 🔄 CI/CD Pipeline (Jenkins + ArgoCD)

### Jenkins Pipeline — 4 Stages

```groovy
Stage 1: Build Docker Image
→ docker build --platform linux/amd64 -t ECR_URL:v${BUILD_NUMBER}

Stage 2: Push to ECR
→ aws ecr get-login-password | docker login
→ docker push ECR_URL:v${BUILD_NUMBER}

Stage 3: Update Helm Chart
→ sed -i "s/tag:.*/tag: v${BUILD_NUMBER}/" helm/values.yaml
→ git commit + push to GitHub

Stage 4: Verify Deployment
→ kubectl rollout status deployment/automation-platform
```

### GitOps Flow (ArgoCD)

```
Jenkins updates values.yaml → pushes to GitHub
        ↓
ArgoCD polls GitHub every 3 minutes
        ↓
Detects values.yaml change
        ↓
Runs helm upgrade on EKS cluster
        ↓
Kubernetes rolling update (zero downtime)
        ↓
Old pods terminated only after new pods are Ready
```

**Why GitOps over direct deployment:**
- GitHub = single source of truth
- Any manual cluster changes auto-reverted
- Full audit trail via Git history
- Rollback = `git revert` → auto-deployed

---

## 📦 Kubernetes Configuration

### Deployment

- **Replicas:** 2 (spread across 2 AZs)
- **Image:** AWS ECR private registry
- **Auth:** IAM role on worker nodes (no credentials in pod spec)
- **Config:** Environment variables from ConfigMap
- **Secrets:** Mounted from Kubernetes Secret

### HPA (Auto Scaling)

```yaml
minReplicas: 2
maxReplicas: 5
targetCPUUtilizationPercentage: 70
```

Pods scale 2→5 when CPU exceeds 70% of requested CPU.

### Health Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10    # wait before first check
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## 📊 Monitoring (Prometheus + Grafana)

### Install

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

**Installs automatically:**
- Prometheus (metrics collection)
- Grafana (visualization)
- Alertmanager (routing alerts)
- Node Exporter (DaemonSet — per-node metrics)
- kube-state-metrics (Kubernetes object states)

### Access Grafana

```bash
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
# Open: http://localhost:3000
# Username: admin
# Password: kubectl get secret monitoring-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d
```

### Key Dashboards

- **Kubernetes / Compute Resources / Cluster** — overall health
- **Kubernetes / Compute Resources / Namespace** — per-namespace metrics
- **Kubernetes / Compute Resources / Pod** — per-pod CPU/memory
- **Node Exporter / Full** — node-level metrics

---

## 🚀 Deploy Application

### Prerequisites

- AWS CLI configured (`aws configure`)
- kubectl installed
- Helm installed
- Terraform installed
- EKS cluster running (via Terraform)

### Deploy via ArgoCD (GitOps)

```bash
# Install ArgoCD on EKS
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**ArgoCD App config:**
- Repository: `https://github.com/pavichan55/automation-platform`
- Path: `helm/automation-platform-chart`
- Cluster: `https://kubernetes.default.svc`
- Namespace: `automation-platform`
- Sync: Automatic

### Deploy via kubectl (manual)

```bash
kubectl create namespace automation-platform
kubectl apply -f k8s/ -n automation-platform
kubectl get pods -n automation-platform
```

### Access Application

```bash
kubectl port-forward svc/automation-platform-service 8080:80 -n automation-platform
# Open: http://localhost:8080
```

---

## 🔐 Security Decisions

| Decision | Reason |
|---|---|
| Worker nodes in private subnets | Not directly accessible from internet |
| ECR over DockerHub | Private registry, IAM auth, no rate limits |
| IAM role on nodes (not credentials) | Temporary tokens, no long-lived secrets |
| Separate IAM roles (control plane vs nodes) | Least privilege — blast radius reduction |
| `scan_on_push = true` on ECR | Catch vulnerabilities before deployment |
| `linux/amd64` platform flag | Matches EKS node architecture |

---

## 💰 Cost Management

EKS is not free. Daily cost when running:

| Resource | Cost/hr | Daily (4hrs) |
|---|---|---|
| EKS Control Plane | $0.10 | ~$0.40 |
| 2x t3.small nodes | $0.02 each | ~$0.16 |
| NAT Gateway | $0.045 | ~$0.18 |
| **Total** | | **~$0.74/day** |

**Always destroy when not in use:**
```bash
terraform destroy
```

---

## 🐛 Key Debugging Lessons

### 1. ImagePullBackOff on EKS
**Problem:** Image name `automation-platform:v3` — no registry prefix.
**Fix:** Use full ECR URI: `251522454642.dkr.ecr.ap-south-1.amazonaws.com/automation-platform:v21`

### 2. Platform mismatch
**Problem:** Image built on Windows, EKS runs linux/amd64.
**Fix:** `docker build --platform linux/amd64 ...`

### 3. EKS node group AMI not supported
**Problem:** K8s 1.29 AMI not available in ap-south-1.
**Fix:** Upgrade to 1.30 — `terraform destroy` then `terraform apply` with new version.

### 4. NodePort on ClusterIP service
**Problem:** `nodePort` field not allowed with `ClusterIP` type.
**Fix:** Remove `nodePort` field when using `ClusterIP`.

---

## 📋 Prerequisites

```bash
# Verify tools
terraform --version    # >= 1.7
kubectl version        # >= 1.28
helm version           # >= 3.0
aws --version          # >= 2.0
docker --version       # >= 24.0

# AWS credentials
aws configure
aws sts get-caller-identity
```

---

## 👤 Author

**Pavithran Chandrasekaran**
Senior DevOps & Automation Engineer
CKA · CKAD · AWS Solutions Architect Associate

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/pavithran-c)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?logo=github)](https://github.com/pavichan55)

---

*Built with real AWS infrastructure. Not a tutorial project.*
