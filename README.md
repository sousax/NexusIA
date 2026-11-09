# NexusAI

Agente para conferência de Part Number × NCM × descrição em documentos logísticos: lê um PDF, encontra os Part Numbers que existem na base da empresa (Excel) e mostra NCM, descrição e demais colunas de cada um.

No ar em **https://nexusaidsv.streamlit.app/**

## Contexto

Conferir manualmente os Part Numbers de documentos como Declarações de Importação (DIs) é lento, repetitivo e sujeito a erro, o que pode gerar atrasos e problemas fiscais. O NexusAI automatiza essa conferência cruzando o documento com a base de dados.

## Funcionalidades

- **Upload de PDF digital ou escaneado**: PDFs com texto são lidos direto (pdfplumber); sem texto, cada página passa por pré-processamento de imagem (escala de cinza + binarização adaptativa com OpenCV) e OCR com Tesseract (`por+eng`).
- **Busca tolerante a formatação**: hífens, barras, pontos e espaços são ignorados na comparação, então `ABC-123.4` no PDF casa com `ABC1234` na base.
- **Tabela de resultados** com todas as linhas da base para os códigos encontrados.
- **Pesquisa manual por Part Number**: busca exata e, se não achar, busca aproximada (por trecho do código).
- Sem correspondência, mostra o texto extraído para conferência.

## Tecnologias

- Python 3.11, Streamlit
- pandas + openpyxl (base Excel)
- pdfplumber (PDF com texto)
- pytesseract, pdf2image, OpenCV (OCR)

## Como rodar

A base de dados não está no repositório. Coloque na raiz um `base_de_dados.xlsx` com uma coluna `Código` (as demais colunas, como NCM e descrição, aparecem no resultado).

```bash
# binários do sistema (lista em packages.txt) — Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-por poppler-utils

pip install -r requirements.txt
streamlit run NexusIA.py   # http://localhost:8501
```

O repositório também tem um `.devcontainer` que instala tudo e sobe o app no GitHub Codespaces.

## Melhorias futuras

- Suporte a outros formatos (.docx, .csv, .txt).
- Migrar a base do Excel para SQLite ou PostgreSQL em bases muito grandes.
