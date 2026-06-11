import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from google import genai
import gspread

# Carrega as variáveis do ficheiro .env
load_dotenv()

# === 1. CONFIGURAÇÃO DA IA (SDK ATUALIZADO) ===
CHAVE_API = os.getenv("GEMINI_API_KEY")
if not CHAVE_API:
    print("❌ Erro: Chave da API do Gemini não encontrada. Verifique o ficheiro .env.")
    sys.exit(1)

client = genai.Client(api_key=CHAVE_API)

# === 2. SELEÇÃO DINÂMICA DO DATASET ===
base_dir = Path(__file__).resolve().parent
pasta_datasets = base_dir / 'teste-meliuz-growth'

# Permite passar o nome do ficheiro pelo terminal ou escolher da lista
if len(sys.argv) > 1:
    nome_ficheiro = sys.argv[1]
else:
    print("=== Ficheiros disponíveis para análise ===")
    ficheiros = list(pasta_datasets.glob("*.csv"))
    
    if not ficheiros:
        print(f"❌ Erro: Nenhum ficheiro CSV encontrado na pasta {pasta_datasets}.")
        sys.exit(1)
        
    for idx, arq in enumerate(ficheiros):
        print(f"[{idx}] {arq.name}")
    
    escolha = input("\nDigite o número do ficheiro ou o nome exato do CSV: ").strip()
    if escolha.isdigit() and int(escolha) < len(ficheiros):
        nome_ficheiro = ficheiros[int(escolha)].name
    else:
        nome_ficheiro = escolha

caminho_arquivo = pasta_datasets / nome_ficheiro

if not caminho_arquivo.exists():
    print(f"❌ Erro: O ficheiro '{nome_ficheiro}' não foi localizado em {pasta_datasets}.")
    sys.exit(1)

print(f"\n🚀 A processar o ficheiro: {nome_ficheiro}...")

# === 3. LIMPEZA AUTOMÁTICA DOS DADOS ===
def limpar_moeda(valor):
    if pd.isna(valor):
        return 0.0
    valor_limpo = str(valor).replace('R$', '').replace('.', '').strip()
    return float(valor_limpo)

df = pd.read_csv(caminho_arquivo)

colunas_financeiras = ['comissão', 'cashback', 'vendas totais']
for coluna in colunas_financeiras:
    df[coluna] = df[coluna].apply(limpar_moeda)

# === 4. TRATAMENTO MATEMÁTICO E AGRUPAMENTO (MÉTRICAS DE GROWTH) ===
df_agrupado = df.groupby('Grupos de usuários')[['compradores', 'comissão', 'cashback', 'vendas totais']].sum().reset_index()

# Criação das métricas estratégicas para o negócio
df_agrupado['lucro_bruto'] = df_agrupado['comissão'] - df_agrupado['cashback']
df_agrupado['alavancagem_gmv'] = df_agrupado['vendas totais'] / df_agrupado['cashback']
df_agrupado['ticket_medio'] = df_agrupado['vendas totais'] / df_agrupado['compradores']

# Ordena pelo maior lucro bruto para identificar o vencedor no topo
df_agrupado = df_agrupado.sort_values(by='lucro_bruto', ascending=False)
dados_em_texto = df_agrupado.to_string(index=False)

# Extração de variáveis dinâmicas para popular a folha de cálculo automaticamente
parceiro_nome = df['Parceiro'].iloc[0] if 'Parceiro' in df.columns else "Desconhecido"
vencedor_grupo = df_agrupado.iloc[0]['Grupos de usuários']
lucro_vencedor = df_agrupado.iloc[0]['lucro_bruto']

