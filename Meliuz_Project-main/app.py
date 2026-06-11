import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types  # Importante para configurar o comportamento do Chat
import gspread

# === 1. CONFIGURAÇÃO DA PÁGINA E MEMÓRIA (STATE) ===
st.set_page_config(page_title="Méliuz Growth | Testes A/B", page_icon="🚀", layout="wide")

# Inicializa as variáveis na memória para não sumirem quando o Streamlit recarregar
if "relatorio_gerado" not in st.session_state:
    st.session_state.relatorio_gerado = False
if "texto_relatorio" not in st.session_state:
    st.session_state.texto_relatorio = ""
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

st.title("🚀 Analisador AI-Native de Testes A/B")
st.markdown("Faça o upload do ficheiro CSV do parceiro para visualizar os dados, gerar o relatório do Gemini, enviar para o Sheets e conversar com a IA sobre os resultados.")

# === 2. AUTENTICAÇÃO ===
load_dotenv()
CHAVE_API = os.getenv("GEMINI_API_KEY")

if not CHAVE_API:
    st.error("❌ Chave da API do Gemini não encontrada. Verifique o ficheiro .env.")
    st.stop()

# Guarda o cliente na memória para a conexão não fechar durante o chat
if "api_client" not in st.session_state:
    st.session_state.api_client = genai.Client(api_key=CHAVE_API)

client = st.session_state.api_client

# === 3. UPLOAD DO FICHEIRO E TRATAMENTO ===
ficheiro_carregado = st.file_uploader("Arraste e solte o ficheiro CSV do teste aqui", type=["csv"])

