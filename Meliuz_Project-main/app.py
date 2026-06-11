import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai
import gspread

# === 1. CONFIGURAÇÃO DA PÁGINA (UI) ===
st.set_page_config(page_title="Méliuz Growth | Testes A/B", page_icon="🚀", layout="wide")

st.title("🚀 Analisador AI-Native de Testes A/B")
st.markdown("Faça o upload do ficheiro CSV do parceiro para visualizar os dados, gerar o relatório do Gemini e enviar as conclusões para o Google Sheets.")

# === 2. AUTENTICAÇÃO ===
load_dotenv()
CHAVE_API = os.getenv("GEMINI_API_KEY")

if not CHAVE_API:
    st.error("❌ Chave da API do Gemini não encontrada. Verifique o ficheiro .env.")
    st.stop()

client = genai.Client(api_key=CHAVE_API)

# === 3. UPLOAD DO FICHEIRO (A Magia da Reutilização) ===
ficheiro_carregado = st.file_uploader("Arraste e solte o ficheiro CSV do teste aqui", type=["csv"])

if ficheiro_carregado is not None:
    # --- LIMPEZA DOS DADOS ---
    def limpar_moeda(valor):
        if pd.isna(valor): return 0.0
        valor_limpo = str(valor).replace('R$', '').replace('.', '').strip()
        return float(valor_limpo)

    df = pd.read_csv(ficheiro_carregado)
    
    colunas_financeiras = ['comissão', 'cashback', 'vendas totais']
    for coluna in colunas_financeiras:
        df[coluna] = df[coluna].apply(limpar_moeda)

    # --- MATEMÁTICA E AGRUPAMENTO ---
    df_agrupado = df.groupby('Grupos de usuários')[['compradores', 'comissão', 'cashback', 'vendas totais']].sum().reset_index()
    df_agrupado['lucro_bruto'] = df_agrupado['comissão'] - df_agrupado['cashback']
    df_agrupado['alavancagem_gmv'] = df_agrupado['vendas totais'] / df_agrupado['cashback']
    df_agrupado['ticket_medio'] = df_agrupado['vendas totais'] / df_agrupado['compradores']
    df_agrupado = df_agrupado.sort_values(by='lucro_bruto', ascending=False)

    # --- VISUALIZAÇÃO DE DADOS (Data Viz) ---
    st.subheader("📊 Visão Geral da Performance")
    
    # Cria duas colunas no ecrã para organizar o layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.dataframe(df_agrupado[['Grupos de usuários', 'lucro_bruto', 'alavancagem_gmv']])
    
    with col2:
        # Gráfico nativo automático!
        st.bar_chart(data=df_agrupado, x='Grupos de usuários', y='lucro_bruto', color='#ff5722')

    # --- BOTÃO DA INTELIGÊNCIA ARTIFICIAL ---
    st.markdown("---")
    if st.button("🧠 Gerar Relatório Analítico & Guardar no Sheets", type="primary"):
        with st.spinner("O Gemini está a analisar as métricas e a redigir o relatório..."):
            
            dados_em_texto = df_agrupado.to_string(index=False)
            parceiro_nome = df['Parceiro'].iloc[0] if 'Parceiro' in df.columns else "Desconhecido"

            prompt = f"""
            Você é um Analista de Growth Sênior IA na Méliuz. 
            Acabamos de rodar um Teste A/B de variação de cashback com o parceiro {parceiro_nome}.
            [DADOS CONSOLIDADOS DO TESTE]
            {dados_em_texto}
            Escreva um relatório executivo indicando a Rentabilidade, Tração, Eficiência e Ticket Médio.
            Conclua com a variante a escalar e justifique. Responda em Markdown.
            """

            try:
                # 1. Chama a IA
                resposta = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=prompt
                )
                
                # Exibe o relatório bonito no ecrã
                st.success("✅ Relatório gerado com sucesso!")
                st.markdown(resposta.text)
                
                # 2. Guarda no Google Sheets com granularidade de Engenharia de Dados
                st.info("A sincronizar com a Base de Dados (Google Sheets)...")
                
                if not os.path.exists('credenciais.json'):
                    st.warning("⚠️ Ficheiro 'credenciais.json' não encontrado. Integração ignorada.")
                else:
                    conta_servico = gspread.service_account(filename='credenciais.json')
                    
                    # URL da Folha de Cálculo
                    url_planilha = "https://docs.google.com/spreadsheets/d/1USRz8BlP5bjTKfyGxi7aysFL4QZw7K-7GV9UzA1FPFU/edit?gid=0#gid=0"
                    
                    planilha = conta_servico.open_by_url(url_planilha)
                    aba = planilha.sheet1
                    
                    todos_valores = aba.get_all_values()
                    linhas_preenchidas = [linha for linha in todos_valores if any(celula.strip() for celula in linha)]
                    proxima_linha = len(linhas_preenchidas) + 1
                    
                    # Extração cirúrgica das métricas do grupo vencedor
                    linha_vencedora = df_agrupado.iloc[0]
                    vencedor_grupo = linha_vencedora['Grupos de usuários']
                    lucro_vencedor = float(linha_vencedora['lucro_bruto'])
                    gmv_vencedor = float(linha_vencedora['vendas totais'])
                    alavancagem_vencedor = float(linha_vencedora['alavancagem_gmv'])
                    ticket_vencedor = float(linha_vencedora['ticket_medio'])
                    
                    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
                    decisao_str = f"Escalar {vencedor_grupo} para 100% do tráfego."
                    
                    # Construção da linha com tipagem forte (números como números)
                    nova_linha = [
                        data_atual,                      # A: Data da Análise
                        parceiro_nome,                   # B: Parceiro
                        vencedor_grupo,                  # C: Variante Vencedora
                        round(lucro_vencedor, 2),        # D: Lucro Bruto (R$)
                        round(gmv_vencedor, 2),          # E: GMV Total (R$)
                        round(alavancagem_vencedor, 2),  # F: Alavancagem
                        round(ticket_vencedor, 2),       # G: Ticket Médio
                        decisao_str                      # H: Recomendação
                    ]
                    
                    # Atualiza o intervalo agora de A até H
                    aba.update(range_name=f"A{proxima_linha}:H{proxima_linha}", 
                               values=[nova_linha], 
                               value_input_option="USER_ENTERED")
                    
                    st.success(f"📈 Sincronização concluída! Métricas detalhadas inseridas na linha {proxima_linha}.")
                    
            except Exception as e:
                st.error(f"❌ Erro durante o processo: {e}")