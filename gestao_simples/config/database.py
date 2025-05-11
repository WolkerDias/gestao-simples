# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import streamlit as st
from utils.logger import logger
import os
import time
from datetime import datetime
import subprocess
import platform
import winreg
from pathlib import Path
from config.settings import DB_CONFIG, BACKUP_DIR


# Monta a URL de conexão
DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
#DATABASE_URL = "mysql+pymysql://root:@localhost:3306/db"

# Create engine with logging
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Enable SQL logging
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600  # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_mysql_path():
    """
    Tenta localizar o caminho do MySQL no Windows através do registro
    ou dos caminhos comuns de instalação
    """
    if platform.system() != 'Windows':
        return 'mysqldump'  # No Linux/Mac, assume que está no PATH
        
    # Lista de possíveis caminhos do MySQL
    possible_paths = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
        r"C:\xampp\mysql\bin\mysqldump.exe",
        r"C:\wamp64\bin\mysql\mysql8.0.31\bin\mysqldump.exe",
        r"C:\wamp64\bin\mysql\mysql5.7.36\bin\mysqldump.exe",
    ]
    
    try:
        # Tenta encontrar através do registro do Windows
        reg_path = r"SOFTWARE\MySQL AB\MySQL Server 8.0"
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        mysql_path = winreg.QueryValueEx(reg_key, "Location")[0]
        winreg.CloseKey(reg_key)
        mysqldump_path = os.path.join(mysql_path, "bin", "mysqldump.exe")
        if os.path.exists(mysqldump_path):
            return mysqldump_path
    except WindowsError:
        pass
    
    # Tenta os caminhos comuns
    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    raise FileNotFoundError("mysqldump não encontrado. Por favor, verifique se o MySQL está instalado corretamente.")

def backup_database():
    """Create a backup of the database"""
    try:
        # Create backups directory if it doesn't exist
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_DIR, f"{DB_CONFIG['database']}_backup_{timestamp}.sql")
        
        # Get mysqldump path
        mysqldump_path = get_mysql_path()
        logger.info(f"Usando mysqldump de: {mysqldump_path}")

        # Preparar comando
        command = [
            mysqldump_path,
            '-u', DB_CONFIG['user'],  # usuário
            '--databases', DB_CONFIG['database'],
            '--result-file', backup_file,
            '--skip-comments',
            '--skip-extended-insert'
        ]
        
        # Se tiver senha, adicione aqui
        # command.extend(['-p', 'sua_senha'])
        
        # Inicializa a barra de progresso
        progress_text = "Backup em andamento. Por favor, aguarde..."
        my_bar = st.progress(0, text=progress_text)
        
        # Variável para armazenar o valor do progresso
        progress_value = 0
        
        # Execute command with Popen
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitorar o processo em tempo real
        while process.poll() is None:  # Enquanto o processo estiver em execução
            time.sleep(0.5)  # Verifica o status a cada 0.5 segundos
            # Atualiza a barra de progresso (simulação de progresso)
            if progress_value < 90:  # Limita o progresso a 90% durante a execução
                progress_value += 5
                my_bar.progress(progress_value, text=progress_text)
        
        # Verifica se o processo foi concluído com sucesso
        if process.returncode == 0:
            my_bar.progress(100, text="Backup concluído com sucesso!")
            time.sleep(1)  # Aguarda 1 segundo para exibir a mensagem de sucesso
            my_bar.empty()  # Remove a barra de progresso
            
            if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                logger.info(f"Database backup created successfully: {backup_file}")
                st.toast(f"Backup criado com sucesso!", icon="✅")
                return backup_file
            else:
                raise Exception("Backup file was not created or is empty")
        else:
            raise Exception(f"Erro ao executar mysqldump: {process.stderr.read()}")
            
    except FileNotFoundError as e:
        error_msg = str(e)
        logger.error(error_msg)
        st.error("""
        mysqldump não encontrado. Por favor, verifique:
        1. Se o MySQL está instalado no sistema
        2. Se o diretório bin do MySQL está no PATH do sistema
        3. Ou instale o MySQL Workbench/Server se ainda não estiver instalado
        """)
        raise
        
    except Exception as e:
        error_msg = f"Erro ao criar backup do banco: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        raise


def restore_database(backup_file):
    """Restore database from a backup file"""
    my_bar = None
    try:
        # Get mysql path from the same directory as mysqldump
        mysql_path = str(Path(get_mysql_path()).parent / "mysql.exe")
        if not os.path.exists(mysql_path):
            mysql_path = "mysql"  # Fallback to PATH
            
        logger.info(f"Usando mysql de: {mysql_path}")
        
        # Inicializa a barra de progresso
        progress_text = "Restauração em andamento. Por favor, aguarde..."
        my_bar = st.progress(0, text=progress_text)
        progress_value = 0
        
        # Preparar comando
        command = [
            mysql_path,
            '-u', DB_CONFIG['user'],  # usuário
            DB_CONFIG['database']     # nome do banco
        ]
        
        # Execute command with Popen
        with open(backup_file, 'r') as f:
            process = subprocess.Popen(
                command,
                stdin=f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitorar o processo em tempo real
            while process.poll() is None:
                time.sleep(0.5)
                # Atualiza progresso simulado
                if progress_value < 90:
                    progress_value += 2  # Aumenta mais lentamente que o backup
                    my_bar.progress(progress_value, text=progress_text)
                    
            # Verifica conclusão
            if process.returncode == 0:
                my_bar.progress(100, text="Restauração concluída com sucesso!")
                time.sleep(1)
                my_bar.empty()
                logger.info(f"Database restored successfully from: {backup_file}")
                st.toast("Restauração concluída com sucesso!", icon="✅")
            else:
                error_msg = f"Erro na restauração: {process.stderr.read()}"
                my_bar.progress(100, text="Erro na restauração!")
                time.sleep(2)
                raise Exception(error_msg)
            
    except FileNotFoundError as e:
        error_msg = "MySQL client não encontrado. Por favor, verifique a instalação do MySQL."
        if my_bar: my_bar.empty()
        logger.error(error_msg)
        st.error(error_msg)
        raise
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Erro ao executar restauração: {e.stderr}"
        if my_bar: my_bar.empty()
        logger.error(error_msg)
        st.error(error_msg)
        raise
        
    except Exception as e:
        error_msg = f"Erro ao restaurar backup: {str(e)}"
        if my_bar: my_bar.empty()
        logger.error(error_msg)
        st.error(error_msg)
        raise