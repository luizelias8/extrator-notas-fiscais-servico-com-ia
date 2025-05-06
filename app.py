import os
import base64
import json
import pandas as pd
from dotenv import load_dotenv
import ast
import fitz  # PyMuPDF
import streamlit as st
import tempfile
from openai import OpenAI
from datetime import datetime

# Configuração da página Streamlit
st.set_page_config(
    page_title='Extrator de Notas Fiscais de Serviço',
    page_icon='📊',
    layout='wide'
)

# Carrega as variáveis de ambiente
load_dotenv()

# Função para codificar uma imagem no formato Base64
def codificar_imagem(caminho_imagem):
    """Codifica uma imagem em base64."""
    try:
        with open(caminho_imagem, 'rb') as imagem:
            return base64.b64encode(imagem.read()).decode('utf-8')
    except Exception as erro:
        st.error(f'Erro ao codificar imagem {caminho_imagem}: {str(erro)}')
        return None

# Função para extrair informações da NFS-e
def extrair_informacoes_nfse(imagem_base64):
    """Envia a imagem para o modelo GPT e extrai as informações da NFS-e."""
    prompt_texto = """
    Analise essa imagem de uma Nota Fiscal de Serviço Eletrônica (NFS-e) brasileira e extraia as seguintes informações específicas:

    1. CNPJ do prestador de serviços
    2. Nome/Razão Social do prestador de serviços
    3. CNPJ do tomador de serviços
    4. Nome/Razão Social do tomador de serviços
    5. Número da nota fiscal
    6. Data de emissão
    7. Valor total do serviço
    8. Discriminação do serviço prestado (descrição do serviço)
    9. Valores de impostos (IR, PIS, COFINS, CSLL, INSS e ISS)
    10. Valor aproximado dos tributos

    IMPORTANTE:
    - Extraia os números de CNPJ com todos os caracteres, incluindo pontos, barras e hífens (formato: 00.000.000/0000-00)
    - Extraia a data no formato DD/MM/AAAA
    - Extraia o valor total, valores de impostos e valor aproximado dos tributos como números decimais (com ponto como separador decimal)
    - Para a discriminação do serviço, busque seções com títulos como "DISCRIMINAÇÃO DOS SERVIÇOS", "DESCRIÇÃO DO SERVIÇO", "DISCRIMINAÇÃO DO SERVIÇO" ou equivalentes
    - IMPORTANTE: Se houver um código de serviço antes da descrição (como "01.01.01 - Análise e desenvolvimento de sistemas"), inclua-o na discriminação do serviço exatamente como aparece na nota
    - Capture a descrição completa do serviço, incluindo o código quando disponível, no formato "CÓDIGO - DESCRIÇÃO" (exemplo: "01.01.01 - Análise e desenvolvimento de sistemas")
    - Busque valores de impostos em seções como "RETENÇÕES FEDERAIS", "IMPOSTOS RETIDOS", "VALORES DE IMPOSTOS" ou similares
    - Para o valor aproximado dos tributos, busque campos como "VALOR APROXIMADO DOS TRIBUTOS", "VALOR APROXIMADO TRIBUTOS", "IBPT" ou similares (exemplo: "R$ 1.880,00 (17,65%) / IBPT")
    - Extraia apenas o valor numérico do "Valor aproximado dos tributos", ignorando percentuais e textos adicionais
    - Se os valores de impostos (IR, PIS, COFINS, CSLL, INSS, ISS) ou o valor aproximado dos tributos não estiverem presentes ou legíveis na imagem, defina-os como "0.00"
    - Se algum outro campo não estiver presente ou legível na imagem, defina seu valor como null
    - Se houver mais de um valor para o mesmo campo, escolha o mais completo e legível

    Retorne apenas um objeto JSON com o seguinte formato:
    {
        "cnpj_prestador": "00.000.000/0000-00",
        "nome_prestador": "Nome da Empresa Prestadora",
        "cnpj_tomador": "00.000.000/0000-00",
        "nome_tomador": "Nome da Empresa Tomadora",
        "numero_nota": "000000000",
        "data_emissao": "DD/MM/AAAA",
        "valor_total": "0.00",
        "discriminacao_servico": "Código - Descrição do serviço prestado",
        "ir": "0.00",
        "pis": "0.00",
        "cofins": "0.00",
        "csll": "0.00",
        "inss": "0.00",
        "iss": "0.00",
        "valor_aproximado_tributos": "0.00"
    }

    Responda APENAS com o JSON, sem texto adicional.
    """

    try:
        # Criar cliente OpenAI com a chave de API fornecida
        cliente = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        resposta = cliente.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt_texto},
                    {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{imagem_base64}'}}
                ]
            }],
            max_tokens=1000
        )

        # Extrair apenas o JSON da resposta
        texto_resposta = resposta.choices[0].message.content.strip()

        # Remover qualquer formatação de markdown (` ```json ... ``` `)
        texto_resposta = texto_resposta.replace("```json", "").replace("```", "").strip()

        # Tentar encontrar um JSON válido na resposta
        try:
            # Se o texto já for um JSON limpo
            dados = json.loads(texto_resposta)
            return dados
        except json.JSONDecodeError:
            # Se falhar com json.loads, tentamos com ast.literal_eval
            try:
                dados = ast.literal_eval(texto_resposta)
                return dados
            except Exception as erro:
                st.error(f'Erro ao extrair dados da resposta: {str(erro)}')
                return None

    except Exception as erro:
        st.error(f'Erro ao processar imagem: {str(erro)}')
        return None

