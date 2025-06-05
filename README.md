🧾 API de Consulta e Renegociação de Dívidas
Esta API Flask foi desenvolvida para integrar os sistemas Sienge (ERP de gestão de obras) e Octadesk (plataforma de atendimento e chat), automatizando o processo de consulta de unidades por CPF, geração de mensagens de negociação, e simulação de reparcelamentos.

🚀 Funcionalidades
🔐 Autenticação via token Bearer

🔎 Consulta de CPF e exibição das unidades vinculadas

💬 Integração com Octadesk para envio de mensagens automáticas

📄 Geração de mensagens de negociação com análise financeira

🔁 Simulação de reparcelamento com 3 propostas distintas

🗂️ Cache em banco de dados para controle de consultas e performance

📦 Tecnologias utilizadas
Flask + Waitress (servidor WSGI)

Pandas (análise de parcelas e extratos)

Sienge API (consulta de dados financeiros e unidades)

Octadesk API (respostas ao cliente)

PostgreSQL (cache de consultas)

📁 Estrutura de Arquivos
bash
Copiar
Editar
📦 projeto/
├── api.py                # Módulo principal com os endpoints da API
├── cpf_utils.py          # Validação de CPF
├── db_cache.py           # Cache em banco de dados
├── consulta_unidades.py  # Integração com o Sienge
├── renegociacao.py       # Análise de extratos e renegociação
├── serv_reparcelamento.py# Cálculo de reparcelamentos
├── mensagens_rep.py      # Geração de mensagens com emojis
├── conexao.py            # ⚠️ Configuração do banco (você deve criar)
├── comunicacao.py        # ⚠️ Configuração do Sienge e Octadesk (você deve criar)
└── requirements.txt      # Dependências do projeto
🔧 Pré-requisitos
Python 3.9+

Instalar dependências:

bash
Copiar
Editar
pip install -r requirements.txt
🔐 Autenticação
A API utiliza um token fixo. Configure com uma variável de ambiente ou diretamente em api.py:

bash
Copiar
Editar
export TOKEN_SECRETO="seu_token_aqui"
⚙️ Configuração necessária
conexao.py
Crie este arquivo com os dados de conexão ao seu banco de dados:

python
Copiar
Editar
# conexao.py
import psycopg2

def get_conexao():
    return psycopg2.connect(
        host="host",
        database="nome_banco",
        user="usuario",
        password="senha"
    )
comunicacao.py
Configure aqui os dados de integração com o Sienge e o Octadesk:

python
Copiar
Editar
# comunicacao.py

# Sienge
SIENGE_URL = "https://api.sienge.com.br/..."
SIENGE_HEADERS = {
    "Authorization": "Bearer SEU_TOKEN_SIENGE",
    "Content-Type": "application/json"
}

# Octadesk
OCTADESK_URL = "https://api.octadesk.com/..."
OCTADESK_HEADERS = {
    "Authorization": "Bearer SEU_TOKEN_OCTADESK",
    "Content-Type": "application/json"
}
⚠️ Atenção: nunca comite conexao.py ou comunicacao.py. Adicione-os ao .gitignore.

▶️ Executando a API
bash
Copiar
Editar
python api.py 5000
📬 Endpoints disponíveis
Método	Endpoint	Descrição
POST	/consultar	Consulta CPF e retorna as unidades vinculadas
POST	/responder	Recebe a escolha da unidade por parte do usuário
POST	/gerar_mensagem	Gera mensagem de resumo financeiro para o cliente
POST	/reparcelamento	Simula renegociação e envia 3 propostas personalizadas

📌 Boas práticas
Use .env ou variáveis de ambiente para dados sensíveis

Arquivos como conexao.py, comunicacao.py e .env devem estar listados no .gitignore

Implemente controle de rate limit se publicar externamente

🧠 Contato
Para dúvidas, contribuições ou integração com outros canais do Octadesk, entre em contato com a equipe responsável.

