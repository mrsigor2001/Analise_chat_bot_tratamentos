import renegociacao
import pandas as pd


def obter_valor_referencia(df):
    hoje = pd.Timestamp.today().normalize()

    # Garantir que a coluna dueDate é datetime
    if 'dueDate' not in df.columns:
        return None

    df = df.copy()
    df['dueDate'] = pd.to_datetime(df['dueDate'], errors='coerce')

    # Filtra parcelas "Em aberto"
    df_abertas = df[df['analise_de_parcela'] == 'Em aberto'].copy()

    if df_abertas.empty:
        return None

    # Busca a próxima parcela a vencer (futura ou hoje)
    df_futuras = df_abertas[df_abertas['dueDate'] >= hoje]
    if not df_futuras.empty:
        parcela_proxima = df_futuras.sort_values('dueDate').iloc[0]
        return float(parcela_proxima['currentBalanceWithAddition'])

    # Se não houver parcelas futuras, pega a última vencida
    df_vencidas = df_abertas[df_abertas['dueDate'] < hoje]
    if not df_vencidas.empty:
        parcela_ultima = df_vencidas.sort_values('dueDate', ascending=False).iloc[0]
        return float(parcela_ultima['currentBalanceWithAddition'])

    return None

def calcular_reparcelamento(df, valor_cliente):

    contagem_status = df['analise_de_parcela'].value_counts()
    parcelas_atrasadas = int(contagem_status.get('Atrasada', 0))
    parcelas_abertas = int(contagem_status.get('Em aberto', 0))
    parcelas_pagas = int(contagem_status.get('Paga', 0))

    saldo_com_juros = float(df.loc[
        df['analise_de_parcela'].isin(['Atrasada', 'Em aberto']),
        'currentBalanceWithAddition'
    ].fillna(0).sum())

    saldo_sem_juros = float(df.loc[
        df['analise_de_parcela'].isin(['Atrasada', 'Em aberto']),
        'currentBalance'
    ].fillna(0).sum())

    saldo_com_juros = round(saldo_com_juros, 2)
    saldo_sem_juros = round(saldo_sem_juros, 2)

    # Definir número de parcelas da renegociação
    parcelas_renegociacao = parcelas_abertas + parcelas_atrasadas + 12

    # Cálculo das propostas
    def gerar_proposta(valor, desconto_pct):
        valor_com_desconto = round(valor * (1 - desconto_pct / 100), 2)
        valor_parcela = round(valor_com_desconto / parcelas_renegociacao, 2)
        return {
            "desconto_percentual": int(desconto_pct),
            "valor_total": float(valor_com_desconto),
            "quantidade_parcelas": int(parcelas_renegociacao),
            "valor_parcela": float(valor_parcela)
        }

    propostas = {
        "proposta_1": gerar_proposta(saldo_sem_juros, 0),
        "proposta_2": gerar_proposta(saldo_sem_juros, 5),
        "proposta_3": gerar_proposta(saldo_sem_juros, 10)
    }

    # ➕ NOVO: valor da próxima parcela a vencer ou última vencida
    valor_referencia = obter_valor_referencia(df)

    # ➕ NOVO: Identificar proposta mais próxima abaixo do valor_cliente
    proposta_indicada = None
    if valor_cliente is not None:
        valores_parcela = {
            chave: proposta["valor_parcela"] for chave, proposta in propostas.items()
        }

        propostas_viaveis = {
            chave: valor for chave, valor in valores_parcela.items()
            if valor <= valor_cliente
        }

        if propostas_viaveis:
            chave_indicada = max(propostas_viaveis, key=propostas_viaveis.get)
            proposta_indicada = propostas[chave_indicada]

    return {
        "parcelas_atrasadas": parcelas_atrasadas,
        "parcelas_abertas": parcelas_abertas,
        "parcelas_pagas": parcelas_pagas,
        "saldo_devedor_com_juros": saldo_com_juros,
        "saldo_devedor_sem_juros": saldo_sem_juros,
        "parcelas_renegociacao": parcelas_renegociacao,
        "valor_cliente": float(valor_cliente) if valor_cliente is not None else None,
        "valor_referencia": float(valor_referencia) if valor_referencia is not None else None,
        "propostas": propostas,
        "proposta_indicada": proposta_indicada  # ⬅️ Nova chave no retorno
    }