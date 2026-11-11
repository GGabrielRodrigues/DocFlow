# Inventário e Especificações do Servidor On-Premise (`infra/docs/servidor.md`)

Este documento registra as especificações técnicas de hardware, sistema operacional, armazenamento, rede e diretrizes de segurança do servidor **on-premise** que hospeda o **DocFlow** (`INF-05`).

---

## 1. Especificações de Hardware e Virtualização

O servidor opera em uma máquina virtual dedicada (**QEMU/KVM**) sob infraestrutura on-premise:

| Componente | Especificação | Observações Operacionais |
| :--- | :--- | :--- |
| **Hostname** | `VM1-ubuntu-2204-cloud-init` | Provisionado via Cloud-Init |
| **Processador (CPU)** | **12th Gen Intel® Core™ i3-12100T** | 4 vCPUs dedicadas (`1 socket`, `1 thread/core`, `NUMA node0: 0-3`) |
| **Memória RAM** | **7.8 GiB** (~8 GB) | ~7.1 GiB disponíveis em repouso; `Swap: 0B` (recomenda-se criar swapfile de 4 GB como margem de segurança para picos do FFmpeg) |
| **Armazenamento (Disco)** | **102.2 GB** (`QEMU HARDDISK /dev/sda`) | Partição raiz `/dev/sda1` com **99 GB** (`ext4`), ~95 GB livres (4% em uso) |

---

## 2. Sistema Operacional e Runtime de Contêineres

| Camada | Versão Instalada |
| :--- | :--- |
| **Sistema Operacional** | Ubuntu 22.04.5 LTS (*Jammy Jellyfish*) |
| **Kernel Linux** | `5.15.0-198-generic` (`x86_64`) |
| **Docker Engine** | `Docker version 29.9.3 (build 5457199)` |
| **Docker Compose** | `Docker Compose version v5.7.0` |

---

## 3. Topologia de Rede, Acesso Administrativo e Exposição

| Canal | Configuração | Finalidade |
| :--- | :--- | :--- |
| **Rede VPN / Overlay (Tailscale)** | `100.102.165.104` | Acesso administrativo privado via SSH (`ssh://<usuario>@100.102.165.104:22`) utilizado pelo Terraform (`kreuzwerker/docker`) e operadores. |
| **Rede Interna Docker** | `shared-network` (`bridge`) | Comunicação isolada entre os contêineres (`postgres`, `redis`, `silo`, `docflow-web`, `docflow-api`, `docflow-worker-*`, `pgadmin`, `portainer`, `grafana`, `grafana-loki`, `grafana-alloy`). |
| **Exposição Pública (HTTPS/TLS)** | **Cloudflare Tunnel (`cloudflared`)** | Conexão *outbound-only* do servidor para a borda da Cloudflare, expondo apenas `app.<dominio>`, `api.<dominio>` e `s3.<dominio>` sem abrir portas no roteador local. |

---

## 4. Alocação de Recursos e Capacidade (Dimensionamento)

Considerando os **7.8 GiB de RAM**, **4 vCPUs** e **99 GB de disco**:

1. **Memória RAM e CPU**:
   - **PostgreSQL (`postgres`)**: ~512 MB – 1 GB RAM.
   - **Redis (`redis`)**: limitado a `512 MB` (`redis_memory_limit`) e `1024` CPU shares via Terraform.
   - **Silo (`silo`)**: ~512 MB – 1 GB RAM.
   - **DocFlow API + Workers (`docflow-api`, `worker-io`, `worker-ai`)**: ~1.5 GB RAM somados.
   - **DocFlow Worker CPU (`docflow-worker-cpu` — FFmpeg/LibreOffice)**: limitado a `2048 MB` (2 GB RAM) e `2048` CPU shares com concorrência `1`, evitando que uma conversão de vídeo esgote a memória da VM.
   - **Observabilidade (`grafana`, `loki`, `alloy`)**: ~1 GB RAM somados.
2. **Capacidade de Disco (`95 GB` livres) e Upload de até 10 GB (`INF-06`)**:
   - O disco atual comporta múltiplos uploads simultâneos de até 10 GB, desde que combinados com:
     - **Limpeza automática de uploads multipart incompletos após 24h** (`RN-18` / `DOC-09`);
     - **Compressão de vídeo em segundo plano** (`RF-08`) substituindo o bruto pesado por versão otimizada quando aplicável;
     - **Alerta no Grafana** quando o uso da partição `/` ultrapassar **80%** (~79 GB).
   - Caso o volume de vídeos retidos cresça na operação, um disco virtual adicional (`/dev/sdb`) pode ser anexado à VM QEMU e montado diretamente no volume `silo-data`.

---

## 5. Diretrizes de Hardening e Operação (`INF-05` / `INF-08`)

- **SSH Restrito**: acesso SSH realizado exclusivamente via rede privada Tailscale (`100.102.165.104`) com autenticação por chave pública (`PasswordAuthentication no`).
- **Firewall (UFW)**: manter tráfego de entrada bloqueado na interface pública (`ufw default deny incoming`), liberando entrada na interface `tailscale0`.
- **Swap Recomendado**: como a VM está com `Swap: 0B`, recomenda-se ativar um arquivo de swap de 4 GB (`/swapfile`) para evitar *OOM Kill* durante processamentos pesados de mídia.
