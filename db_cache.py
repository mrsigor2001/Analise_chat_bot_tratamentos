from datetime import datetime
import json
import logging
from conexao import conectar_banco
from cpf_utils import validar_cpf  # Importa sua função

def executar_query(sql, params=None, fetch_one=False, commit=False):
    db = conectar_banco()
    if not db:
        return None
    cursor = db.cursor()
    try:
        cursor.execute(sql, params)
        if commit:
            db.commit()
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()
    except Exception as e:
        print(f"[ERRO QUERY] {e}")
        return None
    finally:
        cursor.close()
        db.close()

def salvar_consulta_no_db(cpf, cliente_id, nome_cliente, unidades):
    cpf = validar_cpf(cpf)
    if not cpf:
        print(f"[DB] CPF inválido ao tentar salvar: {cpf}")
        return False

    sql = """
        INSERT INTO consultas (cpf, cliente_id, nome_cliente, data_consulta, unidades)
        VALUES (%s, %s, %s, %s, %s)
    """
    unidades_json = json.dumps(unidades)
    data_consulta = datetime.now().isoformat()

    print(f"[DB] Salvando consulta: CPF={cpf}, ID={cliente_id}, Nome={nome_cliente}")
    sucesso = executar_query(sql, (cpf, cliente_id, nome_cliente, data_consulta, unidades_json), commit=True)

    if sucesso:
        print(f"[DB] Consulta salva com sucesso para CPF {cpf}")
    else:
        print(f"[DB] Falha ao salvar consulta para CPF {cpf}")

    return sucesso is not None

def buscar_consulta_no_db(cpf):
    cpf = validar_cpf(cpf)
    if not cpf:
        print(f"[DB] CPF inválido ao buscar: {cpf}")
        return None

    print(f"[DB] Buscando consulta para CPF: {cpf}")
    sql = '''
        SELECT cliente_id, nome_cliente, data_consulta, unidades
        FROM consultas
        WHERE cpf = %s
        ORDER BY data_consulta DESC
        LIMIT 1
    '''
    row = executar_query(sql, (cpf,), fetch_one=True)
    if not row:
        print(f"[DB] Nenhuma consulta encontrada para CPF: {cpf}")
        return None

    cliente_id, nome_cliente, data_consulta, unidades_json = row
    unidades = json.loads(unidades_json)

    return {
        "cliente_id": cliente_id,
        "nome_cliente": nome_cliente,
        "data": data_consulta if isinstance(data_consulta, str) else data_consulta.isoformat(),
        "unidades": unidades
    }

def excluir_consulta_no_db(cpf):
    cpf = validar_cpf(cpf)
    if not cpf:
        logging.error(f"[DB] CPF inválido ao tentar excluir: {cpf}")
        return False

    db = conectar_banco()
    if not db:
        logging.error("Falha na conexão com o banco. Exclusão abortada.")
        return False

    try:
        cursor = db.cursor()
        sql_delete = "DELETE FROM consultas WHERE cpf = %s"
        cursor.execute(sql_delete, (cpf,))
        db.commit()
        logging.info(f"[DB] Consulta excluída com sucesso para CPF: {cpf}")
        return True

    except Exception as e:
        logging.error(f"[DB] Erro ao excluir dados do CPF {cpf}: {e}")
        return False

    finally:
        cursor.close()
        db.close()
