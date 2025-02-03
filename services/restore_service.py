# services/backup_service.py
import streamlit as st
import os
from datetime import datetime
import json
from config.settings import LAST_BACKUP_FILE, LAST_RESTORE_FILE

def load_last_restore():
    """Carrega a última restauração do arquivo JSON."""
    if os.path.exists(LAST_RESTORE_FILE):
        with open(LAST_RESTORE_FILE, "r") as file:
            return json.load(file)
    return None

def save_last_restore(backup_file):
    """Salva a última restauração no arquivo JSON."""
    last_restore = {
        "file": os.path.basename(backup_file),
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    with open(LAST_RESTORE_FILE, "w") as file:
        json.dump(last_restore, file)

def load_last_backup():
    """Carrega o último backup do arquivo JSON."""
    if os.path.exists(LAST_BACKUP_FILE):
        with open(LAST_BACKUP_FILE, "r") as file:
            return json.load(file)
    return None

def save_last_backup(backup_file):
    """Salva o último backup no arquivo JSON."""
    last_backup = {
        "file": os.path.basename(backup_file),
        "size": os.path.getsize(backup_file) / (1024 * 1024),  # Tamanho em MB
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    with open(LAST_BACKUP_FILE, "w") as file:
        json.dump(last_backup, file)