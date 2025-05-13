# app_launcher.py
import os
import sys
import streamlit.web.cli as stcli, webbrowser
import requests
import threading

def is_server_running(port=8501):
    """Verifica se o servidor Streamlit já está respondendo"""
    try:
        response = requests.get(f"http://localhost:{port}/healthz", timeout=2)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False

def resolve_path(path):
    """Resolve o caminho absoluto para um arquivo no ambiente congelado ou normal."""
    if getattr(sys, 'frozen', False):
        # Usa o diretório do executável
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, path)

if __name__ == '__main__':
    # Define o caminho para a pasta gestao_simples
    gestao_simples_path = resolve_path('gestao_simples')
    
    # Altera o diretório de trabalho para a pasta gestao_simples
    os.chdir(gestao_simples_path)
    
    # Agora app.py está na raiz (relativo à gestao_simples)

    # Se o servidor não estiver rodando, inicia
    if not is_server_running():
        print("Iniciando o servidor Streamlit...")
        sys.argv = [
            'streamlit', 'run', 'app.py',  # Caminho relativo à nova raiz
            '--global.developmentMode', 'false',
            '--server.port', '8501',  # Porta fixa
            '--server.headless', 'false',
        ]
        
        sys.exit(stcli.main())

        # Inicia o Streamlit em uma thread separada
        def run_streamlit():
            stcli.main()

        thread = threading.Thread(target=run_streamlit, daemon=True)
        thread.start()

        # Aguarda até 10 segundos para o servidor iniciar
        for _ in range(10):
            if is_server_running():
                break
            time.sleep(1)
        else:
            print("Timeout: Servidor não iniciou corretamente")
            sys.exit(1)

        webbrowser.open("http://localhost:8501")

        thread.join()  # Mantém o programa rodando
    else:
        print("O servidor Streamlit já está rodando.")
        # Aqui você pode abrir o navegador se necessário
        webbrowser.open("http://localhost:8501")