# Projeto NexusAI: Agente de IA para análise de PN, NCM e descrição.

![Flood Alert](https://img.shields.io/badge/Inteligência%20Artificial-Agente%20de%20IA-red)
![Platform](https://img.shields.io/badge/Plataforma-VSCode-purple)
![Microcontroller](https://img.shields.io/badge/VS-Python-blue)

## 📖 Descrição do Projeto

O NexusAI é um agente de inteligência artificial projetado para otimizar e automatizar processos de conferência em sistemas logísticos. A ferramenta analisa documentos em formato PDF, identifica dinamicamente os Part Numbers (PNs) presentes no texto e os valida contra uma base de dados (Excel), retornando as informações correspondentes como NCM e Descrição.

---

## 🎯 Contexto do Problema

A identificação e conferência manual de Part Numbers em documentos, como Declarações de Importação (DIs), é um processo lento, repetitivo e sujeito a erros humanos. Esses erros podem causar atrasos e problemas fiscais. O NexusAI foi criado para mitigar esse problema, oferecendo uma solução automatizada que integra a análise de documentos com a base de dados da empresa, garantindo agilidade e precisão.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem**: Python
* **Interface Web:** Streamlit (temporário)
* **Manipulação de Dados:** Pandas
* **Extração de Dados:** PDFPlumber
* **Leitura do Excel:** Openpyxl 

---

## ⚙️ Explicação de Funcionamento

O sistema opera de forma simples e direta através de uma interface web:
1. Carregamento da Base de Dados: Ao iniciar, o agente carrega a planilha Excel (base_de_dados.xlsx) e cria um conjunto otimizado de todos os Part Numbers válidos. Isso garante que as buscas futuras sejam quase instantâneas.
2. Upload do Documento: O usuário acessa a interface web e faz o upload do arquivo PDF que precisa ser analisado.
3. Extração de Texto: O sistema lê o PDF página por página e extrai todo o conteúdo textual.
4. Busca Dinâmica por Comparação: O agente processa o texto extraído, dividindo-o em palavras individuais. Em seguida, compara cada palavra do documento com a lista de Part Numbers válidos carregada no início.
5. Apresentação dos Resultados: Todos os Part Numbers encontrados no PDF que têm uma correspondência na base de dados são exibidos em uma tabela, juntamente com suas respectivas informações (NCM, Descrição, etc.).

---
## 🚀 Como Replicar o Projeto

**Instruções:**
1.  Tenha Python 3.8 (ou superior) instalado.
2.  Crie uma pasta para o projeto.
3.  Coloque o arquivo de script Python.
4.  Coloque a base de dados com o nome que está no script.

5.  Abra o terminal e digite: `pip install streamlit pandas pdfplumber openpyxl`
6.  Ainda no terminal didite: `streamlist run _nome do arquivo_`

---

## 💡 Melhorias Futuras (Não implementadas)
Este projeto pode ser expandido com as seguintes funcionalidades em uma versão física:
* Suporte a OCR: Integrar uma biblioteca como Pytesseract para permitir a análise de PDFs escaneados (baseados em imagem).
* Suporte a Novos Formatos: Adicionar a capacidade de analisar outros tipos de arquivos, como .docx, .csv e .txt.
* Migração para Banco de Dados: Para bases de dados muito grandes, migrar do Excel para um sistema de banco de dados mais robusto como SQLite ou PostgreSQL para melhorar a performance.

Feito por:

Eduardo Sousa.
