# utils/logger.py
import logging
import os
from datetime import datetime
from config.settings import LOG_DIR


# Nome do arquivo de log com data
log_filename = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m')}.log")

# Configurar o logging
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Criar logger para uso na aplicação
logger = logging.getLogger(__name__)

# Adicionar handler para console também (opcional)
#console_handler = logging.StreamHandler()
#console_handler.setLevel(logging.INFO)
#formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#console_handler.setFormatter(formatter)
#logger.addHandler(console_handler)