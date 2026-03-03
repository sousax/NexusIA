# Importando as bibliotecas necessárias
import streamlit as st
import pandas as pd
import pdfplumber
import re
import time

# Novas importações para OCR e processamento de imagem
import pytesseract
from pdf2image import convert_from_bytes
import cv2
import numpy as np

# =========================================================
# Funções de Pré-processamento e Extração de Texto
# =========================================================

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

        # Mapa: código_normalizado -> código_original
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


def preprocessar_imagem_para_ocr(imagem):
    """
    Aplica técnicas de pré-processamento em uma imagem para melhorar a precisão do OCR.
    """
    img_cv = np.array(imagem)

    # Converter para escala de cinza
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Binarização (Adaptive Threshold)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    return thresh


def extrair_texto_pdf_hibrido(arquivo_pdf_bytes):
    """
    Extrai texto de um PDF usando uma abordagem híbrida e segura:
    1) tenta pdfplumber (PDF digital)
    2) se falhar/sem texto, faz OCR (PDF escaneado)
    """
    texto_completo = ""

    # 1) TENTATIVA RÁPIDA (PDF DIGITAL)
    try:
        arquivo_pdf_bytes.seek(0)
        with pdfplumber.open(arquivo_pdf_bytes) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text(x_tolerance=2)
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
    except Exception:
        texto_completo = ""

    if texto_completo and texto_completo.strip():
        st.info("PDF digital detectado. Extração rápida concluída.")
        return texto_completo

    # 2) OCR (PDF ESCANEADO)
    st.info("PDF sem texto detectado. Iniciando OCR com Tesseract...")

    try:
        arquivo_pdf_bytes.seek(0)
        imagens_pdf = convert_from_bytes(arquivo_pdf_bytes.read())

        progress_bar = st.progress(0)
        texto_ocr = ""

        for i, imagem in enumerate(imagens_pdf):
            st.write(f"Processando página {i+1}/{len(imagens_pdf)}...")
            imagem_processada = preprocessar_imagem_para_ocr(imagem)
            texto_ocr += pytesseract.image_to_string(imagem_processada, lang='por+eng') + "\n"
            progress_bar.progress((i + 1) / len(imagens_pdf))

        st.success("Processamento OCR concluído!")
        return texto_ocr

    except Exception as e:
        if "Unable to get page count" in str(e):
            st.error("Erro: O ficheiro PDF parece estar corrompido. Tente 'Imprimir para PDF' e envie o novo ficheiro.")
        else:
            st.error(f"Ocorreu um erro durante o processo de OCR: {e}")
        return ""


def buscar_codigos_com_mapeamento(texto_pdf, codigo_map):
    """Busca códigos no texto de forma flexível."""
    texto_limpo = re.sub(r'[(),:;!?"\'`]', ' ', texto_pdf)
    palavras_do_pdf = set(texto_limpo.split())
    codigos_encontrados_originais = set()

    for palavra in palavras_do_pdf:
        palavra_normalizada = re.sub(r'[-/.\s]', '', palavra)
        if palavra_normalizada in codigo_map:
            codigo_original = codigo_map[palavra_normalizada]
            codigos_encontrados_originais.add(codigo_original)

    return list(codigos_encontrados_originais)


def buscar_partnumber_na_base(consulta, df_base, codigo_map):
    """
    Busca um partnumber digitado pelo usuário, usando o mesmo mapeamento flexível.
    Retorna (df_resultado, codigo_original_encontrado_ou_None).
    """
    if not consulta:
        return pd.DataFrame(), None

    consulta_norm = re.sub(r'[-/.\s]', '', str(consulta).strip())

    # 1) Match exato via mapa (flexível)
    if consulta_norm in codigo_map:
        codigo_original = codigo_map[consulta_norm]
        df_res = df_base[df_base['Código'].astype(str) == str(codigo_original)]
        return df_res, codigo_original

    # 2) Fallback: busca aproximada (substring) na coluna normalizada
    cod_norm_series = df_base['Código'].astype(str).apply(lambda x: re.sub(r'[-/.\s]', '', x))
    mask = cod_norm_series.str.contains(consulta_norm, na=False)

    df_res = df_base[mask]
    return df_res, None


# =========================================================
# Interface Gráfica com Streamlit
# =========================================================

st.set_page_config(page_title="NexusAI OCR", layout="wide")
st.title("🤖 NexusAI: Agente com OCR e Análise de Imagem")
st.markdown("Faça o upload de um PDF **digital ou escaneado**. O agente irá analisar, melhorar a imagem (se necessário) e encontrar os códigos.")

# 1. Carregar a base de dados
NOME_ARQUIVO_BASE = "base_de_dados.xlsx"
df_base, mapa_de_codigos = carregar_base_dados(NOME_ARQUIVO_BASE)

if df_base is not None and mapa_de_codigos:
    st.success(f"Base de dados '{NOME_ARQUIVO_BASE}' carregada. {len(mapa_de_codigos)} códigos únicos prontos para busca.")

    # =====================================================
    # NOVO: Barra de pesquisa por partnumber/código
    # =====================================================
    st.markdown("---")
    st.subheader("🔎 Pesquisa manual por Partnumber (Código)")
    consulta_partnumber = st.text_input(
        "Digite o Partnumber/Código para pesquisar na base (pode colar com '-' '/' '.' ou espaços):",
        placeholder="Ex: ABC-123 / 45.67"
    )

    if consulta_partnumber:
        df_busca, codigo_ok = buscar_partnumber_na_base(consulta_partnumber, df_base, mapa_de_codigos)

        if not df_busca.empty:
            if codigo_ok:
                st.success(f"Encontrado: {codigo_ok}")
            else:
                st.success("Resultados encontrados (busca aproximada).")

            st.dataframe(df_busca, use_container_width=True)
        else:
            st.warning("Nenhum item encontrado para esse partnumber.")

    # =====================================================
    # Upload do arquivo PDF
    # =====================================================
    st.markdown("---")
    pdf_carregado = st.file_uploader("Selecione o arquivo PDF", type="pdf")

    if pdf_carregado:
        st.markdown("---")
        st.subheader("Resultados da Análise")

        start_time = time.time()

        texto_do_pdf = extrair_texto_pdf_hibrido(pdf_carregado)

        if texto_do_pdf.strip():
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
                with st.expander("Ver texto extraído pelo OCR"):
                    st.text_area("Texto", texto_do_pdf, height=300)
        else:
            st.error("Não foi possível extrair nenhum texto do PDF.")

        end_time = time.time()
        st.caption(f"Análise concluída em {end_time - start_time:.2f} segundos.")

else:
    st.error("Não foi possível carregar a base de dados. Verifique o arquivo e a coluna 'Código'.")
