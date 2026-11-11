# DocFlow — Documento de Requisitos (v0.2)

> Base: análise de público fornecida + protótipo atual (React/Vite, SaaS multi-instituição, perfis Administrador/Funcionário, fluxo Rascunho → Em validação → Aprovado/Devolvido, trilha de auditoria, modelos Ata/Ofício/Prestação de contas).

## 1. Visão

Plataforma **SaaS multi-instituição** de automação inteligente de documentos administrativos: transforma reuniões gravadas (vídeo/áudio de até 2h30 em português) em transcrições com identificação de falantes via provedores de IA em nuvem e preenche documentos institucionais padronizados, sempre com **revisão e aprovação humana**.

**Público prioritário (MVP):** órgãos públicos/secretarias, ONGs, instituições de ensino. Depois: empresas e consultorias.

**Personas**

| Persona | Objetivo | Perfil no sistema |
|---|---|---|
| Servidor / assistente administrativo | Economizar tempo gerando, revisando e validando documentos | Funcionário |
| Coordenador / chefe | Padronizar documentos da área e validar os documentos que solicitar | Funcionário ou Administrador |
| Diretor / gestor | Padronizar processos, gerenciar equipe e acompanhar produção | Administrador |
| Responsável de TI | Segurança, LGPD, governança e auditoria da instituição | Administrador |

## 2. Funcionalidades essenciais

**MVP (SaaS Multi-instituição)**
1. Cadastro de instituição, usuários e perfis (`Administrador` e `Funcionário`, em modelo multi-tenant).
2. Upload de vídeo/áudio (até 10 GB e duração máxima de 2h30) com retomada.
3. Transcrição em português (pt-BR) via nuvem com separação de falantes (diarização) e edição/renomeação dos falantes.
4. Compressão ilimitada de vídeos.
5. Biblioteca de modelos de documento por instituição.
6. Geração de documento (ata, ofício, prestação de contas) a partir da transcrição via IA em nuvem, com extração de campos.
7. Detecção de campos ausentes/inconsistentes.
8. Editor de revisão + fluxo de validação/aprovação (realizado pelo próprio solicitante do documento, seja Administrador ou Funcionário).
9. Exportação (DOCX/PDF).
10. Histórico de versões e trilha de auditoria.

**Fora do escopo do MVP (Pós-MVP):** suporte a outros idiomas além de português, execução de modelos de IA locais/próprios, geração de múltiplos documentos a partir de uma reunião, upload de modelos próprios com detecção automática de campos por IA, geração em lote, assinatura digital e integração com sistemas de processo (ex.: SEI e similares), busca semântica, memorandos/relatórios/planos de ação, SSO.

## 3. Requisitos Funcionais

### 3.1 Conta, instituição e acesso
- **RF-01** Cadastrar instituição (nome, tipo, CNPJ, contato, endereço) e seu primeiro administrador.
- **RF-02** Autenticar usuários (e-mail/senha; recuperação de senha; MFA desejável).
- **RF-03** Administrador gerencia usuários (criar, editar, inativar, definir perfil entre `Administrador` e `Funcionário`).
- **RF-04** Controle de acesso por perfil (`Administrador` e `Funcionário`) e por instituição (SaaS multi-tenant).

### 3.2 Mídia
- **RF-05** Enviar arquivos de vídeo/áudio de até 10 GB e duração máxima de 2h30 (150 minutos), com upload em partes, retomável e barra de progresso.
- **RF-06** Validar formato (MP4, MKV, MOV, WebM, MP3, WAV, M4A…), tamanho (≤ 10 GB), duração (≤ 2h30) e integridade antes de processar.
- **RF-07** Listar, pré-visualizar, baixar e excluir mídias da instituição.
- **RF-08** Comprimir vídeo de forma ilimitada com perfis predefinidos (ex.: "Reunião – leve", "Alta qualidade", "Somente áudio") e mostrar tamanho antes/depois.
- **RF-09** Processamento assíncrono com status (na fila, processando, concluído, falhou), notificação ao concluir e possibilidade de cancelar/reprocessar.

### 3.3 Transcrição
- **RF-10** Transcrever áudio/vídeo em português (pt-BR) com marcação de tempo utilizando provedor de IA em nuvem.
- **RF-11** Separar a fala por pessoa (Falante 1, 2…) e permitir renomear falantes por nomes reais, propagando a mudança.
- **RF-12** Editor de transcrição sincronizado com o player (clicar no trecho → pula no vídeo; corrigir texto e falante).
- **RF-13** Exportar transcrição (TXT, DOCX, SRT/VTT).
- **RF-14** Informar o usuário sobre qualidade (ex.: trechos de baixa confiança destacados).

