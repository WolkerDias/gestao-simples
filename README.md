# Gestão Simples - Sistema de Gestão para Pequenas Empresas

[![Licença MIT](https://img.shields.io/badge/Licença-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Framework Streamlit](https://img.shields.io/badge/Streamlit-1.41.1-FF4B4B)](https://streamlit.io/)

  > Sistema de gestão simplificado para pequenas empresas que automatiza a leitura de cupons via QR Code, coleta dados da SEFAZ-MS e armazena informações de forma segura em banco de dados MySQL ou PostgreSQL.

## 🎯 O Problema

Pequenas empresas, especialmente no setor de alimentação, enfrentam diversos desafios ao cadastrar produtos adquiridos de supermercados e fornecedores:

### 1. Falta de padronização nas informações dos fornecedores

- Produtos podem ser nomeados de forma diferente em notas fiscais (ex.: "Tomate Salada" vs. "Tomate Vermelho").
- Fornecedores usam medidas distintas (kg, unidades, pacotes), dificultando a conversão para sistemas internos.
- Produtos comprados em supermercados muitas vezes não têm identificadores padronizados, exigindo cadastro manual.

### 2. Processos manuais e propensos a erros

- A falta de automação leva a erros de digitação, duplicidade ou omissão de dados.
- Equipes pequenas **perdem horas registrando produtos**, desviando o foco de atividades essenciais como atendimento ao cliente.

### 3. Custos ocultos e margens de lucro

- Erros no cadastro de preços ou quantidades distorcem o cálculo do custo por porção, impactando a precificação.
- Falhas no registro de estoque levam a compras excessivas ou falta de ingredientes, gerando perdas.

### 4. Rotatividade de pessoal

- Funcionários temporários ou mal treinados cometem erros no cadastro, especialmente em períodos de alta demanda.
- A ausência de padrões claros leva a inconsistências entre diferentes colaboradores.

## 💡 Nossa Solução

O Gestão Simples é um sistema de gestão inteligente que transforma notas fiscais em dados precisos em segundos.

### 🛠️ Como Funciona

1. 📸 Faça a leitura da nota fiscal por upload de imagem, câmera ao vivo ou inserindo a chave de acesso/URL.

2. 🤖 Informações da NFC-e são capturadas automaticamente da SEFAZ-MS via *web scraping*.

3. 📦 Itens são vinculados aos produtos cadastrados e novos fornecedores são criados automaticamente, com possibilidade de ajustes manuais.

4. 📊 O sistema atualiza automaticamente o estoque com base no método PEPS, calculando custos, consumo e saldo disponível.

5. 🛠️ Você pode inserir, editar ou excluir registros diretamente pelo sistema quando quiser.

6. 💾 O *backup* pode ser realizado manualmente ou por agendamentos automáticos, com fácil restauração e controle de versões.

  ```mermaid
      flowchart TB
          subgraph Início
              A[👤 Usuário] --> B{{📥 Método de Leitura}}
          end

          subgraph Sistema_Atual
              B -->|📤 Upload de Imagem| C[📸 Leitura QR Code NFC-e]
              B -->|🎥 Câmera ao Vivo| C
              B -->|🔑 Chave de Acesso| D
              C --> D[🕸️ Web Scraping SEFAZ-MS]
              D --> E{{✅ Dados Válidos?}}
              E -->|✔️ Sim| F[💾 Salvar Fornecedor e NFCe no Banco de Dados]
              E -->|❌ Não| G[⚠️ Erro: Solicitar Reenvio] --> A
              F --> H["📝 Cadastro de Associação de Produtos"]
              
              %% Fluxo direto para módulos após associação
              H --> IA[📋 Gestão de Inventário]
              H --> AB[📊 Auditoria PEPS]
              
              %% Módulo de Inventário
              IA --> IA1[Criar/Editar Inventários]
              IA --> IA2[Registrar Itens]
              IA --> IA3[Encerrar Contagens]
              IA --> IA4[Histórico Completo]
              
              %% Módulo de Auditoria
              AB --> AB1[Selecionar Período]
              AB --> AB2[Filtrar Produtos]
              AB --> AB3[Analisar Saldos]
              AB --> AB4[Exportar Dados]
          end

          subgraph Saída
              IA --> O[📈 Relatórios e Dashboards]
              AB --> O
              O --> Q[💡 Otimizar Processos]
          end

          subgraph Backup
              H --> J{{💽 Backup}}
              J -->|"🤖 Automático"| K["Agendamento:\nDiário/Semanal/Mensal"]
              J -->|"🖱️ Manual"| L["Sob Demanda"]
              K --> N["🗑️ Limpar Backups Antigos"]
              K --> M[🔄 Restauração de Backup]
              L --> M
          end

          %% Estilização (Material Design)
          style A fill:#3F51B5,color:white
          style B fill:#009688,color:white
          style C fill:#2196F3,color:white
          style D fill:#673AB7,color:white
          style E fill:#4CAF50,color:white
          style F fill:#FF5722,color:white
          style H fill:#9C27B0,color:white
          style IA fill:#00BCD4,color:black
          style AB fill:#8BC34A,color:black
          style J fill:#FF9800,color:black
          style K fill:#795548,color:white
          style L fill:#795548,color:white
          style M fill:#E91E63,color:white
          style N fill:#E91E63,color:white
  ```

---

### 🚀 Funcionalidades já implementadas

1. 👤 **Autenticação e Gerenciamento de Usuários**
   - Tela de login e logout
   - Gerenciamento de contas e permissões de acesso

    ![Login e Gerenciamento de usuários](/image/login_logout.gif)

2. 📲 **Leitura Instantânea de NF-e (Nota Fiscal Eletrônica) e NFC-e (Nota Fiscal de Consumidor Eletrônica)**
   - Upload de imagem com QR Code
   - Captura em tempo real via câmera
   - Inserção manual da chave de acesso ou URL do QR Code

    ![Leitura de NFC-e via QR Code e chave de acesso](/image/leitor_qrcode.gif)

3. 🤖 **Coleta Automática de Dados da SEFAZ-MS via *Web Scraping***
   - Cadastro automático de fornecedores e documentos fiscais
   - Suporte a correções manuais em casos de notas com descontos

4. 📦 **Cadastro de Produtos e Associação com Itens de Fornecedores**
   - Vinculação de produtos internos aos itens das notas fiscais
   - Otimização da organização e rastreabilidade dos produtos

    ![Cadastro de produtos e associação com itens de fornecedores](/image/produtos_associacao.gif)

5. 📊 **Inventário e Auditoria com Cálculo PEPS**
   - Registros mensais de contagem de estoque
   - Cálculo automático do custo médio (método PEPS), saldo e consumo

    ![Registros de inventários e auditorias no método PEPS](/image/inventarios_auditoria.gif)

6. 📝 **Gestão Manual de Dados**
   - Inserção, edição e exclusão de registros diretamente pelo sistema

7. 💾 **Sistema de Backup de Banco de Dados**
   - Backup manual sob demanda
   - Backup automático com agendamento personalizável
   - Restauração fácil e gerenciamento de versões antigas

    ![Sistema de Gerenciamento de Backup de Banco de Dados](/image/backup_restauracao.gif)

8. 🧾 **Extração Inteligente de Cupons Não Fiscais Usando IA**
   - Permite capturar cupons de supermercados ou vendas com imagem da câmera ou upload
   - Extrai automaticamente os dados com IA usando Gemini
   - Sugere o fornecedor automaticamente com base no CNPJ ou nome aproximado
   - Permite seleção manual do fornecedor com preenchimento automático
   - Aplica sugestões inteligentes de matching com produtos previamente cadastrados
   - Interface amigável para revisão e edição final dos dados extraídos antes do salvamento

---

### 🏗️ Funcionalidades em Desenvolvimento

1. **📘 Fichas Técnicas Gerenciais**
   - Cadastro completo de fichas técnicas para controle de produção e custo:
     - Ingredientes base (matéria-prima principal)
     - Acompanhamentos e complementos
     - Custo por unidade, por porção e rendimento da receita

2. **📊 Integração com Dashboards de Gestão**
   - Painéis interativos com informações em tempo real sobre:
     - **Estoque crítico** (alertas automatizados para reposição)
     - **Variação de preços** por fornecedor ao longo do tempo
     - **Custos operacionais detalhados** por produto, prato ou categoria

3. **📈 Relatórios de Eficiência e Inteligência de Compras**
   - Comparativo de custo-benefício entre produtos similares
   - Evolução histórica de preços por item e fornecedor
   - Identificação de tendências sazonais e oportunidades de compra

4. **🧠 Módulo Inteligente de Apoio à Decisão**
   - Recomendação de fornecedores com base em custo, qualidade e frequência de entrega
   - Sugestões de compras e produção otimizadas com base em séries temporais
   - Alertas preventivos para evitar perdas por vencimento ou excesso de estoque

#### 📌 Benefícios Esperados

- ✅ **Redução de custos** com negociações mais eficientes baseadas em dados reais
- ✅ **Economia de tempo** com automação de tarefas manuais e operacionais
- ✅ **Precisão operacional** por meio de dados padronizados e relatórios claros
- ✅ **Escalabilidade e flexibilidade** para adaptação a novos produtos, fornecedores e processos

#### 🗺️ Roadmap Futuro

- 🔍 Implementação de IA para recomendação de compras e previsão de demanda
- 🛒 Integração com marketplaces e ERPs para automação de pedidos
- 📱 Aplicativo mobile para inventário e leitura de notas via smartphone
- 🌐 API pública para integração com outras plataformas de gestão

## 🚀 Instalação

### 📋 Pré-requisitos

Antes de começar, verifique se você possui

- ✅ Python 3.11 ou superior instalado
- ✅ Git instalado na sua máquina
- ✅ Servidor MySQL ou PostgreSQL em execução
- ✅ Poetry instalado (gerenciador de dependências)

**Siga estes passos para configurar o projeto:**

#### 1. Clonar o repositório

  ```bash
  git clone https://github.com/WolkerDias/gestao-simples.git
  cd gestao-simples
  ```

#### 2. Configurar Ambiente Virtual

Recomendamos o uso do Poetry para gerenciamento de dependências:

  ```bash
  # Instalar Poetry (caso não tenha)
  pip install poetry

  # Instalar dependências do projeto
  poetry install
  ```

#### 3. Configurar Banco de Dados

Antes de iniciar o projeto, configure suas credenciais de banco de dados:

- Crie o banco de dados MySQL ou PostgreSQL:

  ```sql
  CREATE DATABASE db_gestao;
  ```

- Copie o arquivo `.env.example` e renomeie para `.env`:

  ```bash
    cp .env.example .env
  ```

- Adicione ao `.gitignore` (caso ainda não tenha feito):

  ```.gitignore
    # Arquivo de variáveis de ambiente (não versionar)
    .env
  ```

- Preencha com suas credenciais do banco de dados:
  - Opção 1:

    - Ir para a seção [🚦 Iniciando o Sistema](#-iniciando-o-sistema)
    - Configurar na tela de configuração de banco de dados
    - Reiniciar o servidor após salvar as configurações

  - Opção 2:
    - Editar o arquivo `.env` manualmente

      ```.env
      # Configuração do tipo de banco de dados (mysql ou postgres)
      DB_TYPE='mysql'

      # 🛢️ Configurações de acesso ao banco de dados
      DB_USER=root            # 👤 Seu usuário
      DB_PASSWORD=sua_senha   # 🔑 Sua senha
      DB_HOST=localhost       # 🌐 Servidor MySQL ou PostgreSQL
      DB_NAME=db_gestao       # 🗃️ Nome do banco
      DB_PORT='3602'
      ```

## 🚦 Iniciando o Sistema

### Ativar ambiente virtual

```bash
poetry env activate
```

### Entrar no diretório do projeto

```bash
cd gestao_simples
```

### Iniciar aplicação

```bash
poetry run streamlit run app.py
```

Acesse no navegador: 🌐 <http://localhost:8501>

## 📦 Empacotamento e Distribuição

### Gerar executável com cx_Freeze

```bash
poetry run python setup.py build 
```

### 📦 Gerar instalador com Inno Setup

1. Baixe e instale o Inno Setup Compiler:
   👉 [Download Inno Setup (JRSoftware)](https://jrsoftware.org/isdl.php)

2. Abra o arquivo `inno/setup_gestao_simples.iss` com o Inno Setup

3. Pressione `Ctrl + F9` ou clique em **Compile** para gerar o instalador `.exe` no diretório `\dist\vX.X.X`.

## 🗂️ Estrutura do Projeto

```bash
gestao-simples/
├──📂 gestao_simples/     # Pacote principal (diretório com códigos Python)
│  ├──📂 config/          # Configurações do sistema
│  │  ├──📜 database.py   # Conexão com MySQL ou PostgreSQL
│  │  └──📜 settings.py   # Configurações gerais do sistema
│  ├──📂 models/          # Modelos de dados
│  ├──📂 repositories/    # Camada de repositórios
│  ├──📂 services/        # Lógica de negócio
│  ├──📂 utils/           # Funções utilitárias
│  ├──📂 views/           # Interfaces
│  ├──📜 __init__.py      # Inicializador do pacote
│  ├──📜 .env             # Variáveis de ambiente (cópia de .env.example)
│  └──📜 app.py           # Aplicação principal
│
├──📂 inno/               # Scripts para gerar instalador com Inno Setup
│  ├──📜 setup_gestao_simples.iss # Script de instalação
│  └──📜 BrazilianPortuguese.isl  # Tradução do instalador
│
├──📂 build/              # (Ignorado no Git) Saída do cx_Freeze
├──📂 dist/               # (Ignorado no Git) Executável gerado
│
├──📜 app_launcher.py     # Arquivo para inicialização (launcher)
├──📜 setup.py            # Script cx_Freeze para empacotamento
├──📜 .gitignore          # Arquivos ignorados pelo Git
├──📜 pyproject.toml      # Configuração do Poetry
└──📜 README.md           # Este arquivo
```

### 📝 Observações Importantes

- Diretórios com `.` (`.backups`, `.capturas`, `.logs`) são criados automaticamente em `tmp` ao executar o projeto
- Os diretórios `__pycache__` são gerados pelo Python para cache de módulos compilados

## 🆘 Problemas comuns

### Erro de conexão com baco de dados

- Verifique se o servidor está online
- Confira usuário/senha no `.env`
- Garanta privilégios de acesso ao banco

### Dependências não instaladas

  ```bash
  poetry install --sync
  ```

## 🤝 Como Contribuir

1. Faça um Fork do projeto

2. Crie sua branch:

    ```bash
    git checkout -b minha-feature
    ```

3. Commit suas alterações:

    ```bash
    git commit -m 'Adicionei uma nova feature'
    ```

4. Envie para o repositório:

    ```bash
    git push origin minha-feature
    ```

5. Abra um Pull Request

## 📄 Licença

Distribuído sob licença MIT. Consulte o arquivo [LICENSE](LICENSE) para detalhes.

**Contato do desenvolvedor:**  

[![Email](https://img.shields.io/badge/Email-wolker.sd@hotmail.com-blue?logo=microsoft-outlook)](mailto:wolker.sd@hotmail.com)
[![LinkedIn](https://img.shields.io/badge/%40wolkerdias-Linkedin-blue)](https://www.linkedin.com/in/wolkerdias)
