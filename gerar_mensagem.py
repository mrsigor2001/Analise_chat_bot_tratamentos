from flask import Flask, request, jsonify
from api import gerar_mensagem  # Certifique-se de que esta função existe e está corretamente implementada
import renegociacao
import pandas as pd

app = Flask(__name__)

@app.route('/gerar_mensagem', methods=['POST'])
def gerar_mensagem():
    try:
        dados = request.get_json(force=True, silent=True)
        if not dados:
            return jsonify({"erro": "JSON inválido ou não enviado"}), 400

        cliente_id = dados.get("cliente_id")
        bill_id = dados.get("bill_id")
        numero_unidade = dados.get("numero_unidade")

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
        resumo = renegociacao.calcular_resumo(df)

        # Gera mensagem
        mensagem = renegociacao.gerar_mensagem_resumo_com_emojis(resumo)

        return jsonify({"mensagem": mensagem})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