### 3.4 Modelos e documentos
- **RF-15** Biblioteca de modelos por instituição (criar, editar, versionar, ativar/desativar), com categorias, campos e regras de preenchimento (obrigatório, formato).
- **RF-16** Modelos padrão do sistema (ata, ofício, memorando, prestação de contas) disponíveis a todas as instituições.
- **RF-17** Importar modelo (DOCX) e identificar campos a preencher (pós-MVP para detecção por IA).
- **RF-18** Gerar documento a partir de uma ou mais transcrições + informações adicionais do usuário, com IA em nuvem extraindo participantes, pauta, decisões, responsáveis, prazos e encaminhamentos.
- **RF-19** Listar campos **não encontrados** ou ambíguos e solicitá-los ao usuário; a IA nunca inventa valores.
- **RF-20** Vincular trechos da transcrição que embasam cada informação extraída (rastreabilidade da fonte).
- **RF-21** Editar o documento gerado e regenerar seções específicas.
- **RF-22** Revisão automática: inconsistências, ortografia, divergência com o modelo.
- **RF-23** Exportar em DOCX e PDF.

### 3.5 Fluxo de validação e rastreabilidade
- **RF-24** Estados do documento: Rascunho → Em validação → Aprovado / Devolvido (com justificativa).
- **RF-25** Encaminhar o documento para validação, permitindo que a própria pessoa que solicitou a sua geração (seja `Administrador` ou `Funcionário`) realize a validação/aprovação.
- **RF-26** Histórico de versões com comparação (diff) e restauração.
- **RF-27** Trilha de auditoria (quem, o quê, quando) para login, upload, geração, edição, aprovação, exportação e exclusão; consultável pelo administrador.
- **RF-28** Dashboard: documentos por status, mídias em processamento, atividades recentes.
- **RF-29** Busca e filtros de documentos, mídias e transcrições.

### 3.6 Privacidade
- **RF-30** Excluir mídia/transcrição sob demanda e por política de retenção configurável.
- **RF-31** Exportar/excluir dados pessoais de um titular mediante solicitação (LGPD).

## 4. Requisitos Não Funcionais

| ID | Categoria | Requisito |
|---|---|---|
| RNF-01 | Desempenho | Transcrição via provedor em nuvem em ≤ 0,5× a duração do áudio (meta); compressão em fila sem travar a interface. |
| RNF-02 | Escalabilidade | Processamento pesado em workers horizontalmente escaláveis; suportar N jobs concorrentes configurável. |
| RNF-03 | Upload | Arquivos de até 10 GB (e até 2h30 de duração) sem passar pela memória do servidor da API; retomada após falha de rede. |
| RNF-04 | Disponibilidade | 99% mensal na fase inicial; jobs não se perdem em reinício (filas persistentes e jobs idempotentes). |
| RNF-05 | Segurança | HTTPS/TLS, senhas com hash forte (Argon2/bcrypt), criptografia em repouso, URLs de acesso a mídia assinadas e temporárias. |
| RNF-06 | Isolamento | Arquitetura SaaS multi-instituição com dados estritamente isolados por instituição (multi-tenancy). |
| RNF-07 | LGPD | Base legal, minimização, registro de operações, retenção configurável, contrato/DPA com provedores de IA em nuvem. |
| RNF-08 | Arquitetura de IA | Uso de provedores de IA em nuvem no MVP desacoplados por interfaces (`TranscriptionProvider`, `LLMProvider`), permitindo troca futura de provedor sem impacto no domínio. |
| RNF-09 | Auditabilidade | Registros de auditoria imutáveis (append-only). |
| RNF-10 | Usabilidade | Interface e suporte de transcrição exclusivamente em português do Brasil (pt-BR) no MVP, simples para usuários não técnicos e responsiva. |
| RNF-11 | Acessibilidade | Conformidade com WCAG 2.1 AA (e eMAG para órgãos públicos). |
| RNF-12 | Confiabilidade da IA | Saída estruturada validada por esquema; avaliação periódica com conjunto de testes (WER, DER, fidelidade de campos). |
| RNF-13 | Observabilidade | Logs estruturados, métricas, rastreamento por job, alertas de falha e custo de IA por instituição. |
| RNF-14 | Manutenibilidade | Código com testes automatizados (TDD no domínio), CI, módulos desacoplados. |
| RNF-15 | Portabilidade | Execução via contêineres (Docker Compose em dev e produção, provisionamento com Terraform). |
| RNF-16 | Custo | Controle de uso/cotas por instituição para horas de transcrição, tokens de IA e armazenamento (compressão de vídeo ilimitada no MVP). |
| RNF-17 | Compatibilidade | Navegadores modernos (Chrome, Edge, Firefox, Safari — últimas 2 versões). |

## 5. Regras de Negócio