# Função para converter PDF para imagem
def converter_pdf_para_imagem(caminho_pdf, pasta_imagens):
    """Converte a primeira página de um PDF em imagem."""
    try:
        # Verificar se a pasta de imagens existe, se não, criar
        if not os.path.exists(pasta_imagens):
            os.makedirs(pasta_imagens)

        # Gerar nome do arquivo baseado no nome do PDF original
        nome_base = os.path.splitext(os.path.basename(caminho_pdf))[0]
        caminho_img = os.path.join(pasta_imagens, f'{nome_base}.jpg')

        # Abrir o PDF com PyMuPDF
        doc = fitz.open(caminho_pdf)

        # Verificar se o documento tem páginas
        if doc.page_count == 0:
            return None

        # Carregar a primeira página
        pagina = doc.load_page(0)  # índice 0 = primeira página

        # Definir matriz de transformação para aumentar a resolução (300 DPI)
        matriz = fitz.Matrix(3, 3)

        # Renderizar a página para um objeto pixmap (sem canal alpha para reduzir tamanho)
        pix = pagina.get_pixmap(matrix=matriz, alpha=False)

        # Salvar a imagem como JPEG
        pix.save(caminho_img, 'jpeg')

        # Fechar o documento para liberar recursos
        doc.close()

        return caminho_img
    except Exception as erro:
        return None

def processar_arquivo(arquivo, pasta_temp, pasta_imagens):
    """Processa um único arquivo (PDF ou imagem) e retorna os dados extraídos."""
    try:
        # Salvar o arquivo temporariamente
        caminho_arquivo = os.path.join(pasta_temp, arquivo.name)
        with open(caminho_arquivo, 'wb') as f:
            f.write(arquivo.getbuffer())

        # Verificar se é um PDF ou uma imagem
        if arquivo.name.lower().endswith('.pdf'):
            # Converter PDF para imagem
            caminho_img = converter_pdf_para_imagem(caminho_arquivo, pasta_imagens)
            if not caminho_img:
                return None

            # Codificar imagem em base64
            imagem_base64 = codificar_imagem(caminho_img)
        else: # Arquivo de imagem
            # Codificar imagem em base64 diretamente
            imagem_base64 = codificar_imagem(caminho_arquivo)

        if not imagem_base64:
            return None

        # Extrair informações
        dados = extrair_informacoes_nfse(imagem_base64)
        if dados:
            dados['nome_arquivo'] = arquivo.name
            return dados
        else:
            return None
    except Exception as erro:
        return None

# Função para gerar link de download
def get_download_link(df, nome_arquivo, texto):
    """Gera um link para download do DataFrame como CSV."""
    csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{nome_arquivo}">{texto}</a>'
    return href

# Função para formatar valores no padrão brasileiro
def formatar_valor_br(valor):
    """Converte um valor numérico para formato de moeda brasileiro."""
    if valor is None or valor == '':
        return ''

    # Tenta converter para float, tratando diferentes formatos
    try:
        # Se o valor já vier como string com vírgula decimal
        if isinstance(valor, str) and ',' in valor:
            valor = valor.replace('.', '').replace(',', '.')

        valor_float = float(valor)
        # Formata para o padrão brasileiro: 1.234,56
        return f'{valor_float:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return valor # Retorna o valor original em caso de erro

