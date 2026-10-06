# Final Implementation Plan v2: DevSecOps Pipeline & IaC Security (Problem Statement 10)

## Architecture

```
Phase 1: GitHub -> Pre-commit (Checkov, cfn-lint) -> Semgrep/Bandit SAST
Phase 2: CodePipeline -> CodeBuild -> Trivy gate (fail on HIGH/CRITICAL)
Phase 3: Push to ECR (immutable tags, scan on push) -> Sign digest (AWS Signer / Cosign) -> Verify signature at deploy -> IAM Permission Boundary
Phase 4: ECS on EC2 (hardened task defs) -> Falco runtime detection -> Prowler CIS audit
Scheduled: EventBridge -> CodeBuild -> Trivy rescan of deployed digest + Prowler (nightly)
```

---

## Phase 1: Repository & SAST

- GitHub repo (permitted by the statement: "CodeCommit or GitHub/GitLab"): app source, Dockerfile, Terraform + CloudFormation.
- `.pre-commit-config.yaml` with **Checkov** and **cfn-lint**. Block commits containing:
  - Security groups open to `0.0.0.0/0` on 22/3389
  - S3 buckets without server-side encryption
  - IAM policies with `Action: "*"` on `Resource: "*"`
- **Semgrep** and **Bandit** on every PR (GitHub Actions or CodeBuild): SQL string concatenation, unsafe deserialization, hardcoded secrets, over-permissive IAM in IaC. Merge blocked on non-zero exit (branch protection requires the check).

## Phase 2: Pipeline & SCA

- **CodePipeline** triggered via CodeStar Connections (GitHub).
- **CodeBuild** (`BUILD_GENERAL1_SMALL`, Ubuntu): unit tests, build image in an isolated build container.
- **Trivy** in `buildspec.yml`:
  ```
  trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed <image>
  ```
  Non-zero exit aborts the pipeline before any push to ECR.

## Phase 3: Registry, Signing, Governance

Flow (order matters, since signing needs a registry digest):
1. Trivy passes -> push image to **ECR** (tag immutability ON, scan-on-push ON).
2. Sign the image **digest** with **AWS Signer** (Notation-based; signature stored in ECR as an OCI artifact). **Fallback: Cosign** if Signer is unavailable in the account.
3. **Deploy stage verifies the signature** (`notation verify` / `cosign verify`) and fails if unsigned or tampered. ECS does not verify signatures natively, so this step is what makes signing meaningful.
4. Task definition references the image by **digest**, not tag.

**IAM Permission Boundary** on all deployment/execution roles:
- Allowlist of permitted services/actions
- Deny when `aws:RequestedRegion` is outside approved regions
- Deny `ec2:RunInstances` / `ec2:CreateVolume` unless `ec2:Encrypted` is true
- **Anti-escape statements (required):**
  - `iam:CreateRole` / `iam:CreateUser` only with condition `iam:PermissionsBoundary = <boundary ARN>`
  - Deny `iam:DeleteRolePermissionsBoundary`, `iam:PutRolePermissionsBoundary` (except to the same boundary)
  - Deny edits/deletion of the boundary policy itself

## Phase 4: Hardened Deployment & Runtime

- **ECS on EC2** (permitted by the statement: "ECS or EKS"), free-tier `t2/t3.micro`, private subnets, `awsvpc` mode.
- Task definition hardening: `readonlyRootFilesystem: true`, non-root `user`, `privileged: false`, all Linux capabilities dropped, secrets from Secrets Manager (not env vars).
- Two distinct roles:
  - **Task Execution Role**: ECS agent only (ECR pull, read secrets).
  - **Task Role**: app identity; minimal or none.
- Block task access to instance credentials: IMDSv2 required, hop limit 1; with `awsvpc` also `ECS_AWSVPC_BLOCK_IMDS=true`.
- **Falco** on the host (eBPF driver preferred), JSON output to `/var/log/falco_events.log`. Rules: shell in container, privilege escalation, sensitive file reads, unexpected outbound connections.
- **Prowler**:
  ```
  prowler aws --compliance cis_3.0_aws
  ```
  (confirm name with `prowler aws --list-compliance`; varies by version). Export HTML/JSON.

