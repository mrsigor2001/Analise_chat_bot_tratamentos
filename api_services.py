import requests
import re
from Credenciais import obter_credenciais
from service import validar_cpf


def formatar_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def obter_id_cliente_por_cpf(subdominio: str, cpf: str):
    cpf = re.sub(r'\D', '', cpf)

    if not validar_cpf(cpf):
        print("CPF inválido.")
        return None

    url = f"https://api.sienge.com.br/{subdominio}/public/api/v1/customers"
    headers = {
        "Authorization": obter_credenciais(subdominio),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    params = {"cpf": cpf}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        dados = response.json()
        resultados = dados.get("results", [])
        if resultados:
            cliente_id = resultados[0].get("id")
            cliente_id = int(cliente_id) 
            print(f"CPF {formatar_cpf(cpf)} encontrado. ID: {cliente_id}")

            return cliente_id
        else:
            print(f"CPF {formatar_cpf(cpf)} não encontrado.")
            return None
    else:
        print(f"Erro {response.status_code}: {response.text}")
        return None

# Função para obter os dados do extrato do cliente via API (não assíncrona)
def obter_dados_do_extrato(subdominio, start_due_date, end_due_date, cliente_id, bill_receivable_id=None):
    url = f"https://api.sienge.com.br/{subdominio}/public/api/bulk-data/v1/customer-extract-history"
    
    params = {
        "startDueDate": start_due_date,
        "endDueDate": end_due_date,
        "customerId": cliente_id,  # Passando o cliente_id diretamente para a consulta
    }

    if bill_receivable_id:
        params["billReceivableId"] = bill_receivable_id
    
    headers = {
        "Authorization": obter_credenciais(subdominio)
    }

    max_retries = 3
    attempt = 0

    while attempt < max_retries:
        attempt += 1
        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                print(f"✅ Dados extraídos com sucesso de {subdominio} {start_due_date} a {end_due_date}.")
                return response.json()  # Retorna os dados da resposta

            else:
                raise Exception(f"Erro: {response.status_code}, {response.text()}")

        except Exception as e:
            print(f"⚠️ Tentativa {attempt} falhou para {subdominio} {start_due_date} a {end_due_date}: {e}")
            if attempt == max_retries:
                print(f"❌ Falha após {max_retries} tentativas para {subdominio} {start_due_date} a {end_due_date}.")
                raise

           