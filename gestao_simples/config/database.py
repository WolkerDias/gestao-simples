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

# Adicionar no arquivo que cria a sessão de banco de dados
import numpy as np
from psycopg2.extensions import register_adapter, AsIs

def adapt_numpy_int64(numpy_int64):
    return AsIs(numpy_int64)
    
register_adapter(np.int64, adapt_numpy_int64)


def get_database_url():
    """Build the database connection URL based on configuration"""
    db_type = DB_CONFIG['type']
    
    if db_type == 'mysql':
        # MySQL connection
        return f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    elif db_type == 'postgres':
        # PostgreSQL connection
        port = DB_CONFIG.get('port', '5432')  # Default PostgreSQL port
        return f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{port}/{DB_CONFIG['database']}"
    else:
        raise ValueError(f"Tipo de banco de dados não suportado: {db_type}")

# Create database connection URL
DATABASE_URL = get_database_url()

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
        r"..\dump\mysql\bin\mysqldump.exe",
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


def get_postgres_path():
    """
    Tenta localizar o caminho do PostgreSQL através dos caminhos comuns de instalação
    """
    if platform.system() != 'Windows':
        return 'pg_dump'  # No Linux/Mac, assume que está no PATH
        
    # Lista de possíveis caminhos do PostgreSQL
    possible_paths = [
        r"..\dump\PostgreSQL\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\13\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\12\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\11\bin\pg_dump.exe",
    ]
    
    # Tenta os caminhos comuns
    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    raise FileNotFoundError("pg_dump não encontrado. Por favor, verifique se o PostgreSQL está instalado corretamente.")


def backup_database():
    """Create a backup of the database"""
    try:
        # Create backups directory if it doesn't exist
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Determinar o tipo de banco de dados e executar o backup apropriado
        db_type = DB_CONFIG['type']
        
        if db_type == 'mysql':
            return backup_mysql(timestamp)
        elif db_type == 'postgres':
            return backup_postgres(timestamp)
        else:
            raise ValueError(f"Backup não suportado para o tipo de banco: {db_type}")
            
    except Exception as e:
        error_msg = f"Erro ao criar backup do banco: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        raise


def backup_mysql(timestamp):
    """Execute MySQL backup"""
    try:
        backup_file = os.path.join(BACKUP_DIR, f"{DB_CONFIG['database']}_mysql_backup_{timestamp}.sql")
        
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
        if DB_CONFIG['password']:
            command.extend(['-p' + DB_CONFIG['password']])
        
        # Inicializa a barra de progresso
        progress_text = "Backup MySQL em andamento. Por favor, aguarde..."
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
            my_bar.progress(100, text="Backup MySQL concluído com sucesso!")
            time.sleep(1)  # Aguarda 1 segundo para exibir a mensagem de sucesso
            my_bar.empty()  # Remove a barra de progresso
            
            if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                logger.info(f"MySQL database backup created successfully: {backup_file}")
                st.toast(f"Backup MySQL criado com sucesso!", icon="✅")
                return backup_file
            else:
                raise Exception("MySQL backup file was not created or is empty")
        else:
            stderr_output = process.stderr.read() if hasattr(process.stderr, 'read') else "Unknown error"
            raise Exception(f"Erro ao executar mysqldump: {stderr_output}")
    
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


def backup_postgres(timestamp):
    """Execute PostgreSQL backup"""
    try:
        backup_file = os.path.join(BACKUP_DIR, f"{DB_CONFIG['database']}_postgres_backup_{timestamp}.sql")
        
        # Get pg_dump path
        pg_dump_path = get_postgres_path()
        logger.info(f"Usando pg_dump de: {pg_dump_path}")

        # Preparar comando
        command = [
            pg_dump_path,
            '-U', DB_CONFIG['user'],
            '-d', DB_CONFIG['database'],
            '-h', DB_CONFIG['host'],
            '--clean',  # Adiciona DROP TABLE antes de CREATE TABLE
            '-f', backup_file
        ]
        
        # Se tiver porta especificada
        if 'port' in DB_CONFIG:
            command.extend(['-p', DB_CONFIG['port']])
        
        # Configura a variável de ambiente PGPASSWORD para autenticação
        env = os.environ.copy()
        if DB_CONFIG['password']:
            env['PGPASSWORD'] = DB_CONFIG['password']
        
        # Inicializa a barra de progresso
        progress_text = "Backup PostgreSQL em andamento. Por favor, aguarde..."
        my_bar = st.progress(0, text=progress_text)
        
        # Variável para armazenar o valor do progresso
        progress_value = 0
        
        # Execute command with Popen
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Monitorar o processo em tempo real
        while process.poll() is None:
            time.sleep(0.5)
            if progress_value < 90:
                progress_value += 5
                my_bar.progress(progress_value, text=progress_text)
        
        # Verifica se o processo foi concluído com sucesso
        if process.returncode == 0:
            my_bar.progress(100, text="Backup PostgreSQL concluído com sucesso!")
            time.sleep(1)
            my_bar.empty()
            
            if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                logger.info(f"PostgreSQL database backup created successfully: {backup_file}")
                st.toast(f"Backup PostgreSQL criado com sucesso!", icon="✅")
                return backup_file
            else:
                raise Exception("PostgreSQL backup file was not created or is empty")
        else:
            stderr_output = process.stderr.read() if hasattr(process.stderr, 'read') else "Unknown error"
            raise Exception(f"Erro ao executar pg_dump: {stderr_output}")
    
    except FileNotFoundError as e:
        error_msg = str(e)
        logger.error(error_msg)
        st.error("""
        pg_dump não encontrado. Por favor, verifique:
        1. Se o PostgreSQL está instalado no sistema
        2. Se o diretório bin do PostgreSQL está no PATH do sistema
        3. Ou instale o PostgreSQL se ainda não estiver instalado
        """)
        raise