# Função principal da aplicação Streamlit
def main():
    st.title('Extrator de Notas Fiscais de Serviço (NFS-e)')

    # Criar diretórios temporários para trabalhar
    with tempfile.TemporaryDirectory() as temp_dir:
        # Criar subpastas
        pasta_imagens = os.path.join(temp_dir, 'imagens_processadas')
        if not os.path.exists(pasta_imagens):
            os.makedirs(pasta_imagens)

        # Upload de arquivos
        st.subheader('Upload de Arquivos')
        st.write('Faça upload dos PDFs ou imagens de notas fiscais de serviço.')

        arquivos = st.file_uploader(
            'Arraste e solte arquivos aqui ou clique para selecionar',
            type=['pdf', 'jpg', 'jpeg', 'png'],
            accept_multiple_files=True
        )

        # Inicializar variáveis
        resultados = []
        df_resultados = None

        # Botão para processar os arquivos
        if arquivos and st.button('Processar Arquivos'):
            # Exibir barra de progresso
            progresso = st.progress(0)
            texto_status = st.empty()

            # Processar cada arquivo
            total_arquivos = len(arquivos)
            for i, arquivo in enumerate(arquivos):
                texto_status.text(f'Processando {i+1}/{total_arquivos}: {arquivo.name}')
                progresso.progress((i) / total_arquivos)

                resultado = processar_arquivo(arquivo, temp_dir, pasta_imagens)
                if resultado:
                    resultados.append(resultado)
                    st.success(f'✅ {arquivo.name} processado com sucesso')
                else:
                    st.error(f'❌ Falha ao processar {arquivo.name}')

            # Atualizar progresso final
            progresso.progress(1.0)
            texto_status.text(f'Processamento concluído. {len(resultados)} de {total_arquivos} arquivos processados com sucesso.')

            # Criar DataFrame e exibir resultados se houver
            if resultados:
                df_resultados = pd.DataFrame(resultados)

                # Antes de exibir, formatar valores monetários no padrão brasileiro
                if 'valor_total' in df_resultados.columns:
                    # Cria uma cópia do valor para exibição no DataFrame
                    df_exibicao = df_resultados.copy()
                    df_exibicao['valor_total'] = df_exibicao['valor_total'].apply(formatar_valor_br)
                    # Formatar campos de impostos
                    for campo in ['pis', 'cofins', 'ir', 'csll', 'inss', 'iss', 'valor_aproximado_tributos']:
                        if campo in df_exibicao.columns:
                            df_exibicao[campo] = df_exibicao[campo].apply(formatar_valor_br)

                    st.subheader('Resultados Extraídos')
                    st.dataframe(df_exibicao)
                else:
                    st.subheader('Resultados Extraídos')
                    st.dataframe(df_resultados)

                # Para o CSV, formatar os valores monetários
                # (criamos uma cópia para não afetar o JSON)
                df_csv = df_resultados.copy()
                if 'valor_total' in df_csv.columns:
                    df_csv['valor_total'] = df_csv['valor_total'].apply(formatar_valor_br)
                    # Formatar campos de impostos
                    for campo in ['pis', 'cofins', 'ir', 'csll', 'inss', 'iss', 'valor_aproximado_tributos']:
                        if campo in df_csv.columns:
                            df_csv[campo] = df_csv[campo].apply(formatar_valor_br)

                # Botão para download do CSV
                csv = df_csv.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')
                st.download_button(
                    label='Baixar Resultados (CSV)',
                    data=csv,
                    file_name=f'resultados_nfse_{timestamp}.csv',
                    mime='text/csv'
                )

                # Botão para download do JSON
                json_str = json.dumps(resultados, ensure_ascii=False, indent=4)
                st.download_button(
                    label='Baixar Resultados (JSON)',
                    data=json_str.encode('utf-8'),
                    file_name=f'resultados_nfse_{timestamp}.json',
                    mime='application/json'
                )
            else:
                st.warning('Não foi possível extrair informações dos arquivos.')

        # Exibir instruções
        with st.expander('Instruções de Uso'):
            st.markdown("""
            ### Como usar o Extrator de NFS-e

            1. **Faça upload dos arquivos** de notas fiscais (PDF, JPG, PNG).
            2. Clique no botão **Processar Arquivos**.
            3. Aguarde o processamento - você verá o progresso na barra.
            4. Visualize os resultados na tabela.
            5. **Baixe os resultados** em formato CSV ou JSON.

            ### Informações extraídas

            - CNPJ do prestador
            - Nome do prestador
            - CNPJ do tomador
            - Nome do tomador
            - Número da nota fiscal
            - Data de emissão
            - Valor total
            - Discriminação do serviço prestado

            ### Observações

            - A qualidade da extração depende da qualidade das imagens
            - Diferentes formatos de NFS-e podem ter resultados variados
            - O processamento utiliza a API da OpenAI (modelo GPT-4o-mini)
            """)

if __name__ == '__main__':
    main()
