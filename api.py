from flask import Flask, request, jsonify, g
import logging
import uuid
import pandas as pd
from datetime import datetime
from cpf_utils import validar_cpf
from db_cache import salvar_consulta_no_db, buscar_consulta_no_db,excluir_consulta_no_db
from consulta_unidades import consultar_unidades_por_cpf
import renegociacao
from serv_reparcelamento import calcular_reparcelamento
from mensagens_rep import gerar_mensagens
import mensagens_rep
from threading import Thread
from waitress import serve
import sys
import renegociacao
import threading
import time
import os
import sys
from functools import wraps
from flask import abort

TOKEN_SECRETO = "blokocapital_2021_01@#"  # ideal carregar de env var

def verifica_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {TOKEN_SECRETO}":
            logging.warning(f"[{g.get('request_id', 'no-id')}] Acesso negado: token inválido ou ausente.")
            return jsonify({"erro": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated

app = Flask(__name__)

# Ativa logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

@app.before_request
@verifica_token
def log_request_info():
    try:
        logging.info(f"[REQUEST] {request.method} {request.path}")
        if request.method in ['POST', 'PUT', 'PATCH']:
            payload = request.get_data(as_text=True)
            logging.info(f"[PAYLOAD] {payload}")
    except Exception as e:
        logging.warning(f"[LOG ERROR] Falha ao registrar requisição: {e}")

# Função simulada para excluir dados no banco
def excluir_consulta_no_db(cpf):
    # Simula exclusão, retorna True se sucesso
    logging.info(f"Dados para CPF {cpf} excluídos do banco.")
    return True



@app.before_request
@verifica_token
def before_request_with_id():
    g.request_id = str(uuid.uuid4())
    logging.info(f"[REQUEST ID: {g.request_id}] {request.method} {request.path}")



@app.route('/consultar', methods=['POST'])
@verifica_token
def consultar():
    try:
        dados = request.get_json(force=True, silent=True) or {}
        cpf_raw = dados.get("cpf")

        if not cpf_raw:
            logging.warning(f"[{g.request_id}] CPF não fornecido ou JSON inválido.")
            return jsonify({"erro": "CPF não fornecido ou JSON inválido"}), 400

        cpf = validar_cpf(cpf_raw)
        if not cpf:
            logging.warning(f"[{g.request_id}] CPF inválido: {cpf_raw}")
            return jsonify({"erro": "CPF inválido"}), 400

        # Verifica dados no banco
        dados_db = buscar_consulta_no_db(cpf)
        logging.info(f"[{g.request_id}] [DB HIT] CPF {cpf} encontrado.")
        sucesso = excluir_consulta_no_db(cpf)
        if sucesso:
            logging.info(f"[{g.request_id}] Dados excluídos com sucesso.")

            # Consulta externa
            resultado = consultar_unidades_por_cpf(cpf)
            logging.info(f"[{g.request_id}] Resultado da consulta externa para CPF {cpf}: {resultado}")

            if not resultado or "erro" in resultado:
                erro_msg = resultado.get("erro", "Erro ao consultar unidades.") if resultado else "Erro ao consultar unidades. Tente novamente mais tarde."
                status_code = 400 if resultado else 502
                logging.warning(f"[{g.request_id}] Erro na consulta externa: {erro_msg}")
                return jsonify({"erro": erro_msg}), status_code

            unidades = resultado.get("unidades", [])
            if not unidades:
                logging.info(f"[{g.request_id}] Nenhuma unidade encontrada para CPF {cpf}")
                return jsonify({"mensagem": "Cliente não encontrado em nossa base de dados."}), 404

            nome_cliente = unidades[0].get("nome_cliente", "Cliente")
            cliente_id = unidades[0].get("cliente_id", "desconhecido")
            data_consulta = datetime.now().isoformat()


            dados_db = {
                "unidades": unidades,
                "cliente_id": cliente_id,
                "nome_cliente": nome_cliente,
                "data": data_consulta,
            }

            if salvar_consulta_no_db(cpf, cliente_id, nome_cliente, unidades):
                logging.info(f"[{g.request_id}] [DB SET] CPF {cpf}")
            else:
                logging.warning(f"[{g.request_id}] [DB SET] Falha ao salvar dados do CPF {cpf}")

        # Geração da mensagem com os dados corretos
        unidades_lista = []
        for i, unidade in enumerate(dados_db["unidades"], start=1):
            nome = unidade.get("nome_unidade", "Unidade sem nome")
            bill_id = unidade.get("billReceivableId")

            if bill_id is None:
                logging.warning(f"[{g.request_id}] Unidade sem billReceivableId: {unidade}")
                bill_id = "ID não disponível"

            unidades_lista.append(f"{i}. {nome} ")

        mensagem = (
            f"Olá {dados_db['nome_cliente']}, conseguimos localizar suas unidades. "
            f"Digite a unidade que deseja escolher:\n" + "\n".join(unidades_lista)
        )

        return jsonify({
            "mensagem": mensagem,
            "cliente_id": dados_db["cliente_id"]
        })

    except Exception:
        logging.exception(f"[{g.request_id}] Erro inesperado no endpoint /consultar")
        return jsonify({"erro": "Erro interno ao processar a consulta"}), 500


@app.route('/responder', methods=['POST'])
@verifica_token
def responder():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "JSON inválido ou não enviado"}), 400
        

        print(dados)
        cpf_raw = dados.get("cpf")
        opcao = dados.get("opcao")

        if not cpf_raw or opcao is None:
            return jsonify({"erro": "CPF e opção são obrigatórios."}), 400

        cpf = validar_cpf(cpf_raw)
        if not cpf:
            return jsonify({"erro": "CPF inválido"}), 400

        dados_db = buscar_consulta_no_db(cpf)
        if not dados_db:
            return jsonify({"erro": "Nenhuma consulta encontrada para este CPF."}), 404

        try:
            opcao_int = int(opcao)
            if opcao_int < 1 or opcao_int > len(dados_db["unidades"]):
                raise ValueError("Opção fora do intervalo válido.")
        except ValueError as e:
            return jsonify({"erro": str(e) or "Opção inválida. Deve ser um número."}), 400

        unidade_escolhida = dados_db["unidades"][opcao_int - 1]

        return jsonify({
            "mensagem": f"Você selecionou a unidade: {unidade_escolhida['nome_unidade']}",
            "cliente_id": dados_db["cliente_id"],
            "unidade": unidade_escolhida
        })

    except Exception as e:
        logging.exception("Erro inesperado no endpoint /responder")
        return jsonify({"erro": "Erro interno ao processar a resposta"}), 500


