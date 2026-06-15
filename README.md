# 🚀 Analisador AI-Native de Testes A/B | Méliuz Growth

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B)
![Gemini](https://img.shields.io/badge/Google_Gemini-API-8E75B2)
![Google Sheets](https://img.shields.io/badge/Google_Sheets-Integration-34A853)

Uma solução completa, automatizada e com interface visual (Web App) desenvolvida para o case técnico de Estágio em Growth AI-Native da Méliuz. 

Esta ferramenta automatiza a análise de resultados de testes A/B de variação de cashback. Realiza a extração e tratamento dos dados, calcula métricas estratégicas de negócio, aciona o LLM do Google (Gemini) para redigir um relatório executivo, envia as conclusões para um pipeline no Google Sheets e disponibiliza um **Chatbot Interativo** para exploração aprofundada dos resultados.

---

## 🏗️ Arquitetura e Funcionalidades

A solução foi construída com foco em **Experiência do Utilizador (UX)** e **Escalabilidade**, substituindo scripts isolados de terminal por uma aplicação web orientada a dados.

* 📊 **ETL & Data Viz:** `Pandas` e `Streamlit` (Tratamento robusto de strings monetárias BRL, agregações matemáticas dinâmicas e geração de gráficos nativos).
* 🤖 **Motor de IA (Relatório):** `google-genai` (SDK unificado v2 do Gemini para análise semântica, cálculo de Rentabilidade, Tração, Eficiência e recomendação de escala).
* 💬 **Agente Conversacional (Chat):** Implementação de memória de sessão (`st.session_state`) com System Instructions do Gemini, permitindo ao gestor tirar dúvidas sobre os dados em linguagem natural após a geração do relatório.
* 📈 **Pipeline de Carga (Load):** `gspread` (Gravação determinística em tempo real via Service Account API no Google Sheets, utilizando um esquema de 8 colunas fortemente tipadas).

---

## ⚙️ Como Configurar e Executar (Setup Local)

Siga os passos abaixo para testar a aplicação na sua máquina.

### 1. Clonar o Repositório e Instalar Dependências
```bash
# Clone este repositório
git clone https://github.com/antoniiorabelo/Meliuz_Project.git
cd teste-meliuz-growth

# Crie e ative um ambiente virtual (Recomendado)
python -m venv venv

# Ativação no Mac/Linux:
source venv/bin/activate  
# Ativação no Windows:
.\venv\Scripts\activate

# Instale as dependências mapeadas
pip install -r requirements.txt
## 2. Configurar Variáveis de Ambiente (Segurança)

Por boas práticas de segurança cibernética, as chaves não estão expostas no código fonte.

1. Localize o ficheiro `.env.example` na raiz do projeto.
2. Renomeie-o para `.env`.
3. Insira a sua chave de API do Google AI Studio:

```env
GEMINI_API_KEY=sua_chave_de_api_aqui
```

---

## 3. Iniciar o Web App

Sendo uma aplicação interativa, inicialize o servidor local com o comando:

```bash
streamlit run app.py
```

A interface será aberta automaticamente no seu navegador padrão (geralmente em `http://localhost:8501`).

Faça o upload de um dos ficheiros CSV do case e clique em **"Gerar Relatório Analítico"**.

---

# ⚠️ Avisos Importantes e Observabilidade (Troubleshooting)

O sistema foi desenhado para ser resiliente a falhas de rede, limites de cota e ausência de credenciais.

## 1. Integração com o Google Sheets (Ignorada por Segurança)

### O que vai acontecer

Ao executar localmente, a interface avisará que o ficheiro `credenciais.json` não foi encontrado e irá ignorar a gravação no Sheets graciosamente, entregando o relatório e o chat normalmente no ecrã.

### Por que acontece

O ficheiro `.json` com a chave privada da Conta de Serviço foi explicitamente inserido no `.gitignore` para não expor credenciais na web.

### Prova de Conceito

Pode visualizar as cargas de dados já realizadas com sucesso por este script acedendo à folha de cálculo oficial da integração aqui:

> **https://docs.google.com/spreadsheets/d/1USRz8BlP5bjTKfyGxi7aysFL4QZw7K-7GV9UzA1FPFU/edit?usp=sharing**

---

## 2. Erro 429 (Resource Exhausted) / 503 (Unavailable) na API do Gemini

### O que vai acontecer

Uma mensagem de erro indicando:

- `Quota exceeded`
- `Model overloaded`

### Por que acontece

Esta solução utiliza os modelos mais recentes do Google. Se for utilizada uma chave de API do **Free Tier (Plano Gratuito)**, o Google impõe um limite de requisições por minuto (RPM) rígido.

### Como resolver

Este comportamento é esperado na infraestrutura gratuita.

Basta aguardar **60 segundos** para o reset da cota e interagir com o botão ou o chat novamente.

O estado da sessão está protegido e o seu progresso não será perdido.

---

# 📂 Estrutura do Projeto

```plaintext
├── teste-meliuz-growth/       # Pasta com os datasets brutos do case (Parceiros A, B e C)
├── .env.example              # Template de variáveis de ambiente
├── .gitignore                # Exclusão de ficheiros sensíveis e cache
├── app.py                    # Código fonte principal do Web App (Streamlit + Agente IA)
├── README.md                 # Documentação do projeto
└── requirements.txt          # Dependências limpas (Pandas, Streamlit, Google GenAI, etc.)
```

---

## Desenvolvido por

**Antônio Henrique Rabelo Andrade**

Como case técnico para a vaga de **Estágio em Growth AI-Native da Méliuz**.

---
## Vídeo do sistema
