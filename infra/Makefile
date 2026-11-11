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
	docker run --rm -v $(CURDIR):/path zricethezav/gitleaks:latest detect --source="/path" --verbose --redact

# 3. TruffleHog
trufflehog:
	@echo "\n🔍 [3/6] Executando TruffleHog (Secret Scan)..."
	docker run --rm -v $(CURDIR):/workdir trufflesecurity/trufflehog:latest filesystem /workdir

# 4. TFLint
tflint:
	@echo "\n🔍 [4/6] Executando TFLint..."
	docker run --rm -v $(CURDIR):/data -w /data ghcr.io/terraform-linters/tflint:latest --recursive

# 5. Trivy Security Scan
trivy:
	@echo "\n🔍 [5/6] Executando Trivy (Security & Secrets Scan)..."
	docker run --rm -v $(CURDIR):/root/src aquasec/trivy:latest fs /root/src --severity CRITICAL,HIGH --exit-code 1 --ignore-unfixed

# 6. Checkov IaC Scan
checkov:
	@echo "\n🔍 [6/6] Executando Checkov (IaC & Secret Scan)..."
	docker run --rm -v $(CURDIR):/tf bridgecrew/checkov:latest -d /tf --framework terraform,secrets --enable-secret-scan-all-files --skip-path terraform.tfvars
