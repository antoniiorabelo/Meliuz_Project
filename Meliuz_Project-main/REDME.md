# 🚀 Analisador AI-Native de Testes A/B | Méliuz Growth

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B)
![Gemini](https://img.shields.io/badge/Google_Gemini-API-8E75B2)
![Google Sheets](https://img.shields.io/badge/Google_Sheets-Integration-34A853)

Uma solução completa, automatizada e com interface visual (Web App) desenvolvida para o case técnico de Estágio em Growth AI-Native da Méliuz. 

Esta ferramenta automatiza a análise de resultados de testes A/B de variação de cashback. Ela realiza a ingestão e tratamento dos dados, calcula métricas de negócio (Lucro Bruto, Ticket Médio, Alavancagem GMV), aciona o LLM do Google (Gemini) para redigir um relatório executivo e envia as conclusões automaticamente para um pipeline de destino no Google Sheets.

---

## 🏗️ Arquitetura da Solução

A solução foi construída com foco em **experiência do usuário (UX)** e **escalabilidade**, substituindo scripts isolados de terminal por uma aplicação web robusta.

* **Interface e Data Viz:** `Streamlit` (Permite upload de CSVs por arrastar e soltar e geração nativa de gráficos).
* **Processamento de Dados (ETL):** `Pandas` (Tratamento de strings monetárias BRL e agregações matemáticas dinâmicas).
* **Motor de Inteligência Artificial:** `google-genai` (SDK unificado v2 do Gemini para análise semântica e decisão de negócios).
* **Pipeline de Carga (Load):** `gspread` (Gravação determinística em tempo real via Service Account API no Google Sheets).

---

## ⚙️ Como Configurar e Executar (Setup Local)

Siga os passos abaixo para testar a aplicação na sua máquina.

### 1. Clonar o Repositório e Instalar Dependências
```bash
# Clone este repositório
git clone [https://github.com/SEU_USUARIO/teste-meliuz-growth.git](https://github.com/SEU_USUARIO/teste-meliuz-growth.git)
cd teste-meliuz-growth

# Crie e ative um ambiente virtual (Recomendado)
python -m venv venv
source venv/bin/activate  # No Windows use: .\venv\Scripts\activate

# Instale as dependências mapeadas
pip install -r requirements.txt