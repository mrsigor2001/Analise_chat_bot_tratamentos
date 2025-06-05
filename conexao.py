import pymysql

def conectar_banco():
    try:        
        # Configuração da conexão com o banco de dados
        db = pymysql.connect(
            host="",         # Endereço do servidor
            user="",              # Nome de usuário do banco de dados
            password="",      # Senha do banco de dados
            database=""    # Nome do banco de dados
        )
        print("Conexão estabelecida com sucesso!")
        return db
    except pymysql.MySQLError as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        return None
