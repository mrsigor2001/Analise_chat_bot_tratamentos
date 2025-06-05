from flask import Flask, request, jsonify
from api import gerar_mensagem  # Certifique-se de que esta função existe e está corretamente implementada
import renegociacao
import pandas as pd
from cpf_utils import validar_cpf
from db_cache import salvar_consulta_no_db, buscar_consulta_no_db,excluir_consulta_no_db
import logging


app = Flask(__name__)

@app.route('/responder', methods=['POST'])
def responder():
    try:
        dados = request.get_json(force=True, silent=True)
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



if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
