# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()  # Carrega o .env automaticamente

# configurações do jwt
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# Email e senha padrão para o usuário inicial
DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD")

# conexão com o banco de dados
DB_CONFIG = {
    'type': os.getenv('DB_TYPE', 'mysql'),  # 'mysql' ou 'postgres'
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'port': os.getenv('DB_PORT'),  # Porta opcional, útil para PostgreSQL
}

# Criar diretório de logs se não existir
LOG_DIR = "./tmp/.logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Caminhos dos arquivos de persistência
BACKUP_DIR = "./tmp/.backups"
BACKUP_CONFIG_FILE = os.path.join(BACKUP_DIR, "backup_config.json")
LAST_RESTORE_FILE = os.path.join(BACKUP_DIR, "last_restore.json")
LAST_BACKUP_FILE = os.path.join(BACKUP_DIR, "last_backup.json")

# Cria o diretório de backups se não existir
os.makedirs(BACKUP_DIR, exist_ok=True)

# Criar diretório de captura de imagens qrcode se não existir
CAPTURE_DIR = "./tmp/.capturas"
os.makedirs(CAPTURE_DIR, exist_ok=True)

# Configuração do cache
CACHE_DIR = "./tmp/.cache"
CHROME_DRIVER_CACHE_PATH = os.path.join(CACHE_DIR, "chromedriver_path.txt")

# Garante que o diretório existe (funciona em qualquer SO)
os.makedirs(CACHE_DIR, exist_ok=True)