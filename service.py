import pandas as pd
from conexao import conectar_banco
from datetime import datetime  # Corrigido aqui
import re

def formatar_cpf(cpf):
    # Remove qualquer caractere não numérico e formata o CPF
    cpf = ''.join(filter(str.isdigit, cpf))
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def buscar_dataframe_por_documento(documento):
    conexao = conectar_banco()
    if conexao:
        try:
            query = "SELECT * FROM extratos_cliente WHERE customer_document = %s"
            df = pd.read_sql(query, conexao, params=(documento,))
            # Converte as colunas para datetime
            df['dueDate'] = pd.to_datetime(df['dueDate'], errors='coerce')
            df['receipt_date'] = pd.to_datetime(df['receipt_date'], errors='coerce')

            # Data de hoje
            # Data de hoje como datetime
            hoje = pd.to_datetime(datetime.today().date())

            # Uma parcela é inadimplente se:
            # - dueDate < hoje
            # - e receipt_date está vazio/nulo (ainda não foi paga)
            df['inadimplente'] = (df['dueDate'] < hoje) & (df['receipt_date'].isna())

            inadimplentes_df = df[df['inadimplente'] == True]


            # Garante que os valores estão no formato numérico
            df['currentBalanceWithAddition'] = pd.to_numeric(df['currentBalanceWithAddition'], errors='coerce')
            df['currentBalance'] = pd.to_numeric(df['currentBalance'], errors='coerce')

            # Calcula os saldos
            Saldo_Devedor_Corrigido = round(inadimplentes_df['currentBalanceWithAddition'].sum(), 2)
            Saldo_Devedor = round(inadimplentes_df['currentBalance'].sum(), 2)
            total_inadimplentes = inadimplentes_df['inadimplente'].sum()
            customer_name = inadimplentes_df['customer_name'].iloc[0]
            
            return Saldo_Devedor_Corrigido, Saldo_Devedor, total_inadimplentes, customer_name
        
        except Exception as e:
            print(f"Erro ao executar a consulta: {e}")
            return pd.DataFrame()
        finally:
            conexao.close()
            print("🔒 Conexão encerrada.")

def extrair_unidades(dados):
    unidades_extraidas = []

    for item in dados.get("data", []):
        cliente = item.get("customer", {})
        nome_cliente = cliente.get("name", "N/A")
        documento_cliente = cliente.get("document", "N/A")

        for unidade in item.get("units", []):
            unidades_extraidas.append({
                "nome_unidade": unidade.get("name", "N/A"),
                "id_unidade": unidade.get("id", "N/A"),
                "nome_cliente": nome_cliente,
                "documento_cliente": documento_cliente,
            })

    return unidades_extraidas
def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True

