import socket
import psutil
import sys
import subprocess
import threading
from api import app
from waitress import serve

PORTS = [5000, 5001, 5002]

def kill_process_on_port(port):
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        for conn in proc.info['connections'] or []:
            if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                print(f"Matando processo PID {proc.pid} na porta {port}")
                proc.kill()
                return True
    return False

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0

def start_server_on_port(port):
    print(f"Iniciando Waitress na porta {port}...")
    serve(app, host='0.0.0.0', port=port)

def main():
    threads = []
    for port in PORTS:
        if is_port_in_use(port):
            print(f"Porta {port} está ocupada. Tentando liberar...")
            if not kill_process_on_port(port):
                print(f"Não foi possível liberar a porta {port}. Abortando.")
                sys.exit(1)
        else:
            print(f"Porta {port} está livre.")

        thread = threading.Thread(target=start_server_on_port, args=(port,), daemon=False)
        thread.start()
        threads.append(thread)

    print("Servidores nas portas 5000, 5001 e 5002 estão ativos.")
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    try:
        import psutil
    except ImportError:
        print("Instalando psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    main()
