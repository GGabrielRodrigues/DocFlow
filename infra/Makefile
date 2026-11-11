.PHONY: check fmt gitleaks trufflehog tflint trivy checkov

# Comando principal: executa todas as verificações em sequência
check: fmt gitleaks trufflehog tflint trivy checkov
	@echo "\n✅ Todas as verificações de estática e segurança passaram com sucesso!"

# 1. Terraform Format Check
fmt:
	@echo "\n🔍 [1/6] Verificando formatação do Terraform..."
	terraform fmt -check -recursive

# 2. Gitleaks
gitleaks:
	@echo "\n🔍 [2/6] Executando Gitleaks (Secret Scan)..."
	docker run --rm -v $(abspath $(CURDIR)/..):/path zricethezav/gitleaks:v8.18.2 detect --source="/path" --gitleaks-ignore-path="/path/infra/.gitleaksignore" --verbose --redact

# 3. TruffleHog
trufflehog:
	@echo "\n🔍 [3/6] Executando TruffleHog (Secret Scan)..."
	docker run --rm -v $(CURDIR):/workdir trufflesecurity/trufflehog:latest filesystem /workdir --exclude-paths=/workdir/.trufflehogignore --fail

# 4. TFLint
tflint:
	@echo "\n🔍 [4/6] Executando TFLint..."
	docker run --rm -v $(CURDIR):/data -w /data ghcr.io/terraform-linters/tflint:v0.54.0 --recursive

# 5. Trivy Security Scan
trivy:
	@echo "\n🔍 [5/6] Executando Trivy (Security & Secrets Scan)..."
	docker run --rm -v $(CURDIR):/root/src aquasec/trivy:latest fs /root/src --scanners misconfig,secret --severity CRITICAL,HIGH --exit-code 1 --ignore-unfixed --skip-dirs "**/.terraform" --skip-files "**/terraform.tfvars"

# 6. Checkov IaC Scan
checkov:
	@echo "\n🔍 [6/6] Executando Checkov (IaC & Secret Scan)..."
	docker run --rm -v $(CURDIR):/tf bridgecrew/checkov:latest -d /tf --framework terraform,secrets --enable-secret-scan-all-files --skip-path terraform.tfvars --skip-path .terraform