- **RN-01** Todo dado pertence a uma instituição; usuário só acessa dados da sua instituição (SaaS multi-instituição).
- **RN-02** Cada instituição tem ao menos um Administrador ativo; o último administrador não pode ser inativado/removido.
- **RN-03** Somente Administrador gerencia usuários, modelos institucionais e auditoria.
- **RN-04** Usuário inativo não autentica, mas seus registros e autoria são preservados.
- **RN-05** Arquivos acima de 10 GB ou com duração superior a 2h30 (150 minutos) são rejeitados antes do processamento, com mensagem clara. Suporte de idioma restrito ao português (pt-BR) no MVP.
- **RN-06** A IA **não emite** documento oficial: todo documento gerado nasce como Rascunho e requer aprovação humana.
- **RN-07** A pessoa que solicitou a geração do documento é a responsável por sua validação (aprovação ou devolução), independentemente de possuir o perfil `Administrador` ou `Funcionário`.
- **RN-08** A IA não pode inventar informações: campos sem evidência ficam marcados "pendente" e bloqueiam a aprovação se obrigatórios.
- **RN-09** Documento Aprovado é imutável; alterações geram nova versão que volta para Rascunho.
- **RN-10** Devolução exige justificativa registrada.
- **RN-11** Toda ação relevante gera registro de auditoria que não pode ser editado nem excluído.
- **RN-12** Modelos versionados: documentos já gerados mantêm a versão do modelo usada.
- **RN-13** Transcrições e mídias são confidenciais; só o autor, administradores e usuários explicitamente compartilhados acessam.
- **RN-14** Mídias e transcrições seguem a política de retenção da instituição; após o prazo, mídia original é excluída (documentos aprovados permanecem).
- **RN-15** Antes de enviar conteúdo a provedor de IA em nuvem, a instituição deve ter habilitado esse provedor (consentimento/contrato).
- **RN-16** Cota de uso por instituição aplica-se a horas de transcrição, tokens de IA e armazenamento (ao esgotar, novos jobs de transcrição/IA/upload são bloqueados e o administrador é avisado); a compressão de vídeos é ilimitada no MVP.
- **RN-17** Falantes são identificados como "Falante N" até serem renomeados por um humano; o sistema não infere identidade real por voz.
- **RN-18** Compressão é ilimitada por instituição no MVP e nunca sobrescreve o original sem confirmação; a versão comprimida é sempre salva como um novo arquivo.

## 6. Matriz de Rastreabilidade Inicial (Requisito → Issue)

### 6.1 Requisitos Funcionais (RF)

| Requisito | Descrição resumida | Issues relacionadas |
|---|---|---|
| **RF-01** | Cadastro de instituição e primeiro administrador | `BE-04`, `FE-04`, `DOC-10`, `DOC-11` |
| **RF-02** | Autenticação de usuários e recuperação de senha | `BE-05`, `BE-24`, `FE-04` |
| **RF-03** | Gestão de usuários pelo administrador | `BE-06`, `FE-05` |
| **RF-04** | Controle de acesso por perfil e instituição | `BE-03`, `BE-06`, `FE-04` |
| **RF-05** | Upload multipart retomável de até 10 GB / 2h30 | `DOC-09`, `INF-06`, `BE-08`, `FE-06` |
| **RF-06** | Validação de formato, tamanho, duração (≤ 2h30) e integridade | `BE-08`, `WK-02`, `FE-06` |
| **RF-07** | Listagem, pré-visualização, download e exclusão de mídias | `BE-09`, `FE-07` |
| **RF-08** | Compressão ilimitada de vídeo com perfis predefinidos | `WK-09`, `FE-10` |
| **RF-09** | Processamento assíncrono de jobs com status e cancelamento | `BE-10`, `WK-01`, `WK-04`, `FE-07`, `FE-08` |
| **RF-10** | Transcrição em português (pt-BR) via nuvem com timestamps | `DOC-06`, `BE-11`, `WK-03`, `WK-04`, `FE-08` |
| **RF-11** | Diarização de falantes e renomeação com propagação | `BE-12`, `WK-03`, `FE-09` |
| **RF-12** | Editor de transcrição sincronizado com player | `BE-12`, `FE-09` |
| **RF-13** | Exportação da transcrição (TXT, DOCX, SRT/VTT) | `BE-11`, `FE-09` |
| **RF-14** | Destaque de trechos de baixa confiança na transcrição | `BE-11`, `WK-03`, `FE-09` |
| **RF-15** | Biblioteca de modelos por instituição com versionamento | `BE-13`, `FE-11` |
| **RF-16** | Modelos padrão do sistema (ata, ofício, prestação de contas) | `DOC-14`, `BE-13`, `FE-11` |
| **RF-17** | Importação de modelo DOCX (detecção por IA no pós-MVP) | `BE-13`, `FE-11` |
| **RF-18** | Geração de documento via IA a partir de transcrições | `BE-14`, `WK-05`, `WK-06`, `FE-12` |
| **RF-19** | Detecção de campos pendentes/ambíguos sem alucinação | `BE-14`, `WK-06`, `FE-12` |
| **RF-20** | Vínculo de evidências (trechos/timestamps) por campo | `BE-14`, `WK-06`, `FE-12` |
| **RF-21** | Edição de documento e regeneração de seções | `BE-15`, `FE-13` |
| **RF-22** | Revisão automática de inconsistências e ortografia | `BE-17`, `WK-07`, `FE-13` |
| **RF-23** | Exportação de documentos em DOCX e PDF | `BE-18`, `WK-10`, `FE-14` |
| **RF-24** | Máquina de estados do documento (Rascunho → Validação → Aprovado/Devolvido) | `DOC-10`, `BE-16`, `FE-14` |
| **RF-25** | Envio para validação e aprovação pelo solicitante | `BE-16`, `BE-24`, `FE-14` |
| **RF-26** | Histórico de versões de documentos com diff e restauração | `BE-15`, `FE-13` |
| **RF-27** | Trilha de auditoria consultável pelo administrador | `BE-07`, `FE-15` |
| **RF-28** | Dashboard com indicadores e atividades recentes | `BE-19`, `FE-15` |
| **RF-29** | Busca e filtros de documentos, mídias e transcrições | `BE-19`, `FE-15` |
| **RF-30** | Exclusão de mídia/transcrição sob demanda e por retenção | `BE-21`, `WK-11`, `FE-16` |
| **RF-31** | Exportação e exclusão de dados de titulares (LGPD) | `DOC-12`, `BE-21`, `FE-16` |

