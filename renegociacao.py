import requests
import pandas as pd
from Credenciais import obter_credenciais
import pandas as pd
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import numpy as np



def obter_dados_do_extrato(subdominio, cliente_id, bill_receivable_id=None, unit_id=None):
    url = f"https://api.sienge.com.br/{subdominio}/public/api/bulk-data/v1/customer-extract-history"
    start_due_date = "1990-01-01"
    end_due_date = "2100-12-31"

    params = {
        "startDueDate": start_due_date,
        "endDueDate": end_due_date,
        "customerId": cliente_id,
    }

    if bill_receivable_id:
        params["billReceivableId"] = bill_receivable_id
    if unit_id:
        params["unitId"] = unit_id

    headers = {
        "Authorization": obter_credenciais(subdominio)
    }

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                print(f"✅ Dados extraídos com sucesso de {subdominio}.")
                return response.json()
            else:
                raise Exception(f"Erro {response.status_code}: {response.text}")
        except Exception as e:
            print(f"⚠️ Tentativa {attempt} falhou em {subdominio}: {e}")
            if attempt == max_retries:
                print(f"❌ Falha após {max_retries} tentativas para {subdominio}.")
                return None






def extrair_dados_completos(dados_json: dict, subdominio: str):
    if not dados_json or "data" not in dados_json or not dados_json["data"]:
        return pd.DataFrame()

    registros = []

    for item in dados_json["data"]:
        base = {
            "subdominio": subdominio,
            "billReceivableId": item.get("billReceivableId"),
            "company_id": item.get("company", {}).get("id"),
            "company_name": item.get("company", {}).get("name"),
            "costCenter_id": item.get("costCenter", {}).get("id"),
            "costCenter_name": item.get("costCenter", {}).get("name"),
            "customer_id": item.get("customer", {}).get("id"),
            "customer_name": item.get("customer", {}).get("name"),
            "customer_document": item.get("customer", {}).get("document"),
            "emissionDate": item.get("emissionDate"),
            "lastRenegotiationDate": item.get("lastRenegotiationDate"),
            "correctionDate": item.get("correctionDate"),
            "document": item.get("document"),
            "privateArea": item.get("privateArea"),
            "oldestInstallmentDate": item.get("oldestInstallmentDate"),
            "revokedBillReceivableDate": item.get("revokedBillReceivableDate"),
        }

        if item.get("units"):
            base["unit_id"] = item["units"][0].get("id")
            base["unit_name"] = item["units"][0].get("name")
        else:
            base["unit_id"] = None
            base["unit_name"] = None

        for parcela in item.get("installments", []):
            registro = base.copy()
            registro.update({
                "installment_id": parcela.get("id"),
                "annualCorrection": parcela.get("annualCorrection"),
                "sentToScripturalCharge": parcela.get("sentToScripturalCharge"),
                "paymentTerms_id": parcela.get("paymentTerms", {}).get("id"),
                "paymentTerms_descrition": parcela.get("paymentTerms", {}).get("descrition"),
                "baseDate": parcela.get("baseDate"),
                "originalValue": parcela.get("originalValue"),
                "dueDate": parcela.get("dueDate"),
                "indexerId": parcela.get("indexerId"),
                "calculationDate": parcela.get("calculationDate"),
                "currentBalance": parcela.get("currentBalance"),
                "currentBalanceWithAddition": parcela.get("currentBalanceWithAddition"),
                "generatedBillet": parcela.get("generatedBillet"),
                "installmentSituation": parcela.get("installmentSituation"),
                "installmentNumber": parcela.get("installmentNumber"),
            })

            if parcela.get("receipts"):
                receipt = parcela["receipts"][0]
                registro.update({
                    "receipt_days": receipt.get("days"),
                    "receipt_date": receipt.get("date"),
                    "receipt_value": receipt.get("value"),
                    "receipt_extra": receipt.get("extra"),
                    "receipt_discount": receipt.get("discount"),
                    "receipt_netReceipt": receipt.get("netReceipt"),
                    "receipt_type": receipt.get("type"),
                })

            registros.append(registro)

    return pd.DataFrame(registros)

def obter_dados_extrato_por_bill_ids(subdominios, cliente_id, bill_id, unit_id=None):
    dfs = []
    for sub in subdominios:
        dados_json = obter_dados_do_extrato(
            subdominio=sub,
            cliente_id=cliente_id,
            bill_receivable_id=bill_id,
            unit_id=unit_id
        )
        df = extrair_dados_completos(dados_json, sub)
        if not df.empty:
            dfs.append(df)

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        print("Nenhum dado retornado para os subdomínios e bill_id informado.")
        return pd.DataFrame()



