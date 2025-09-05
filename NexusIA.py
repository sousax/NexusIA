# Importando as bibliotecas necessárias
import streamlit as st
import pandas as pd
import pdfplumber
import re
import time # Para medir o tempo de execução

# --- Funções do Agente (Lógica Atualizada) ---

@st.cache_data # Cache para otimizar o carregamento
def carregar_base_dados(caminho_arquivo):
    """
    Carrega a base de dados do Excel e retorna o DataFrame completo
    e um CONJUNTO (set) otimizado de Part Numbers para busca rápida.
    """
    try:
        df = pd.read_excel(caminho_arquivo)
        if 'Código' not in df.columns:
            st.error("Erro: A coluna 'Código' não foi encontrada na base de dados.")
            return None, None

        df['Código'] = df['Código'].astype(str)
        # Criar um conjunto (set) de Códigos é CRUCIAL para a performance.
        # Buscar um item em um set é milhares de vezes mais rápido do que em uma lista.
        codigos_validos = set(df['Código'])
        return df, codigos_validos

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

def buscar_pns_por_comparacao_direta(texto_pdf, pns_validos_set):
    """
    Quebra o texto do PDF em palavras e verifica cada uma contra o conjunto
    de Part Numbers válidos.
    """
    # 1. Limpeza e Tokenização:
    #    - Remove pontuações comuns que podem estar "coladas" nos Part Numbers.
    #    - Divide o texto em "palavras" (tokens).
    texto_limpo = re.sub(r'[(),:;!?"\'`]', ' ', texto_pdf) # Substitui pontuação por espaço
    palavras_do_pdf = set(texto_limpo.split()) # Usa set para evitar verificar a mesma palavra várias vezes

    # 2. Comparação:
    #    - Encontra a interseção entre as palavras do PDF e os PNs válidos.
    #    - É extremamente rápido por usar operações de conjunto (set).
    pns_encontrados = palavras_do_pdf.intersection(pns_validos_set)

    return list(pns_encontrados)


# --- Interface Gráfica com Streamlit ---

st.set_page_config(page_title="Agente de Busca Dinâmica", layout="wide")

st.title("🤖 Agente de Busca Dinâmica de Part Numbers")
st.markdown("Faça o upload de um PDF. O agente irá comparar as palavras do documento com sua base de dados.")

# 1. Carregar a base de dados
NOME_ARQUIVO_BASE = "base_de_dados.xlsx"
df_base, pns_validos = carregar_base_dados(NOME_ARQUIVO_BASE)

if df_base is not None:
    st.success(f"Base de dados '{NOME_ARQUIVO_BASE}' carregada. {len(pns_validos)} Part Numbers únicos prontos para busca.")

    # 2. Upload do arquivo PDF
    pdf_carregado = st.file_uploader("Selecione o arquivo PDF", type="pdf")

    if pdf_carregado:
        st.markdown("---")
        st.subheader("Resultados da Análise")

        # Inicia a contagem de tempo
        start_time = time.time()

        # Extrai o texto
        texto_do_pdf = extrair_texto_pdf(pdf_carregado)

        if texto_do_pdf:
            # A nova função de busca!
            pns_encontrados_lista = buscar_pns_por_comparacao_direta(texto_do_pdf, pns_validos)

            if pns_encontrados_lista:
                # Mostra os PNs encontrados
                st.write(f"**{len(pns_encontrados_lista)}** Part Numbers correspondentes encontrados no PDF:")
                st.info(", ".join(pns_encontrados_lista))

                # Filtra o DataFrame original para mostrar os detalhes
                st.markdown("---")
                st.subheader("Itens encontrados na sua Base de Dados:")
                resultados_finais = df_base[df_base['Código'].isin(pns_encontrados_lista)]
                st.dataframe(resultados_finais, use_container_width=True)

            else:
                st.warning("Nenhuma palavra no PDF correspondeu a um Part Number da sua base de dados.")
        else:
            st.error("Não foi possível extrair texto do PDF. O arquivo pode ser uma imagem escaneada.")

        # Mostra o tempo de execução
        end_time = time.time()
        st.caption(f"Análise concluída em {end_time - start_time:.2f} segundos.")