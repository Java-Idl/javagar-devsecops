# 🛠️ Technology Stack & Security Tooling Matrix

**Project**: DevSecOps Pipeline & Infrastructure as Code (IaC) Security  
**Repository**: [`Java-Idl/javagar-devsecops`](https://github.com/Java-Idl/javagar-devsecops)  
**Problem Statement**: PS-10 (DevSecOps Pipeline & IaC Security)

---

## 📌 Architecture & Lifecycle Mapping Overview

```
Phase 1: Shift-Left SAST & IaC Linting (Pre-commit, Bandit, Semgrep, Checkov, cfn-lint)
Phase 2: CI/CD Pipeline & SCA Gate (CodePipeline, CodeBuild, Trivy, Docker)
Phase 3: Registry, Cryptographic Signing & Governance (ECR, AWS Signer, Cosign, IAM Permission Boundary)
Phase 4: Hardened Runtime Deployment & CIS Audit (ECS, Falco, Prowler)
Scheduled: Continuous Rescan & Re-evaluation (Amazon EventBridge, Trivy, Prowler)
```

---

## 1. 🔍 Shift-Left Security & Static Analysis (SAST)

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **Pre-commit** | Git Hook Orchestrator (`v3.x`) | Enforces local client-side security checks before code can be committed to Git. | [`.pre-commit-config.yaml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/.pre-commit-config.yaml) |
| **Bandit** | Python SAST Analyzer | Scans Python code AST for common security flaws (SQL injection, hardcoded secrets, unsafe deserialization, shell injection). | [`.github/workflows/javagar-sast.yml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/.github/workflows/javagar-sast.yml) |
| **Semgrep** | Semantic SAST Engine (`OSS`) | Polyglot semantic rule scanner matching OWASP Top 10, credential leaks, and CI security patterns. | [`.github/workflows/javagar-sast.yml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/.github/workflows/javagar-sast.yml) |
| **Checkov** | IaC Security Scanner (Prisma Cloud) | Evaluates CloudFormation and Terraform for misconfigurations (open security groups, unencrypted S3 buckets, wildcard IAM). | [`.pre-commit-config.yaml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/.pre-commit-config.yaml) |
| **cfn-lint** | CloudFormation Linter (`v1.x`) | Validates CloudFormation templates against the AWS CloudFormation Resource Specification. | [`.pre-commit-config.yaml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/.pre-commit-config.yaml) |

---

## 2. 🛡️ Software Composition Analysis (SCA) & Container Security

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **Trivy** | Container & Dependency SCA (Aqua Security) | Scans base images and dependencies for known CVEs. Enforces blocking gate (`--exit-code 1 --severity HIGH,CRITICAL`). | [`buildspec.yml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/buildspec.yml), [`.github/workflows/javagar-trivy.yml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/.github/workflows/javagar-trivy.yml) |
| **Docker** | Container Engine (`v29.8`) | Multi-stage Dockerfile packaging the Python Flask microservice with hardened runtime security and stripped build tools. | [`app/Dockerfile`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/app/Dockerfile) |
| **Amazon ECR** | Container Registry (Private) | Stores container images with **Tag Immutability** (`IMMUTABLE`) and **Scan-on-Push** (`BASIC` scan) enabled. | Repository: `javagar-app` |

---

## 3. ✍️ Cryptographic Supply Chain Security & Artifact Signing

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **Sigstore Cosign** | OCI Container Signing Tool (`v2.4.1`) | Generates ECDSA key pairs, signs image digests directly into Amazon ECR, and verifies signatures before deployment. | [`infra/keys/javagar-cosign.pub`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/infra/keys/javagar-cosign.pub) |
| **AWS Signer** | Native Cloud Code Signing Service | Managed signing profile configured with `Notation-OCI-SHA384-ECDSA` for container registries. | Profile: `javagar_signing_profile` |

---

## 4. ☁️ CI/CD Pipeline & Orchestration

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **GitHub** | Version Control & Repository Hosting | Central Git repository hosting application code, IaC, workflows, and branch protection rules. | `Java-Idl/javagar-devsecops` |
| **GitHub Actions** | CI Automation Platform | Automates pull request and push workflows for SAST scanning (`javagar-sast-pr`) and Trivy SCA gates (`javagar-trivy-scan`). | [`.github/workflows/`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/.github/workflows) |
| **AWS CodePipeline** | Managed CI/CD Orchestration (`V2`) | Pipeline triggering on GitHub commits and executing the automated build and scan stages. | [`infra/pipeline/javagar-pipeline.json`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/infra/pipeline/javagar-pipeline.json) |
| **AWS CodeBuild** | Serverless Build Service | Executes builds inside isolated Linux containers (`aws/codebuild/standard:7.0`) with Docker privileged mode enabled. | [`infra/codebuild/javagar-build-project.json`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/infra/codebuild/javagar-build-project.json) |
| **AWS CodeStar Connections** | Managed OAuth Connection | Connects AWS developer tools securely to GitHub without static access tokens. | Connection: `javagar-github-connection` |
| **Amazon S3** | Cloud Object Storage | Houses encrypted, versioned CI/CD pipeline artifact bundles with Public Access Block enabled. | Bucket: `javagar-pipeline-artifacts-024687770842` |

---

## 5. 🏗️ Infrastructure as Code (IaC) & Cloud Provisioning

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **AWS CloudFormation** | Native Declarative IaC | Deploys compliant cloud infrastructure including SSE-KMS encrypted S3 buckets, restricted Security Groups, and IAM roles. | [`infra/cfn/javagar-stack.yaml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/infra/cfn/javagar-stack.yaml) |
| **Terraform / OpenTofu** | Cloud-Agnostic IaC (`HCL`) | Declarative infrastructure specifications for multi-environment deployments. | [`infra/terraform/main.tf`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/infra/terraform/main.tf) |
| **AWS CLI** | Command Line Management (`v2.x`) | Programmatic provisioning, state inspection, and validation testing. | Used in local terminal & pipelines |

---

## 6. 🔒 Governance, Guardrails & Access Control

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **IAM Permission Boundary** | AWS IAM Preventive Guardrail | Enforces maximum allowable permissions: locks regions to `us-east-1`, denies unencrypted EBS, and mandates boundary inheritance on role creation. | [`infra/iam/javagar-permission-boundary.json`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/infra/iam/javagar-permission-boundary.json) |
| **Dual IAM Roles (ECS)** | IAM Privilege Separation | Separate **Task Execution Role** (ECR pull, CloudWatch write) vs **Task Role** (application runtime secret access). | Roles: `javagar-ecs-execution-role`, `javagar-ecs-task-role-dev` |

---

## 7. 🚀 Hardened Container Runtime & Detection

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **Amazon ECS** | Container Orchestration (EC2 / Fargate) | Manages container execution in cluster `javagar-cluster` using `awsvpc` network isolation. | Cluster: `javagar-cluster` |
| **Hardened Task Definition** | Container Security Specifications | Implements non-root user (`appuser`), `readonlyRootFilesystem: true`, `privileged: false`, dropped kernel capabilities (`ALL`), and digest-pinning. | [`infra/ecs/javagar-task-definition.json`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/infra/ecs/javagar-task-definition.json) |
| **Amazon CloudWatch Logs** | Observability & Logging | Centralized log group receiving microservice logs (`awslogs` driver). | Log Group: `/ecs/javagar-app` |
| **Falco** | Cloud-Native Runtime Security | Detection engine monitoring container syscalls for shell spawns, `/etc/shadow` reads, and IMDS (`169.254.169.254`) credential theft. | [`infra/falco/javagar-falco-rules.yaml`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/infra/falco/javagar-falco-rules.yaml) |

---

## 8. 📊 Compliance Auditing & Scheduled Continuous Controls

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **Prowler** | Cloud Security Assessment Tool (`v5.44.0`) | Executes automated CIS AWS Foundations Benchmark compliance scans across IAM, S3, ECR, and ECS. Exports HTML/CSV reports. | Directory: [`prowler-output/`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/prowler-output) |
| **Amazon EventBridge** | Event Bus & Cron Scheduler | Triggers nightly automated rescan of deployed image digests and scheduled security posture evaluations. | Rule: `javagar-nightly-rescan` (`cron(0 2 * * ? *)`) |

---

## 9. 💻 Languages, Runtimes & Package Managers

| Technology | Category / Version | Project Role & Implementation | Config / Key File |
|---|---|---|---|
| **Python** | Programming Language (`3.11`, `3.12`) | Microservice application logic, test fixtures, and security analysis scripts. | [`app/app.py`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/app/app.py) |
| **uv** | Python Package Manager & Tool Runner | High-performance dependency resolution, virtual environment management, and CLI tool runner (`uv tool run`). | [`.venv/`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/.venv) |
| **Flask** | Web Microservice Framework (`3.1.x`) | Lightweight HTTP REST service providing application endpoints and health check probes (`/health`). | [`app/requirements.txt`](file:///c:/Users/java/projects/sem7/dscc/end_sem_lab/app/requirements.txt) |
| **PowerShell** | Shell & Automation Environment | Terminal interface for executing local commands, AWS CLI operations, and verification tests on Windows. | Local terminal scripts |

---

## 📋 Technology Summary Table

| Category | Primary Technologies Used |
|---|---|
| **Shift-Left SAST** | Pre-commit, Bandit, Semgrep, Checkov, cfn-lint |
| **SCA & Containers** | Trivy, Docker, Amazon ECR |
| **Supply Chain Signing** | Sigstore Cosign, AWS Signer (Notation-OCI) |
| **CI/CD Orchestration** | GitHub Actions, AWS CodePipeline, AWS CodeBuild, CodeStar Connections |
| **Infrastructure as Code** | CloudFormation, Terraform, AWS CLI |
| **Governance & IAM** | IAM Permission Boundaries, Dual-Role Segregation |
| **Runtime & Detection** | Amazon ECS, Hardened Task Definition, CloudWatch Logs, Falco |
| **Compliance & Continuous** | Prowler (CIS AWS Benchmark), Amazon EventBridge |
| **Languages & Package Management** | Python 3.12, Flask, uv, PowerShell |
