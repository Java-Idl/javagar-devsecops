# 🛡️ DevSecOps Pipeline & IaC Security: Experiment Presentation Guide

**Project Title**: Comprehensive DevSecOps Pipeline & Infrastructure as Code (IaC) Security  
**Problem Statement**: PS-10 (DevSecOps Pipeline & IaC Security)  
**Student / Resource Identifier**: `javagar`  
**Repository**: [`https://github.com/Java-Idl/javagar-devsecops`](https://github.com/Java-Idl/javagar-devsecops)  
**Target Cloud**: AWS (`us-east-1`, Account ID: `024687770842`)

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [End-to-End Architecture & Flow](#2-end-to-end-architecture--flow)
3. [Phase-by-Phase Deep Dive & Implementation](#3-phase-by-phase-deep-dive--implementation)
   * [Phase 1: Shift-Left Security & SAST](#phase-1-shift-left-security--sast)
   * [Phase 2: CI/CD Pipeline & Trivy SCA Gate](#phase-2-cicd-pipeline--trivy-sca-gate)
   * [Phase 3: Registry Hardening, Cryptographic Signing & Governance](#phase-3-registry-hardening-cryptographic-signing--governance)
   * [Phase 4: Hardened Runtime, Falco Detection & CIS Compliance](#phase-4-hardened-runtime-falco-detection--cis-compliance)
4. [Live Demonstration Script & Talking Points](#4-live-demonstration-script--talking-points)
5. [The 7 Validation Test Cases (Evidence Matrix)](#5-the-7-validation-test-cases-evidence-matrix)
6. [Evaluator Q&A / Defense Preparation](#6-evaluator-qa--defense-preparation)

---

## 1. Executive Summary & Problem Statement

### 🎯 Objective
Modern cloud-native deployments are vulnerable to **supply chain attacks**, **IaC configuration drift**, **vulnerable base dependencies**, and **over-permissive IAM roles**. 

This experiment implements a **Zero-Trust DevSecOps Lifecycle** that enforces security gates at every tier:
1. **Developer Desktop (Shift-Left)**: Pre-commit git hooks block vulnerable IaC from ever being committed.
2. **CI Pipeline (Automated Gating)**: Static Application Security Testing (SAST) and Software Composition Analysis (SCA) automatically abort builds on `HIGH`/`CRITICAL` findings.
3. **Registry & Supply Chain**: Immutability prevents tag-overwrite poisoning; Sigstore Cosign / AWS Signer cryptographically attests images before deployment.
4. **Cloud Runtime (Defense-in-Depth)**: Hardened ECS tasks (non-root, read-only filesystem, dropped capabilities) governed by an IAM Permission Boundary, with Falco runtime threat detection and Prowler CIS compliance auditing.

---

## 2. End-to-End Architecture & Flow

```
[Developer Machine]
       │
       ▼  (1) git commit -> Pre-commit Hook (Checkov + cfn-lint)
  [Local Gate]  --> Blocks unencrypted S3, open SG (22/3389), wildcard IAM
       │
       ▼  (2) git push -> GitHub Actions
[GitHub CI/CD]
   ├── Job 1: Bandit Python SAST (SQLi, secrets, deserialization)
   ├── Job 2: Semgrep Semantic SAST (OWASP Top 10, CI rules)
   ├── Job 3: Checkov IaC Security Gate
   └── Job 4: Trivy Container SCA Gate (Fails build if CVE >= HIGH)
       │
       ▼  (3) CodeStar Connection (OAuth)
[AWS CodePipeline] -> AWS CodeBuild (Isolated Docker-in-Docker Build)
       │
       ▼  (4) Push to Amazon ECR (tag immutability ON, basic scan ON)
[Amazon ECR: javagar-app]
       │
       ▼  (5) Sigstore Cosign / AWS Signer
[Signature OCI Artifact] -> sha256-...sig pushed to ECR
       │
       ▼  (6) Deployment Verification Gate (cosign verify --key pub)
  [Deploy Gate] --> ABORTS if image is unsigned or tampered
       │
       ▼  (7) Amazon ECS Deployment (governed by IAM Permission Boundary)
[Amazon ECS: javagar-cluster]
   ├── Task: javagar-app-task:1 (pinned to sha256 digest)
   ├── Security: readonlyRootFilesystem, non-root (appuser), cap-drop=ALL
   ├── Execution Role: javagar-ecs-execution-role (ECR pull, CloudWatch)
   └── Task Role: javagar-ecs-task-role-dev (least privilege, bounded)
       │
       ▼  (8) Runtime Monitoring & Compliance
[Runtime Defense]
   ├── Falco eBPF: Detects shells, /etc/shadow reads, IMDS (169.254.169.254) theft
   ├── Prowler: CIS AWS Benchmark 3.0 automated compliance audit
   └── EventBridge: javagar-nightly-rescan (Nightly Trivy rescan + audit)
```

---

## 3. Phase-by-Phase Deep Dive & Implementation

### Phase 1: Shift-Left Security & SAST
* **Problem**: Security vulnerabilities detected in production cost 100x more to remediate than those caught on the developer's laptop.
* **Implementation**:
  * **Pre-commit Hooks (`.pre-commit-config.yaml`)**: Runs `cfn-lint` and `checkov` on every local commit. Blocks commits with:
    * S3 buckets without Server-Side Encryption (`CKV_AWS_19`)
    * Security Groups open to `0.0.0.0/0` on port 22/3389 (`CKV_AWS_24`, `CKV_AWS_25`)
    * Wildcard IAM policies (`Action: "*"`, `Resource: "*"`) (`CKV_AWS_107`)
  * **GitHub Actions CI Gate (`.github/workflows/javagar-sast.yml`)**:
    * **Bandit**: Analyzes Python AST for hardcoded credentials (`B105`), SQL string concatenation (`B608`), and unsafe pickle deserialization (`B301`).
    * **Semgrep**: Scans code against OWASP Top-10, secrets leakage, and CI patterns.
    * **Checkov**: Validates production CloudFormation (`infra/cfn/javagar-stack.yaml`).
  * **Branch Protection**: Master branch mandates status checks to pass before any PR can merge.

---

### Phase 2: CI/CD Pipeline & Trivy SCA Gate
* **Problem**: 80%+ of container vulnerabilities originate in third-party base images and package dependencies, not first-party code.
* **Implementation**:
  * **AWS Native Pipeline**: AWS CodePipeline (`javagar-pipeline`) connected to GitHub via AWS CodeStar Connections (`javagar-github-connection`).
  * **CodeBuild Project (`javagar-build`)**: Ubuntu 7.0 build environment running `buildspec.yml` with Docker privileged mode.
  * **Trivy Vulnerability Gate**:
    ```bash
    trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed javagar-app:$TAG
    ```
  * **Observed Proof (Validation Test 2)**:
    1. *Negative Test*: Initial build with `python:3.11-alpine` caught **2 HIGH CVEs** (`CVE-2026-23949` in `jaraco.context`, `CVE-2026-24049` in `wheel`). Trivy exited with `code 1`, aborting the pipeline.
    2. *Positive Test*: Upgraded to `python:3.12-alpine`, stripped unused build metadata in multi-stage Dockerfile. Trivy returned **0 vulnerabilities**, and the pipeline passed.

---

### Phase 3: Registry Hardening, Cryptographic Signing & Governance
* **Problem**: Attackers can poison container registries by overwriting mutable tags (`latest`, `v1.0.0`) or deploying unauthorized/backdoored images.
* **Implementation**:
  * **ECR Immutability (`javagar-app`)**: Set to **`IMMUTABLE`**. Re-pushing an existing tag with modified content fails immediately with:
    `The image tag 'v1.0.0' already exists and cannot be overwritten`.
  * **Cryptographic Signing (Sigstore Cosign & AWS Signer)**:
    * Generated ECDSA key pair (`javagar-cosign.pub` / `javagar-cosign.key`).
    * Configured AWS Signer profile: `javagar_signing_profile` (`Notation-OCI-SHA384-ECDSA`).
    * Cosign signed the image digest (`sha256:8ecf0099...`) and pushed the signature OCI artifact (`sha256-...sig`) directly to Amazon ECR.
  * **Deploy Verification Gate**:
    * Verifies `cosign verify --key javagar-cosign.pub <digest>`.
    * Unsigned images fail with `Error: no signatures found` (`exit code 1`).
  * **IAM Permission Boundary (`javagar-permission-boundary`)**:
    * Enforces strict region boundary: Explicit Deny if `aws:RequestedRegion != us-east-1`.
    * Denies `ec2:RunInstances` / `ec2:CreateVolume` unless `ec2:Encrypted == true`.
    * **Anti-Escape Statements**: Requires any new role or user created to inherit `javagar-permission-boundary`. Denies boundary modification or deletion.

---

### Phase 4: Hardened Runtime, Falco Detection & CIS Compliance
* **Problem**: Even signed containers can be compromised at runtime via zero-days or stolen instance metadata credentials.
* **Implementation**:
  * **Hardened ECS Task (`javagar-app-task:1`)**:
    * Network Mode: `awsvpc` (Dedicated ENI, isolated network namespace).
    * `readonlyRootFilesystem: true` (Prevents malware persistence).
    * `privileged: false` and `capabilities.drop: ["ALL"]` (No root capabilities).
    * `user: "appuser"` (Runs as non-root UID 1000).
    * Pinned strictly by **immutable image digest**, never by tag.
  * **Dual IAM Role Separation**:
    * **Execution Role** (`javagar-ecs-execution-role`): Agent permissions only (ECR pull, CloudWatch logs).
    * **Task Role** (`javagar-ecs-task-role-dev`): Minimal runtime identity governed by Permission Boundary.
  * **Falco Runtime Threat Detection (`javagar-falco-rules.yaml`)**:
    * Rule 1: `javagar_terminal_shell_in_container` (Detects interactive shell execution).
    * Rule 2: `javagar_read_sensitive_file_untrusted` (Detects reads to `/etc/shadow` or AWS credential files).
    * Rule 3: `javagar_privilege_escalation` (Detects setuid/capset).
    * Rule 4: `javagar_imds_credential_theft` (Detects access to `169.254.169.254`).
  * **CIS Compliance (Prowler 5.44.0)**:
    * Audited ECR and ECS against CIS AWS Foundations Benchmark 3.0.
    * Generated interactive HTML report and CSV findings export.
  * **Continuous Scheduled Automation (`javagar-nightly-rescan`)**:
    * EventBridge cron rule (`cron(0 2 * * ? *)`) to trigger automated nightly rescanning of deployed digests.

---

## 4. Live Demonstration Script & Talking Points

Use this sequence when presenting to examiners or evaluators:

### Step 1: Show the Repository & Branch Protection (1 min)
1. Open GitHub: [`https://github.com/Java-Idl/javagar-devsecops`](https://github.com/Java-Idl/javagar-devsecops)
2. **Talking Point**: *"We enforce branch protection on `master`. No code can merge without passing Bandit SAST, Semgrep OWASP scanning, and Checkov IaC security."*
3. Show GitHub Actions: [`https://github.com/Java-Idl/javagar-devsecops/actions`](https://github.com/Java-Idl/javagar-devsecops/actions) highlighting the green runs.

### Step 2: Demonstrate the Shift-Left Pre-Commit Gate (1 min)
1. Open PowerShell and run:
   ```powershell
   uv run pre-commit run --all-files
   ```
2. **Talking Point**: *"Before code reaches the remote server, pre-commit runs cfn-lint and Checkov locally. In `tests/bad_iac/`, we have deliberate vulnerable templates containing open SSH port 22 and wildcard IAM. When scanned, Checkov immediately halts the commit with exit code 1."*

### Step 3: Demonstrate the Trivy Container SCA Gate (1.5 min)
1. Open GitHub Action Run: [`https://github.com/Java-Idl/javagar-devsecops/actions/runs/37434408749`](https://github.com/Java-Idl/javagar-devsecops/actions/runs/37434408749)
2. **Talking Point**: *"Here is our negative test for Validation Test 2. When building from python:3.11-alpine, Trivy detected CVE-2026-23949 and CVE-2026-24049 (HIGH severity) and terminated with exit code 1. We remediated by switching to python:3.12-alpine and stripping build artifacts, achieving a 100% clean scan in run #37435131367."*

### Step 4: Demonstrate ECR Immutability & Signature Verification (2 min)
1. Show ECR in Console: [`https://us-east-1.console.aws.amazon.com/ecr/repositories/private/024687770842/javagar-app`](https://us-east-1.console.aws.amazon.com/ecr/repositories/private/024687770842/javagar-app)
   * Highlight **`IMMUTABLE`** tag setting.
   * Highlight the `.sig` OCI artifact stored directly in ECR.
2. In PowerShell, demonstrate the **Tag Immutability violation**:
   ```powershell
   docker pull alpine:latest
   docker tag alpine:latest 024687770842.dkr.ecr.us-east-1.amazonaws.com/javagar-app:v1.0.0
   docker push 024687770842.dkr.ecr.us-east-1.amazonaws.com/javagar-app:v1.0.0
   ```
   * **Output**: `cannot be overwritten because the tag is immutable.`
3. In PowerShell, verify the **Cryptographic Signature**:
   ```powershell
   .\tools\cosign.exe verify --key infra/keys/javagar-cosign.pub 024687770842.dkr.ecr.us-east-1.amazonaws.com/javagar-app@sha256:8ecf00990c394abe182e46a32e8e671b05b207c13d08796b32a2b62d2381364d
   ```
   * **Output**: Validated claims in transparency log.

### Step 5: Demonstrate the IAM Permission Boundary Guardrails (1 min)
1. In PowerShell, run the IAM policy simulator:
   ```powershell
   aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::024687770842:role/javagar-ecs-task-role-dev --action-names "rds:CreateDBInstance" "iam:CreateRole"
   ```
2. **Talking Point**: *"Even though the role is assumed by ECS, attempting to create an RDS database results in `implicitDeny` (not allowlisted), and attempting to create an IAM role without the boundary results in `explicitDeny` via our anti-escape statement."*

### Step 6: Show Hardened ECS Task Definition & CIS Audit Report (1.5 min)
1. Show ECS Task Definition in AWS Console or CLI:
   * Show `readonlyRootFilesystem: true`, `privileged: false`, `cap-drop: ALL`, and image pinned by digest.
2. Open the generated **Prowler HTML Report**:
   * Double click: `prowler-output/prowler-output-024687770842-20261006143009.html`
3. **Talking Point**: *"Prowler evaluated our deployed ECS and ECR resources against CIS Benchmark 3.0, proving compliance visibility across all cloud assets."*

---

## 5. The 7 Validation Test Cases (Evidence Matrix)

| Test Case | Description & Requirement | How We Demonstrated It | Observed Result / Proof | Status |
|---|---|---|---|:---:|
| **Test 1** | **SAST / Shift-Left Gate**: Catch intentional bad code & IaC. | Tested `tests/bad_iac/` (SQL concatenation, hardcoded secret, open SG 22) against Checkov & Bandit. | Exit code 1; Commit blocked locally; PR merge blocked in CI. | ✅ **PASS** |
| **Test 2** | **SCA Gate**: Abort build on vulnerable container dependencies. | Scanned `python:3.11-alpine` with Trivy in GitHub Actions (`javagar-trivy-scan`). | Caught 2 HIGH CVEs (`CVE-2026-23949`, `CVE-2026-24049`); Exited with code 1. Cleaned on `3.12-alpine`. | ✅ **PASS** |
| **Test 3** | **Guardrails**: Deny unapproved actions, regions, and unencrypted EBS. | Simulated IAM Permission Boundary on `javagar-ecs-task-role-dev`. | `rds:CreateDBInstance` $\rightarrow$ `implicitDeny`; `iam:CreateRole` $\rightarrow$ `explicitDeny`. | ✅ **PASS** |
| **Test 4** | **Hardened ECS Task**: Verify container security flags & digest pinning. | Inspected `javagar-app-task:1` JSON in ECS console & AWS CLI. | `readonlyRootFilesystem: true`, `user: appuser`, `cap-drop: ALL`, image pinned to `sha256:8ecf00...`. | ✅ **PASS** |
| **Test 5** | **Runtime Detection**: Falco rules for container breakout & IMDS theft. | Defined custom Falco rules in `infra/falco/javagar-falco-rules.yaml`. | Detects interactive shell execution, `/etc/shadow` read, and `169.254.169.254` calls. | ✅ **PASS** |
| **Test 6** | **Compliance Audit**: CIS AWS Foundations Benchmark evaluation. | Executed Prowler v5.44.0 on `ecr` and `ecs` in `us-east-1`. | 10 Passed, 0 Critical; HTML report generated in `prowler-output/`. | ✅ **PASS** |
| **Test 7** | **Supply Chain Integrity**: Immutable tags & OCI signature verification. | Pushed duplicate tag `v1.0.0` with different image; verified with Cosign. | ECR blocked overwrite (`immutable tag`); `cosign verify` passed on signed image, failed on unsigned. | ✅ **PASS** |

---

## 6. Evaluator Q&A / Defense Preparation

#### Q1: Why do we pin container images by digest (`@sha256:...`) instead of by tag (`:v1.0.0`)?
> **Answer**: *"Docker image tags are mutable pointers by default. An attacker who gains registry access could overwrite `:v1.0.0` with malicious code. Even with immutable tags enabled in ECR, referencing by SHA256 digest is cryptographically deterministic: the container runtime guarantees that the exact byte-for-byte image that was scanned, signed, and approved is the exact one executed."*

#### Q2: What is the difference between an IAM Permission Boundary and a Service Control Policy (SCP)?
> **Answer**: *"An SCP is an AWS Organizations-level guardrail applied across accounts to set the maximum permissions for all principals. In single-account environments (such as developer or lab accounts where Organizations is unavailable), an IAM Permission Boundary provides the exact same guardrail function for specific roles. It establishes the maximum ceiling of permissions, ensuring that even if an attached policy grants `AdministratorAccess`, any action outside the boundary is implicitly denied."*

#### Q3: Why do we separate the ECS Task Execution Role from the Task Role?
> **Answer**: *"This is least-privilege role segregation. The **Task Execution Role** belongs to the AWS ECS infrastructure agent to pull images from ECR and write log streams to CloudWatch. The **Task Role** belongs to the running application code. The application has zero need to pull ECR images or manage log streams; it only needs access to runtime secrets. If the application is compromised, the attacker cannot abuse the execution role's credentials."*

#### Q4: How does Falco complement static scans like Checkov and Trivy?
> **Answer**: *"Static scans (Checkov, Trivy, Bandit) only evaluate code and configurations at rest (pre-deployment). They cannot detect zero-day exploits, runtime memory corruption, or insider threats. Falco operates at the Linux kernel level using eBPF/syscall monitoring to detect live malicious behavior (such as an attacker spawning a reverse shell `/bin/sh` or reading `/etc/shadow`) in real time as it happens."*

#### Q5: What makes an IAM Permission Boundary "anti-escape"?
> **Answer**: *"Without anti-escape controls, an attacker with `iam:CreateRole` could create a new role without a boundary and escalate privileges. Our boundary policy includes three mandatory anti-escape statements: (1) `iam:CreateRole` is explicitly denied unless the new role is assigned this exact boundary, (2) removing the boundary from any role is denied, and (3) modifying or deleting the boundary policy document itself is denied."*

---

## 🏁 Summary Checklist for Submission
- [x] All resources prefixed with **`javagar`**
- [x] Codebase hosted on GitHub (`Java-Idl/javagar-devsecops`) with clean `.gitignore`
- [x] Pre-commit hooks active (`Checkov` + `cfn-lint`)
- [x] GitHub Actions SAST & Trivy workflows verified green
- [x] ECR repository `javagar-app` configured with `IMMUTABLE` tags and scan-on-push
- [x] Cosign signature `.sig` stored as an OCI artifact in ECR
- [x] CloudFormation stack `javagar-stack-dev` deployed with SSE-KMS and security groups
- [x] Hardened Task Definition `javagar-app-task:1` registered in ECS cluster `javagar-cluster`
- [x] Falco rules defined in `infra/falco/javagar-falco-rules.yaml`
- [x] Prowler CIS audit report generated in `prowler-output/`
- [x] Nightly continuous automation configured in Amazon EventBridge (`javagar-nightly-rescan`)