## Scheduled Controls (closes the "continuous" gap)

EventBridge nightly -> CodeBuild: (a) Trivy on the currently deployed image digest, (b) Prowler, report stored in S3.

---

## Substitutions and Honest Gaps

| Statement names | Used | Why | Not covered |
|---|---|---|---|
| CodeCommit (or GitHub/GitLab) | GitHub | **Permitted by statement**; CodeCommit closed to new customers | None |
| CodeGuru Reviewer | Semgrep + Bandit | Deprecated/paid, blocked in learner accounts | No ML/automated-reasoning analysis; **no concurrency-bug detection** (statement calls this out) |
| Inspector scan in build | Trivy + ECR basic scan | Per-image fees after trial | No continuous re-evaluation on new CVEs (mitigated by nightly rescan) |
| Control Tower SCPs + IAM boundaries | IAM Permission Boundaries only | No Organizations in single-account/Learner Lab | The statement lists boundaries explicitly, so half is met directly. SCP half is an approximation: boundaries only constrain attached identities |
| ECS or EKS | ECS on EC2 | **Permitted by statement** | None |
| GuardDuty EKS Runtime Monitoring | Falco on host | Requires EKS + paid agent; not applicable to ECS-EC2 setup | Detection only; no central aggregation or managed rules |
| Security Hub + Config | Prowler (scheduled) | Per-rule/item fees | No change history or drift detection; point-in-time |

### Optional: use native services during free trials
If the exam falls inside trial windows and the account permits, enabling the named services directly is the strongest answer: Inspector (15-day trial), GuardDuty (30-day), Security Hub (30-day). Config has no trial but costs cents at demo scale if limited to a few resource types. Keep the open-source stack as the documented fallback.

---

## Validation Test Cases

1. **SAST / shift-left.** Commit an IAM resource with `Action:"*"`, `Resource:"*"` plus SQL concatenation and a dummy hardcoded credential. Expected: pre-commit/Semgrep/Checkov exit 1 with file, line, rule ID; merge blocked.
2. **SCA gate.** Build from `python:3.7-slim` or `node:14-alpine`. Expected: Trivy table with CRITICAL CVEs, build fails, nothing pushed. Rebuild on `python:3.11-alpine`; passes.
3. **Guardrails.** As the deployment role:
   - `aws rds create-db-instance ...` -> `AccessDenied` (not in allowlist)
   - `aws ec2 run-instances` with unencrypted EBS -> explicit deny
   - Call in a non-approved region -> explicit deny
   - `aws iam create-role` without the boundary -> deny
4. **Hardened ECS.** `aws ecs describe-tasks` healthy; `describe-task-definition` shows `readonlyRootFilesystem: true`, `privileged: false`, non-root user. Show execution role vs task role. In-container `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/` fails.
5. **Runtime detection.** On the host: `docker exec -it -u 0 <id> /bin/sh`, then `cat /etc/shadow`. (`-u 0` is needed because the container runs non-root, and a failed read would not trigger the rule.) Expected Falco events: *"Terminal shell in container"* and *"Read sensitive file untrusted"*. Paste real output from `/var/log/falco_events.log`.
6. **Compliance.** Run Prowler CIS; show HTML/JSON report plus the scheduled run's report in S3.
7. **Signing and immutability (new).**
   - Re-push an existing tag to ECR -> `ImageTagAlreadyExistsException`.
   - Run deploy stage against an unsigned image digest -> verify step fails, deployment blocked. Then sign it and re-run -> passes.

## Pre-Demo Checklist

- [ ] Learner Lab permits: IAM roles with boundaries, ECR scanning, AWS Signer (else Cosign)
- [ ] Falco driver loads on the chosen AMI/kernel
- [ ] Prowler framework name matches installed version
- [ ] Container has `/bin/sh` and a root-exec path for test 5
- [ ] Dry-run all seven tests and capture logs/screenshots