# === 5. PROMPT E EXECUÇÃO DA INTELIGÊNCIA ARTIFICIAL ===
prompt = f"""
Você é um Analista de Growth Sênior na Méliuz. 
Acabamos de rodar um Teste A/B de variação de cashback com o parceiro {parceiro_nome} e preciso que analise os resultados abaixo.

[DADOS CONSOLIDADOS DO TESTE]
{dados_em_texto}

Avalie os dados e escreva um relatório executivo para a diretoria. 
Para tomar a sua decisão, pondere as seguintes frentes:
1. Rentabilidade Absoluta: Qual grupo gerou o maior lucro bruto (Comissão - Cashback)?
2. Tração (Volume): Qual grupo atraiu mais compradores únicos e maior volume de vendas totais (GMV)?
3. Eficiência: Avalie a alavancagem (quantos reais em vendas cada R$ 1 de cashback gerou) Vendas Totais / Cashback Total.
4. Ticket Médio: O incentivo fez os usuários gastarem mais por compra(Vendas Totais / Compradores)?

O seu relatório final deve conter:
- Qual variante de cashback devemos escalar pra 100% do tráfego? (Justifique o vencedor).
- Um breve resumo dos pontos fortes do vencedor.

Responda em formato Markdown, de forma clara, objetiva e com linguagem de negócios.
"""

print("\nA gerar o relatório analítico com o Gemini...")
try:
    resposta = client.models.generate_content(
        model='gemini-3.5-flash', 
        contents=prompt
    )

    print("\n================ RELATÓRIO FINAL ================\n")
    print(resposta.text)
    print("\n=================================================")
except Exception as e:
    print(f"\n❌ Ocorreu um erro na comunicação com a API do Gemini: {e}")
    sys.exit(1)

# === 6. REGISTRO AUTOMÁTICO DINÂMICO NO GOOGLE SHEETS (DE Approach) ===
print("\n[Pipeline] Iniciando carga de dados no Google Sheets...")
caminho_credenciais = base_dir / 'credenciais.json'

if not caminho_credenciais.exists():
    print("⚠️ [Aviso] Credenciais não encontradas. Bypass da etapa de carga ativado por segurança.")
else:
    try:
        # 1. Conexão
        print("[Pipeline] Autenticando via Service Account...")
        conta_servico = gspread.service_account(filename=str(caminho_credenciais))
        
        print("[Pipeline] Conectando à planilha via URL direta...")
        # COLE O LINK COMPLETO DA SUA PLANILHA AQUI DENTRO DAS ASPAS:
        url_planilha = "https://docs.google.com/spreadsheets/d/1USRz8BlP5bjTKfyGxi7aysFL4QZw7K-7GV9UzA1FPFU/edit?gid=0#gid=0" 
        
        planilha = conta_servico.open_by_url(url_planilha)
        aba = planilha.sheet1
        
        # 2. Leitura de Estado (Descobrindo a real última linha)
        print("[Pipeline] Lendo estado atual da tabela destino...")
        todos_valores = aba.get_all_values()
        
        # Filtra apenas as linhas que realmente têm algum conteúdo (ignora formatação vazia)
        linhas_preenchidas = [linha for linha in todos_valores if any(celula.strip() for celula in linha)]
        proxima_linha_vazia = len(linhas_preenchidas) + 1
        
        # 3. Transformação (Preparando o payload)
        nome_teste = f"Teste A/B - {parceiro_nome}"
        descricao = f"Avaliação de elasticidade de cashback para o parceiro {parceiro_nome}."
        resultado_str = f"Vencedor: {vencedor_grupo} (Lucro Bruto: R$ {lucro_vencedor:,.2f})"
        decisao_str = f"Escalar o {vencedor_grupo} para 100% do tráfego. Maior rentabilidade."
        
        payload = [[nome_teste, descricao, resultado_str, decisao_str]]
        
        # 4. Carga Determinística (Escrevendo em coordenadas exatas)
        intervalo_destino = f"A{proxima_linha_vazia}:D{proxima_linha_vazia}"
        print(f"[Pipeline] Escrevendo payload nas coordenadas exatas: {intervalo_destino}")
        
        aba.update(range_name=intervalo_destino, values=payload, value_input_option="USER_ENTERED")
        
        # 5. Observabilidade
        print(f"✅ [Sucesso] Transação concluída! Dados gravados visivelmente na linha {proxima_linha_vazia}.")
        
    except Exception as e:
        print(f"❌ [Erro Crítico] Falha no pipeline de carga: {e}")