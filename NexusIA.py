# Importando as bibliotecas necessárias
import streamlit as st
import pandas as pd
import pdfplumber
import re
import time

# --- Funções do Agente (Lógica Atualizada e Mais Robusta) ---

@st.cache_data
def carregar_base_dados(caminho_arquivo):
    """
    Carrega a base de dados do Excel e retorna o DataFrame completo
    e um DICIONÁRIO DE MAPEAMENTO para busca flexível.
    """
    try:
        df = pd.read_excel(caminho_arquivo)
        if 'Código' not in df.columns:
            st.error("Erro: A coluna 'Código' não foi encontrada na base de dados.")
            return None, None

        df['Código'] = df['Código'].astype(str)
        
        # <<< MUDANÇA AQUI: CRIANDO O MAPA DE CÓDIGOS >>>
        # Para cada código, criamos uma versão "normalizada" (sem -, /, .)
        # O mapa associa a versão normalizada ao código original.
        # Ex: {'70415202': '70415-202'}
        codigo_map = {
            re.sub(r'[-/.\s]', '', codigo): codigo 
            for codigo in df['Código'].dropna().unique()
        }
        
        return df, codigo_map

    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return None, None
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler o arquivo Excel: {e}")
        return None, None

def extrair_texto_pdf(arquivo_pdf):
    """Extrai todo o texto de um arquivo PDF."""
    texto_completo = ""
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_completo += texto + "\n"
    return texto_completo

# <<< MUDANÇA AQUI: NOVA FUNÇÃO DE BUSCA FLEXÍVEL >>>
def buscar_codigos_com_mapeamento(texto_pdf, codigo_map):
    """
    Busca códigos no texto do PDF de forma flexível, normalizando 
    os dados antes de comparar com o mapa de códigos.
    """
    # 1. Limpeza e extração de "palavras" do PDF
    texto_limpo = re.sub(r'[(),:;!?"\'`]', ' ', texto_pdf)
    palavras_do_pdf = set(texto_limpo.split())

    codigos_encontrados_originais = set()

    # 2. Comparação Normalizada
    for palavra in palavras_do_pdf:
        # Normaliza a palavra do PDF (remove -, /, .)
        palavra_normalizada = re.sub(r'[-/.\s]', '', palavra)
        
        # Procura a versão normalizada no nosso mapa
        if palavra_normalizada in codigo_map:
            # Se encontrar, adiciona o CÓDIGO ORIGINAL à nossa lista de resultados
            codigo_original = codigo_map[palavra_normalizada]
            codigos_encontrados_originais.add(codigo_original)

    return list(codigos_encontrados_originais)


# --- Interface Gráfica com Streamlit ---

st.set_page_config(page_title="Agente de Busca Flexível", layout="wide")
st.title("🤖 Agente de Busca Dinâmica e Flexível")
st.markdown("Faça o upload de um PDF. O agente irá encontrar os códigos, mesmo que o formato (com ou sem `-`) seja diferente da base de dados.")

# 1. Carregar a base de dados
NOME_ARQUIVO_BASE = "base_de_dados.xlsx"
# <<< MUDANÇA AQUI >>>
df_base, mapa_de_codigos = carregar_base_dados(NOME_ARQUIVO_BASE)

# <<< MUDANÇA AQUI >>>
if df_base is not None and mapa_de_codigos:
    st.success(f"Base de dados '{NOME_ARQUIVO_BASE}' carregada. {len(mapa_de_codigos)} códigos únicos prontos para busca.")

    # 2. Upload do arquivo PDF
    pdf_carregado = st.file_uploader("Selecione o arquivo PDF", type="pdf")

    if pdf_carregado:
        st.markdown("---")
        st.subheader("Resultados da Análise")

        start_time = time.time()
        texto_do_pdf = extrair_texto_pdf(pdf_carregado)

        if texto_do_pdf:
            # <<< MUDANÇA AQUI: Usando a nova função de busca >>>
            codigos_encontrados_lista = buscar_codigos_com_mapeamento(texto_do_pdf, mapa_de_codigos)

            if codigos_encontrados_lista:
                st.write(f"**{len(codigos_encontrados_lista)}** Códigos correspondentes encontrados no PDF:")
                st.info(", ".join(codigos_encontrados_lista))

                st.markdown("---")
                st.subheader("Itens encontrados na sua Base de Dados:")
                resultados_finais = df_base[df_base['Código'].isin(codigos_encontrados_lista)]
                st.dataframe(resultados_finais, use_container_width=True)

            else:
                st.warning("Nenhum código no PDF correspondeu à sua base de dados.")
        else:
            st.error("Não foi possível extrair texto do PDF. O arquivo pode ser uma imagem escaneada ou estar em branco.")

        end_time = time.time()
        st.caption(f"Análise concluída em {end_time - start_time:.2f} segundos.")