def restore_database(backup_file):
    """Restore database from a backup file"""
    my_bar = None
    try:
        # Determinar o tipo de banco de dados com base no nome do arquivo de backup
        if "mysql_backup" in backup_file:
            restore_mysql(backup_file)
        elif "postgres_backup" in backup_file:
            restore_postgres(backup_file)
        else:
            # Tenta determinar pelo tipo de banco configurado atualmente
            db_type = DB_CONFIG['type']
            if db_type == 'mysql':
                restore_mysql(backup_file)
            elif db_type == 'postgres':
                restore_postgres(backup_file)
            else:
                raise ValueError(f"Não foi possível determinar o tipo de banco de dados do backup: {backup_file}")
                
    except Exception as e:
        error_msg = f"Erro ao restaurar backup: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        raise


def restore_mysql(backup_file):
    """Restore a MySQL database from backup file"""
    my_bar = None
    try:
        # Get mysql path from the same directory as mysqldump
        mysql_path = str(Path(get_mysql_path()).parent / "mysql.exe")
        if not os.path.exists(mysql_path):
            mysql_path = "mysql"  # Fallback to PATH
            
        logger.info(f"Usando mysql de: {mysql_path}")
        
        # Inicializa a barra de progresso
        progress_text = "Restauração MySQL em andamento. Por favor, aguarde..."
        my_bar = st.progress(0, text=progress_text)
        progress_value = 0
        
        # Preparar comando
        command = [
            mysql_path,
            '-u', DB_CONFIG['user'],  # usuário
            DB_CONFIG['database']     # nome do banco
        ]
        
        # Se tiver senha, adicione aqui
        if DB_CONFIG['password']:
            command.extend(['-p' + DB_CONFIG['password']])
        
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
                my_bar.progress(100, text="Restauração MySQL concluída com sucesso!")
                time.sleep(1)
                my_bar.empty()
                logger.info(f"MySQL database restored successfully from: {backup_file}")
                st.toast("Restauração MySQL concluída com sucesso!", icon="✅")
            else:
                stderr_output = process.stderr.read() if hasattr(process.stderr, 'read') else "Unknown error"
                my_bar.progress(100, text="Erro na restauração MySQL!")
                time.sleep(2)
                raise Exception(f"Erro na restauração MySQL: {stderr_output}")
            
    except FileNotFoundError as e:
        error_msg = "MySQL client não encontrado. Por favor, verifique a instalação do MySQL."
        if my_bar: my_bar.empty()
        logger.error(error_msg)
        st.error(error_msg)
        raise
        
    except Exception as e:
        error_msg = f"Erro ao restaurar backup MySQL: {str(e)}"
        if my_bar: my_bar.empty()
        logger.error(error_msg)
        st.error(error_msg)
        raise


def restore_postgres(backup_file):
    """Restore a PostgreSQL database from backup file"""
    my_bar = None
    try:
        # Get psql path from the same directory as pg_dump
        psql_path = str(Path(get_postgres_path()).parent / "psql.exe")
        if not os.path.exists(psql_path):
            psql_path = "psql"  # Fallback to PATH
            
        logger.info(f"Usando psql de: {psql_path}")
        
        # Inicializa a barra de progresso
        progress_text = "Restauração PostgreSQL em andamento. Por favor, aguarde..."
        my_bar = st.progress(0, text=progress_text)
        progress_value = 0
        
        # Preparar comando
        command = [
            psql_path,
            '-U', DB_CONFIG['user'],  # usuário
            '-d', DB_CONFIG['database'],  # nome do banco
            '-h', DB_CONFIG['host'],  # host
            '-f', backup_file  # arquivo de backup
        ]
        
        # Se tiver porta especificada
        if 'port' in DB_CONFIG:
            command.extend(['-p', DB_CONFIG['port']])
        
        # Configura a variável de ambiente PGPASSWORD para autenticação
        env = os.environ.copy()
        if DB_CONFIG['password']:
            env['PGPASSWORD'] = DB_CONFIG['password']
        
        # Execute command with Popen
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Monitorar o processo em tempo real
        while process.poll() is None:
            time.sleep(0.5)
            # Atualiza progresso simulado
            if progress_value < 90:
                progress_value += 2
                my_bar.progress(progress_value, text=progress_text)
                
        # Verifica conclusão
        if process.returncode == 0:
            my_bar.progress(100, text="Restauração PostgreSQL concluída com sucesso!")
            time.sleep(1)
            my_bar.empty()
            logger.info(f"PostgreSQL database restored successfully from: {backup_file}")
            st.toast("Restauração PostgreSQL concluída com sucesso!", icon="✅")
        else:
            stderr_output = process.stderr.read() if hasattr(process.stderr, 'read') else "Unknown error"
            my_bar.progress(100, text="Erro na restauração PostgreSQL!")
            time.sleep(2)
            raise Exception(f"Erro na restauração PostgreSQL: {stderr_output}")
        
    except FileNotFoundError as e:
        error_msg = "PostgreSQL client (psql) não encontrado. Por favor, verifique a instalação do PostgreSQL."
        if my_bar: my_bar.empty()
        logger.error(error_msg)
        st.error(error_msg)
        raise
        
    except Exception as e:
        error_msg = f"Erro ao restaurar backup PostgreSQL: {str(e)}"
        if my_bar: my_bar.empty()
        logger.error(error_msg)
        st.error(error_msg)
        raise