# Extrator de Notas Fiscais de Serviço (NFS-e)

Uma aplicação web desenvolvida com Streamlit para extrair automaticamente informações de Notas Fiscais de Serviço Eletrônicas (NFS-e) a partir de arquivos PDF ou imagens, usando Inteligência Artificial.

## 🔍 Visão Geral

O **Extrator de NFS-e** é uma ferramenta que utiliza Computer Vision e processamento de linguagem natural para automatizar a extração de dados de Notas Fiscais de Serviço Eletrônicas (NFS-e). A aplicação processa arquivos PDF ou imagens de notas fiscais e extrai dados como CNPJ, nome do prestador/tomador, número da nota, valor total e discriminação do serviço.

Os dados extraídos são apresentados em uma tabela interativa e podem ser exportados em formatos CSV (com formatação brasileira para valores monetários) e JSON.

## ✨ Funcionalidades

- **Upload Múltiplo**: Processamento em lote de PDFs e imagens (jpg, jpeg, png)
- **Extração Inteligente**: Utiliza IA para extrair dados estruturados de documentos não padronizados
- **Conversão de PDF**: Converte automaticamente PDFs em imagens para processamento
- **Visualização de Dados**: Exibe os dados extraídos em tabela interativa
- **Exportação**: Baixe os resultados em CSV (com formatação brasileira) ou JSON
- **Interface Amigável**: Desenvolvida com Streamlit para fácil utilização

## 🛠️ Tecnologias Utilizadas

- **Python**: Linguagem base do projeto
- **Streamlit**: Framework para aplicações web em Python
- **OpenAI API**: API para acesso ao modelo GPT-4o
- **PyMuPDF (fitz)**: Conversão de PDFs para imagens
- **Pandas**: Manipulação e processamento de dados
- **dotenv**: Carregamento de variáveis de ambiente

## 🚀 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/extrator-nfse.git
   cd extrator-nfse
   ```

2. Crie um ambiente virtual e ative-o:
   ```bash
   python -m venv venv

   # No Windows
   venv\Scripts\activate

   # No Linux/Mac
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Copie o arquivo .env.exemplo para .env e adicione sua chave da API da OpenAI:
   ```bash
   # Copie o arquivo de exemplo
   cp .env.exemplo .env

   # Edite o arquivo .env e substitua com sua chave
   OPENAI_API_KEY=sua-chave-api-aqui
   ```

## 📖 Como Usar

1. Execute a aplicação:
   ```bash
   streamlit run app.py
   ```

2. Acesse a aplicação no navegador (geralmente em http://localhost:8501)

3. Faça upload dos arquivos de notas fiscais (PDF, JPG, PNG)

4. Clique no botão "Processar Arquivos"

5. Visualize os resultados na tabela e baixe em CSV ou JSON

## 📁 Estrutura do Projeto

```
extrator-nfse/
├── app.py              # Aplicação principal
├── .env                # Variáveis de ambiente (não versionado)
├── requirements.txt    # Dependências do projeto
├── README.md           # Este arquivo
└── .gitignore          # Arquivos ignorados pelo git
```

## ⚙️ Configuração

### Requisitos do Sistema
- Python 3.7 ou superior
- Acesso à internet (para uso da API da OpenAI)
- Chave de API da OpenAI válida

### Arquivo requirements.txt
```
streamlit>=1.20.0
pandas>=1.3.0
python-dotenv>=0.19.0
openai>=1.0.0
PyMuPDF>=1.18.0
```

## ⚠️ Limitações

- A precisão da extração depende da qualidade das imagens/documentos
- Diferentes formatos de NFS-e podem resultar em variações na qualidade da extração
- O processamento consome tokens da API da OpenAI, o que pode gerar custos
- A API tem um limite de tamanho para as imagens processadas

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das mudanças (`git commit -m 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request