def obter_dados_extrato_por_cliente(subdominios, cliente_id, unit_id=None):
    dfs = []

    for sub in subdominios:
        dados_json = obter_dados_do_extrato(sub, cliente_id=cliente_id, unit_id=unit_id)
        df = extrair_dados_completos(dados_json, sub)
        dfs.append(df)

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        print("Nenhum dado retornado para os subdomínios.")
        return pd.DataFrame()
    


def analisar_parcela(row):
    hoje = datetime.today().date()
    due = row["dueDate"].date() if pd.notnull(row["dueDate"]) else None
    receipt = row["receipt_date"].date() if pd.notnull(row["receipt_date"]) else None
    receipt_type = row.get("receipt_type", "")

    if receipt_type == "Distrato":
        return "Distratada"
    elif receipt_type == "Reparcelamento":
        return "Renegociada"
    elif receipt_type == "Recebimento":
        return "Paga"
    elif due:
        if due >= hoje:
            return "Em aberto"
        else:
            return "Atrasada"
    else:
        return "Sem data de vencimento"

def arredondar_decimal(valor, casas=2):
    d = Decimal(str(valor)).quantize(Decimal(f'1.{"0"*casas}'), rounding=ROUND_HALF_UP)
    return d

def calcular_renegociação(df):
    contagem_status = df['analise_de_parcela'].value_counts()

    parcelas_atrasadas = contagem_status.get('Atrasada', 0)
    parcelas_abertas = contagem_status.get('Em aberto', 0)
    parcelas_renegociadas = contagem_status.get('Renegociada', 0)
    parcelas_pagas = contagem_status.get('Paga', 0)
    parcelas_sem_venc = contagem_status.get('Sem data de vencimento', 0)

    saldo_com_juros = df.loc[
        df['analise_de_parcela'].isin(['Atrasada', 'Em aberto']),
        'currentBalanceWithAddition'
    ].fillna(0).sum()

    saldo_sem_juros = df.loc[
        df['analise_de_parcela'].isin(['Atrasada', 'Em aberto']),
        'currentBalance'
    ].fillna(0).sum()

    saldo_com_juros = arredondar_decimal(saldo_com_juros)
    saldo_sem_juros = arredondar_decimal(saldo_sem_juros)

    return {
        "parcelas_atrasadas": int(parcelas_atrasadas),
        "parcelas_abertas": int(parcelas_abertas),
        "parcelas_renegociadas": int(parcelas_renegociadas),
        "parcelas_pagas": int(parcelas_pagas),
        "saldo_devedor_com_juros": float(saldo_com_juros),
        "saldo_devedor_sem_juros": float(saldo_sem_juros)
    }



def calcular_reparcelamento(df):
    
    contagem_status = df['analise_de_parcela'].value_counts()

    parcelas_atrasadas = contagem_status.get('Atrasada', 0)
    parcelas_abertas = contagem_status.get('Em aberto', 0)
    parcelas_renegociadas = contagem_status.get('Renegociada', 0)
    parcelas_pagas = contagem_status.get('Paga', 0)


    saldo_com_juros = df.loc[
        df['analise_de_parcela'].isin(['Atrasada', 'Em aberto']),
        'currentBalanceWithAddition'
    ].fillna(0).sum()

    saldo_sem_juros = df.loc[
        df['analise_de_parcela'].isin(['Atrasada', 'Em aberto']),
        'currentBalance'
    ].fillna(0).sum()

    saldo_com_juros = arredondar_decimal(saldo_com_juros)
    saldo_sem_juros = arredondar_decimal(saldo_sem_juros)

    return {
        "parcelas_atrasadas": int(parcelas_atrasadas),
        "parcelas_abertas": int(parcelas_abertas),
        "parcelas_renegociadas": int(parcelas_renegociadas),
        "parcelas_pagas": int(parcelas_pagas),
        "saldo_devedor_com_juros": float(saldo_com_juros),
        "saldo_devedor_sem_juros": float(saldo_sem_juros)
    }


def gerar_mensagem_resumo_com_emojis(resumo):
    msg = (
        "📊 Resumo da Situação das Parcelas 📊\n\n"
        "Prezado(a) cliente,\n\n"
        "Segue o resumo atualizado da situação das suas parcelas:\n\n"
        f"⚠️ Parcelas Atrasadas: {resumo.get('parcelas_atrasadas', 0)}\n"
        f"🕒 Parcelas A Vencer: {resumo.get('parcelas_abertas', 0)}\n"
        f"• 💰 Saldo Devedor: R$ {resumo.get('saldo_devedor_com_juros', 0):,.2f}\n"
    )
    return msg







