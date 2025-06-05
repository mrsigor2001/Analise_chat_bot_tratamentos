from api_services import obter_id_cliente_por_cpf, obter_dados_do_extrato
from service import extrair_unidades, validar_cpf, formatar_cpf
import pandas as pd
import logging

def extrair_unidades(dados):
    unidades = []
    for item in dados.get("data", []):
        bill_receivable_id = item.get("billReceivableId")
        # Informações do cliente para repetir em cada unidade
        cliente = item.get("customer", {})
        nome_cliente = cliente.get("name", "")
        documento_cliente = cliente.get("document", "")
        cliente_id = cliente.get("id")

        for unidade in item.get("units", []):
            unidades.append({
                "billReceivableId": bill_receivable_id,
                "id_unidade": unidade.get("id"),
                "nome_unidade": unidade.get("name"),
                "nome_cliente": nome_cliente,
                "documento_cliente": documento_cliente,
                "cliente_id": cliente_id
            })

    return unidades



def consultar_unidades_por_cpf(cpf_input, subdominios=None, start_due_date="2001-01-01", end_due_date="2100-01-01"):
    if subdominios is None:
        subdominios = ["sej", "macapainvest"]

    if not validar_cpf(cpf_input):
        return {"erro": "CPF inválido."}

    cpf_numeric = ''.join(filter(str.isdigit, cpf_input))
    unidades_encontradas = []

    for subdominio in subdominios:
        logging.info(f"🔎 Subdomínio: {subdominio}")
        id_cliente = obter_id_cliente_por_cpf(subdominio, cpf_numeric)

        if not id_cliente:
            logging.warning(f"⚠️ Cliente não encontrado em {subdominio}. Pulando para o próximo.")
            continue

        logging.info(f"✅ ID do cliente: {id_cliente}")

        try:
            dados = obter_dados_do_extrato(
                subdominio=subdominio,
                start_due_date=start_due_date,
                end_due_date=end_due_date,
                cliente_id=id_cliente
            )

            if dados:
                unidades = extrair_unidades(dados)  # Aqui já inclui billReceivableId
                for unidade in unidades:
                    unidade["cliente_id"] = id_cliente
                    unidade["subdominio"] = subdominio
                unidades_encontradas.extend(unidades)
            else:
                logging.warning("⚠️ Nenhum dado de extrato retornado.")

        except Exception as e:
            logging.error(f"❌ Erro ao processar o CPF {cpf_input}: {e}")

    return {"unidades": unidades_encontradas}




def consultar_unidades_por_clienteid_numberunit(cpf_input, subdominios=["sej", "macapainvest"], start_due_date="2001-01-01", end_due_date="2100-01-01"):
    if not validar_cpf(cpf_input):
        return {"erro": "CPF inválido."}

    cpf = formatar_cpf(cpf_input)
    unidades_encontradas = []

    for subdominio in subdominios:
        print(f"\n🔎 Subdomínio: {subdominio}")
        id_cliente = obter_id_cliente_por_cpf(subdominio, cpf)

        if not id_cliente:
            print(f"⚠️ Cliente não encontrado em {subdominio}. Pulando para o próximo.")
            continue

        print(f"✅ ID do cliente: {id_cliente}")

        try:
            dados = obter_dados_do_extrato(
                subdominio=subdominio,
                start_due_date=start_due_date,
                end_due_date=end_due_date,
                cliente_id=id_cliente
            )

            if dados:
                df = pd.DataFrame(dados.get('results', []))
                return dados
            else:
                print("⚠️ Nenhum dado de extrato retornado.")

        except Exception as e:
            print(f"❌ Erro ao processar o CPF {cpf_input}: {e}")

    return {"unidades": unidades_encontradas}



