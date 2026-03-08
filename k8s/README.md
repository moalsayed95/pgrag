# Deploy PG-RAG on Minikube

## What is Minikube?

**Minikube** runs a complete, single-node Kubernetes cluster on your laptop. It gives you the same orchestration layer used in production (EKS, GKE, AKS) — but locally and for free. Perfect for learning, developing, and testing before deploying to the cloud.

**kubectl** is the CLI you use to talk to any Kubernetes cluster — local or remote. Think of Minikube as the cluster and kubectl as the remote control.

---

## Prerequisites

- [Docker Desktop](https://docs.docker.com/get-docker/) (macOS / Windows) or Docker Engine (Linux)
- An [OpenAI API key](https://platform.openai.com/api-keys)

---

## macOS

### Install

```bash
brew install minikube kubectl
```

### Verify

```bash
minikube version
kubectl version --client
```

### Start the cluster

```bash
minikube start
```

### Build images inside Minikube

```bash
eval $(minikube docker-env)
docker build -t pgrag-backend  ./app/backend
docker build -t pgrag-frontend ./app/frontend
```

### Add your OpenAI API key

```bash
cp k8s/secret.example.yaml k8s/secret.yaml
```

Open `k8s/secret.yaml` and replace `REPLACE_WITH_YOUR_OPENAI_API_KEY` with your real key. This file is gitignored — it will never be committed.

### Deploy

```bash
kubectl apply -f k8s/
kubectl get pods -w          # wait until all 3 pods show Running 1/1
```

### Open the app

```bash
minikube service frontend
```

### Tear down

```bash
kubectl delete -f k8s/
minikube stop                # pause (preserves state)
minikube delete              # destroy entirely
```

---

## Windows

### Install (pick one)

**Option A — Chocolatey:**

```powershell
choco install minikube kubernetes-cli
```

**Option B — winget:**

```powershell
winget install Kubernetes.minikube
winget install Kubernetes.kubectl
```

### Verify

```powershell
minikube version
kubectl version --client
```

### Start the cluster

```powershell
minikube start
```

### Build images inside Minikube

```powershell
& minikube docker-env --shell powershell | Invoke-Expression
docker build -t pgrag-backend  ./app/backend
docker build -t pgrag-frontend ./app/frontend
```

### Add your OpenAI API key

```powershell
Copy-Item k8s/secret.example.yaml k8s/secret.yaml
```

Open `k8s/secret.yaml` and replace `REPLACE_WITH_YOUR_OPENAI_API_KEY` with your real key. This file is gitignored — it will never be committed.

### Deploy

```powershell
kubectl apply -f k8s/
kubectl get pods -w          # wait until all 3 pods show Running 1/1
```

### Open the app

```powershell
minikube service frontend
```

### Tear down

```powershell
kubectl delete -f k8s/
minikube stop                # pause (preserves state)
minikube delete              # destroy entirely
```

---

## Linux

### Install

```bash
# minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

# kubectl
sudo snap install kubectl --classic
```

### Verify

```bash
minikube version
kubectl version --client
```

### Start the cluster

```bash
minikube start
```

### Build images inside Minikube

```bash
eval $(minikube docker-env)
docker build -t pgrag-backend  ./app/backend
docker build -t pgrag-frontend ./app/frontend
```

### Add your OpenAI API key

```bash
cp k8s/secret.example.yaml k8s/secret.yaml
```

Open `k8s/secret.yaml` and replace `REPLACE_WITH_YOUR_OPENAI_API_KEY` with your real key. This file is gitignored — it will never be committed.

### Deploy

```bash
kubectl apply -f k8s/
kubectl get pods -w          # wait until all 3 pods show Running 1/1
```

### Open the app

```bash
minikube service frontend
```

### Tear down

```bash
kubectl delete -f k8s/
minikube stop                # pause (preserves state)
minikube delete              # destroy entirely
```

---

## Useful Commands

| Command | Purpose |
|---------|---------|
| `kubectl get pods` | List running pods |
| `kubectl get svc` | List services and ports |
| `kubectl logs deploy/backend` | View backend logs |
| `kubectl describe pod <name>` | Debug a pod |
| `minikube dashboard` | Open the K8s web UI |
