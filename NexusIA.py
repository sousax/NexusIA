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

# --- Funções de Pré-processamento e Extração de Texto ---

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
    # Converte a imagem para o formato que o OpenCV consegue usar
    img_cv = np.array(imagem)
    
    # 1. Converter para escala de cinza
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # 2. Binarização (Thresholding) - Converte para preto e branco puro.
    # Adaptive thresholding é excelente para documentos com iluminação não uniforme.
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    return thresh

# Na Célula 3 do seu código Colab ou no seu script Streamlit

# Substitua a sua função antiga por esta versão mais segura

def extrair_texto_pdf_hibrido(arquivo_pdf_bytes):
    """
    Extrai texto de um PDF usando uma abordagem híbrida e segura.
    """
    texto_completo = ""
    
    # 1. TENTATIVA RÁPIDA (PDF DIGITAL)
    try:
        with pdfplumber.open(arquivo_pdf_bytes) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text(x_tolerance=2)
                # Garante que o texto da página não seja None antes de o juntar
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
    except Exception:
        # Se o pdfplumber falhar, garantimos que texto_completo continua a ser uma string vazia
        texto_completo = ""

    # <<< MUDANÇA AQUI: Adicionada verificação para 'None' >>>
    # Esta verificação dupla impede o erro.
    # 1º: Verifica se `texto_completo` não é None.
    # 2º: Se não for, então verifica se não está em branco.
    if texto_completo and texto_completo.strip():
        st.info("PDF digital detectado. Extração rápida concluída.")
        return texto_completo

    # 2. SE FALHAR, TENTATIVA LENTA (OCR EM PDF ESCANEADO)
    st.info("PDF sem texto detectado. Iniciando OCR com Tesseract...")
    
    texto_ocr = ""
    try:
        # É importante voltar ao início do ficheiro antes de o ler novamente
        arquivo_pdf_bytes.seek(0)
        imagens_pdf = convert_from_bytes(arquivo_pdf_bytes.read())
        
        progress_bar = st.progress(0)
        for i, imagem in enumerate(imagens_pdf):
            st.write(f"Processando página {i+1}/{len(imagens_pdf)}...")
            imagem_processada = preprocessar_imagem_para_ocr(imagem)
            texto_ocr += pytesseract.image_to_string(imagem_processada, lang='por+eng') + "\n"
            progress_bar.progress((i + 1) / len(imagens_pdf))
            
        st.success("Processamento OCR concluído!")
        return texto_ocr
        
    except Exception as e:
        if "Unable to get page count" in str(e):
            st.error("Erro: O ficheiro PDF parece estar corrompido. Por favor, tente a solução 'Imprimir para PDF' e envie o novo ficheiro.")
        else:
            st.error(f"Ocorreu um erro durante o processo de OCR: {e}")
        return "" # Retorna sempre uma string vazia em caso de erro

    # ... (resto do código da função com a barra de progresso e o pytesseract) ...
    
    # 1. TENTATIVA RÁPIDA (PDF DIGITAL)
    try:
        with pdfplumber.open(arquivo_pdf_bytes) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text(x_tolerance=2) # Tolera pequenos desalinhamentos
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
    except Exception:
        texto_completo = "" # Ignora erros se não for um PDF válido para pdfplumber

    # Se encontrou texto, retorna.
    if texto_completo.strip():
        st.info("PDF digital detectado. Extração rápida concluída.")
        return texto_completo

    # 2. SE FALHAR, TENTATIVA LENTA (OCR EM PDF ESCANEADO)
    st.info("PDF sem texto detectado. Iniciando OCR com Tesseract...")
    
    texto_ocr = ""
    try:
        # Converte o PDF (em bytes) em uma lista de imagens
        imagens_pdf = convert_from_bytes(arquivo_pdf_bytes.read())
        
        progress_bar = st.progress(0)
        for i, imagem in enumerate(imagens_pdf):
            st.write(f"Processando página {i+1}/{len(imagens_pdf)}...")
            
            # Aplica o pré-processamento na imagem
            imagem_processada = preprocessar_imagem_para_ocr(imagem)
            
            # Extrai o texto da imagem limpa (especificando o idioma português)
            texto_ocr += pytesseract.image_to_string(imagem_processada, lang='por+eng') + "\n"
            progress_bar.progress((i + 1) / len(imagens_pdf))
            
        st.success("Processamento OCR concluído!")
        return texto_ocr
    except Exception as e:
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


# --- Interface Gráfica com Streamlit ---

st.set_page_config(page_title="NexusAI OCR", layout="wide")
st.title("🤖 NexusAI: Agente com OCR e Análise de Imagem")
st.markdown("Faça o upload de um PDF **digital ou escaneado**. O agente irá analisar, melhorar a imagem (se necessário) e encontrar os códigos.")

# 1. Carregar a base de dados
NOME_ARQUIVO_BASE = "base_de_dados.xlsx"
df_base, mapa_de_codigos = carregar_base_dados(NOME_ARQUIVO_BASE)

if df_base is not None and mapa_de_codigos:
    st.success(f"Base de dados '{NOME_ARQUIVO_BASE}' carregada. {len(mapa_de_codigos)} códigos únicos prontos para busca.")

    # 2. Upload do arquivo PDF
    pdf_carregado = st.file_uploader("Selecione o arquivo PDF", type="pdf")

    if pdf_carregado:
        st.markdown("---")
        st.subheader("Resultados da Análise")

        start_time = time.time()
        
        # <<< MUDANÇA PRINCIPAL AQUI >>>
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
                # Opcional: Mostrar o texto extraído para depuração
                with st.expander("Ver texto extraído pelo OCR"):
                    st.text_area("Texto", texto_do_pdf, height=300)
        else:
            st.error("Não foi possível extrair nenhum texto do PDF.")

        end_time = time.time()
        st.caption(f"Análise concluída em {end_time - start_time:.2f} segundos.")


