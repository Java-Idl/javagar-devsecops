# javagar-devsecops

**Problem Statement 10 – DevSecOps Pipeline & IaC Security**

## Phase 1 – Repository & SAST

| Tool | Version | Role |
|---|---|---|
| pre-commit | 4.6.2 | Local git hook runner |
| Checkov | 3.3.23 | IaC SAST (CFN, TF, Dockerfile) |
| cfn-lint | 1.57.1 | CloudFormation linting |
| Bandit | 1.9.4 | Python SAST |
| Semgrep | CI only | Python + IaC multi-rule SAST |

### Quick start (local)

```powershell
# Install tools (uv required)
uv venv .venv
uv pip install --python .venv\Scripts\python.exe pre-commit cfn-lint bandit

# Install the git hooks
.venv\Scripts\pre-commit install

# Test the hooks manually (runs against staged files)
.venv\Scripts\pre-commit run --all-files
```

### Structure

```
javagar-devsecops/
├── app/
│   ├── app.py              # Flask app (clean – parameterized queries)
│   ├── Dockerfile          # Multi-stage, non-root, python:3.11-alpine
│   └── requirements.txt
├── infra/
│   ├── cfn/
│   │   └── javagar-stack.yaml   # Compliant CFN (VPC, SG, IAM, S3)
│   └── terraform/
│       └── main.tf              # ECR repo (immutable tags, scan-on-push)
├── tests/
│   └── bad_iac/                 # Validation Test 1 – deliberately bad files
│       ├── javagar-bad-cfn.yaml
│       └── javagar-bad-app.py
├── .github/
│   └── workflows/
│       └── javagar-sast.yml     # Bandit + Semgrep + Checkov on every PR
├── .pre-commit-config.yaml
├── checkov.bat                  # Windows shim for checkov uv tool
└── .gitignore
```

## Validation Tests

See [init.md](init.md) for the full test matrix.