@app.route('/gerar_mensagem', methods=['POST'])
@verifica_token
def gerar_mensagem():
    try:
        dados = request.get_json(force=True, silent=True)
        if not dados:
            return jsonify({"erro": "JSON inválido ou não enviado"}), 400

        cliente_id = dados.get("cliente_id")
        bill_id = dados.get("bill_id")
        numero_unidade = dados.get("unidade")

        if not cliente_id:
            return jsonify({"erro": "cliente_id é obrigatório"}), 400

        if not bill_id:
            return jsonify({"erro": "bill_id é obrigatório"}), 400

        subdominios = ["sej", "macapainvest"]

        df = renegociacao.obter_dados_extrato_por_bill_ids(
            subdominios=subdominios,
            cliente_id=cliente_id,
            bill_id=bill_id,
            unit_id=numero_unidade
        )

        if df.empty:
            return jsonify({"mensagem": "Nenhum dado encontrado para o cliente e unidade informados."})

        # Conversão de datas
        for col in ["dueDate", "receipt_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Análise por parcela
        df["analise_de_parcela"] = df.apply(renegociacao.analisar_parcela, axis=1)

        # Resumo
        resumo = renegociacao.calcular_renegociação(df)

        # Gera mensagem
        mensagem = renegociacao.gerar_mensagem_resumo_com_emojis(resumo)

        return jsonify({"mensagem": mensagem})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/reparcelamento', methods=['POST'])
@verifica_token
def reparcelamento():
    try:
        dados = request.get_json(force=True, silent=True)
        if not dados:
            return jsonify({"erro": "JSON inválido ou não enviado"}), 400
        
        cliente_id = dados.get("cliente_id")
        bill_id = dados.get("bill_id")
        numero_unidade = dados.get("unidade")
        valor_cliente = dados.get("valor_cliente_rene")


        if not bill_id:
            return jsonify({"erro": "bill_id é obrigatório"}), 400

        if not valor_cliente:
            return jsonify({"erro": "valor_cliente é obrigatório"}), 400

        # Converte valor_cliente para float, mesmo com vírgula
        if isinstance(valor_cliente, str):
            valor_cliente = valor_cliente.replace('.', '').replace(',', '.')
        try:
            valor_cliente = float(valor_cliente)
        except ValueError:
            return jsonify({"erro": "valor_cliente inválido"}), 400

        subdominios = ["sej", "macapainvest"]

        df = renegociacao.obter_dados_extrato_por_bill_ids(
            subdominios=subdominios,
            cliente_id=cliente_id,
            bill_id=bill_id,
            unit_id=numero_unidade
        )

        if df.empty:
            return jsonify({"mensagem": "Nenhum dado encontrado para o cliente e unidade informados."})
        
        # Conversão de datas
        for col in ["dueDate", "receipt_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Análise por parcela
        df["analise_de_parcela"] = df.apply(renegociacao.analisar_parcela, axis=1)

        
        resumo = calcular_reparcelamento(df, valor_cliente)

        msg_prop_1, msg_prop_2, msg_prop_3, mensagem_indicada = gerar_mensagens(resumo)
  
        return jsonify({
            "mensagens_proposta_1": msg_prop_1,
            "mensagens_proposta_2": msg_prop_2,
            "mensagens_proposta_3": msg_prop_3,
            "mensagem_indicada": mensagem_indicada,
            "resumo": resumo
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def run_on_port(port):
    serve(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            run_on_port(port)
        except ValueError:
            print("Porta inválida. Use: python api.py <porta>")
    else:
        print("Informe a porta. Exemplo: python api.py 5000")