### 6.2 Requisitos Não Funcionais (RNF) e Regras de Negócio (RN)

| ID | Escopo | Issues relacionadas |
|---|---|---|
| **RNF-01, RNF-02, RNF-04** | Desempenho, escalabilidade de workers e filas persistentes | `INF-11`, `BE-10`, `WK-01`, `WK-04` |
| **RNF-03, RN-05** | Upload multipart até 10 GB e limite de duração de 2h30 em pt-BR | `DOC-09`, `INF-06`, `BE-08`, `WK-02`, `FE-06` |
| **RNF-05** | Segurança (TLS, Argon2, URLs assinadas, headers) | `INF-07`, `INF-20`, `BE-05`, `BE-09`, `BE-22` |
| **RNF-06, RN-01** | Isolamento estrito SaaS multi-tenant (`institution_id` + RLS) | `DOC-08`, `BE-03` |
| **RNF-07, RN-14, RN-15** | Conformidade LGPD, retenção e habilitação de IA em nuvem | `DOC-12`, `BE-21`, `WK-11`, `FE-16` |
| **RNF-08, RNF-12** | Provedores de IA em nuvem atrás de interfaces, saída estruturada e evals | `DOC-06`, `WK-03`, `WK-05`, `WK-08` |
| **RNF-09, RN-11** | Imutabilidade da trilha de auditoria (append-only) | `BE-07` |
| **RNF-10, RNF-11** | Usabilidade em pt-BR, responsividade e acessibilidade WCAG 2.1 AA | `FE-02` |
| **RNF-13** | Observabilidade (logs, métricas, alertas) | `INF-15`, `BE-01` |
| **RNF-14** | Manutenibilidade, TDD e CI | `DOC-01`, `BE-02`, `FE-01`, `FE-17`, `INF-13`, `INF-14` |
| **RNF-15** | Contêineres e IaC (Docker Compose, Terraform, Infisical) | `DOC-07`, `INF-01` a `INF-12`, `INF-16` |
| **RNF-16, RN-16, RN-18** | Cotas de transcrição/IA/storage e compressão ilimitada | `INF-18`, `BE-20`, `WK-09`, `WK-11`, `FE-10`, `FE-16` |
| **RN-02, RN-03, RN-04** | Regras de administradores, perfis e inativação de usuários | `BE-04`, `BE-05`, `BE-06`, `FE-05` |
| **RN-06, RN-07, RN-08, RN-09, RN-10** | Ciclo de vida do documento, validação pelo solicitante e evidências | `BE-14`, `BE-15`, `BE-16`, `WK-06`, `FE-12`, `FE-13`, `FE-14` |
| **RN-12** | Imutabilidade de versão de modelo nos documentos gerados | `BE-13` |
| **RN-13** | Confidencialidade de mídias e transcrições | `BE-09`, `BE-11` |
| **RN-17** | Identificação neutra de falantes ("Falante N") | `BE-12`, `WK-03`, `FE-09` |