if ficheiro_carregado is not None:
    def limpar_moeda(valor):
        if pd.isna(valor): return 0.0
        valor_limpo = str(valor).replace('R$', '').replace('.', '').strip()
        return float(valor_limpo)

    df = pd.read_csv(ficheiro_carregado)
    
    colunas_financeiras = ['comissão', 'cashback', 'vendas totais']
    for coluna in colunas_financeiras:
        df[coluna] = df[coluna].apply(limpar_moeda)

    df_agrupado = df.groupby('Grupos de usuários')[['compradores', 'comissão', 'cashback', 'vendas totais']].sum().reset_index()
    df_agrupado['lucro_bruto'] = df_agrupado['comissão'] - df_agrupado['cashback']
    df_agrupado['alavancagem_gmv'] = df_agrupado['vendas totais'] / df_agrupado['cashback']
    df_agrupado['ticket_medio'] = df_agrupado['vendas totais'] / df_agrupado['compradores']
    df_agrupado = df_agrupado.sort_values(by='lucro_bruto', ascending=False)

    st.subheader("📊 Visão Geral da Performance")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.dataframe(df_agrupado[['Grupos de usuários', 'lucro_bruto', 'alavancagem_gmv']])
    with col2:
        st.bar_chart(data=df_agrupado, x='Grupos de usuários', y='lucro_bruto', color='#ff5722')

    # === 4. BOTÃO GERADOR DO RELATÓRIO E SETUP DO CHAT ===
    st.markdown("---")
    if st.button("🧠 Gerar Relatório Analítico & Guardar no Sheets", type="primary"):
        with st.spinner("O Gemini está a analisar as métricas e a redigir o relatório..."):
            
            dados_em_texto = df_agrupado.to_string(index=False)
            parceiro_nome = df['Parceiro'].iloc[0] if 'Parceiro' in df.columns else "Desconhecido"
            vencedor_grupo = df_agrupado.iloc[0]['Grupos de usuários']
            lucro_vencedor = float(df_agrupado.iloc[0]['lucro_bruto'])
            gmv_vencedor = float(df_agrupado.iloc[0]['vendas totais'])
            alavancagem_vencedor = float(df_agrupado.iloc[0]['alavancagem_gmv'])
            ticket_vencedor = float(df_agrupado.iloc[0]['ticket_medio'])

            prompt = f"""
            Você é um Analista de Growth Sênior IA na Méliuz. 
            Acabamos de rodar um Teste A/B de variação de cashback com o parceiro {parceiro_nome}.
            [DADOS CONSOLIDADOS DO TESTE]
            {dados_em_texto}
            Escreva um relatório executivo indicando a Rentabilidade, Tração, Eficiência e Ticket Médio.
            Conclua com a variante a escalar e justifique. Responda em Markdown.
            """

            try:
                # Gera o relatório principal
                resposta = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                # Guarda na memória do Streamlit
                st.session_state.texto_relatorio = resposta.text
                st.session_state.relatorio_gerado = True
                
                # Prepara a IA do Chat passando o contexto (dados e relatório) de forma invisível
                instrucao_chat = f"""
                Você é um consultor analítico de Growth da Méliuz. O usuário vai fazer perguntas 
                sobre o teste A/B do parceiro {parceiro_nome}. 
                
                DADOS DO TESTE:
                {dados_em_texto}
                
                CONCLUSÃO DO RELATÓRIO GERADO:
                {resposta.text}
                
                Responda às perguntas do usuário com foco em dados, negócios e de forma objetiva.
                """
                
                st.session_state.chat_session = client.chats.create(
                    model='gemini-2.5-flash',
                    config=types.GenerateContentConfig(system_instruction=instrucao_chat)
                )
                
                # Saudação inicial do Chatbot
                st.session_state.mensagens = [{"role": "assistant", "content": f"Relatório do {parceiro_nome} gerado! O que gostaria de aprofundar ou questionar sobre os dados?"}]
                
                # Integração Google Sheets
                st.info("A sincronizar com a Base de Dados (Google Sheets)...")
                if not os.path.exists('credenciais.json'):
                    st.warning("⚠️ Ficheiro 'credenciais.json' não encontrado. Integração ignorada.")
                else:
                    conta_servico = gspread.service_account(filename='credenciais.json')
                    url_planilha = "https://docs.google.com/spreadsheets/d/1USRz8BlP5bjTKfyGxi7aysFL4QZw7K-7GV9UzA1FPFU/edit?gid=0#gid=0"
                    
                    planilha = conta_servico.open_by_url(url_planilha)
                    aba = planilha.sheet1
                    
                    todos_valores = aba.get_all_values()
                    linhas_preenchidas = [linha for linha in todos_valores if any(celula.strip() for celula in linha)]
                    proxima_linha = len(linhas_preenchidas) + 1
                    
                    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
                    decisao_str = f"Escalar {vencedor_grupo} para 100% do tráfego."
                    
                    nova_linha = [data_atual, parceiro_nome, vencedor_grupo, round(lucro_vencedor, 2), round(gmv_vencedor, 2), round(alavancagem_vencedor, 2), round(ticket_vencedor, 2), decisao_str]
                    
                    aba.update(range_name=f"A{proxima_linha}:H{proxima_linha}", values=[nova_linha], value_input_option="USER_ENTERED")
                    st.success(f"📈 Sincronização concluída na linha {proxima_linha}.")
                    
            except Exception as e:
                st.error(f"❌ Erro durante o processo: {e}")

# === 5. EXIBIÇÃO DO RELATÓRIO E INTERFACE DO CHAT ===
# (Isto fica fora do botão para não desaparecer quando interagir com o chat)
if st.session_state.relatorio_gerado:
    st.markdown("---")
    st.success("✅ Relatório Analítico:")
    st.markdown(st.session_state.texto_relatorio)
    
    st.markdown("---")
    st.subheader("💬 Tire dúvidas com o Analista IA")
    
    # Exibe o histórico de mensagens
    for msg in st.session_state.mensagens:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Caixa de entrada do utilizador
    if pergunta_utilizador := st.chat_input("Ex: Por que motivo a alavancagem caiu tanto no Grupo 3?"):
        # Adiciona a pergunta ao histórico e exibe
        st.session_state.mensagens.append({"role": "user", "content": pergunta_utilizador})
        with st.chat_message("user"):
            st.markdown(pergunta_utilizador)

        # Pede resposta ao Gemini
        with st.chat_message("assistant"):
            with st.spinner("A analisar..."):
                resposta_chat = st.session_state.chat_session.send_message(pergunta_utilizador)
                st.markdown(resposta_chat.text)
                
        # Guarda a resposta no histórico
        st.session_state.mensagens.append({"role": "assistant", "content": resposta_chat.text})