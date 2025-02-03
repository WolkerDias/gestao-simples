# config/settings.py
import os

# conexão com o banco de dados
USER = 'root'
PASSWORD = ''
HOST = 'localhost'
DATABASE = 'db_teste'

# Criar diretório de logs se não existir
LOG_DIR = ".logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Caminhos dos arquivos de persistência
BACKUP_DIR = ".backups"
LAST_RESTORE_FILE = os.path.join(BACKUP_DIR, "last_restore.json")
LAST_BACKUP_FILE = os.path.join(BACKUP_DIR, "last_backup.json")

# Cria o diretório de backups se não existir
os.makedirs(BACKUP_DIR, exist_ok=True)

# Criar diretório de captura de imagens qrcode se não existir
CAPTURE_DIR = ".capturas"
os.makedirs(CAPTURE_DIR, exist_ok=True)