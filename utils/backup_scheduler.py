# utils/backup_scheduler.py
import schedule
import time
import streamlit as st
import threading
from datetime import datetime
from config.database import backup_database
from utils.logger import logger
import json
import os
from services.restore_service import save_last_backup
from utils.message_handler import message_handler, MessageType
from config.settings import BACKUP_DIR


class BackupScheduler:
    def __init__(self):
        self.config_file = "config/backup_config.json"
        self.default_config = {
            "schedule_type": "daily",  # daily, weekly, monthly
            "time": "23:00",           # Horário do backup
            "day": "1",                # Dia do mês (para monthly) ou dia da semana (para weekly)
            "enabled": True,           # Status do agendamento
            "retention_method": "Dias", # Método de retenção: Dias ou Quantidade de Backups
            "retain_days": 30,         # Dias para manter backups antigos
            "retain_count": 10,        # Quantidade de backups a serem mantidos
            "retention_enabled": False, # Método de retenção desabilitado por padrão
        }
        self.load_config()
        self.running = False
        self._schedule_thread = None


    def load_config(self):
        """Carrega ou cria configuração de backup"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                self.config = self.default_config
                self.save_config()
                
        except Exception as e:
            logger.error(f"Erro ao carregar configuração de backup: {str(e)}")
            self.config = self.default_config

    def save_config(self):
        """Salva configuração de backup"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Erro ao salvar configuração de backup: {str(e)}")

    def cleanup_old_backups(self):
        """Remove backups mais antigos que o período configurado, se o método de retenção estiver habilitado."""
        try:
            # Verifica se o método de retenção está habilitado
            if not self.config.get("retention_enabled", False):
                logger.info("Método de retenção de backups desabilitado. Nenhum backup será excluído.")
                return  # Sai da função sem excluir backups

            if not os.path.exists(BACKUP_DIR):
                return

            backups = sorted(
                [f for f in os.listdir(BACKUP_DIR) if f.endswith('.sql')],
                key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x)),
                reverse=True
            )

            retention_method = self.config.get("retention_method", "Dias")
            
            if retention_method == "Dias":
                retain_days = self.config.get("retain_days", 30)
                current_time = datetime.now()
                for filename in backups:
                    file_path = os.path.join(BACKUP_DIR, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    age_days = (current_time - file_time).days
                    
                    if age_days > retain_days:
                        os.remove(file_path)
                        logger.info(f"Backup antigo removido: {filename}")
            else:
                retain_count = self.config.get("retain_count", 10)
                for filename in backups[retain_count:]:
                    file_path = os.path.join(BACKUP_DIR, filename)
                    os.remove(file_path)
                    logger.info(f"Backup antigo removido: {filename}")
                        
        except Exception as e:
            logger.error(f"Erro ao limpar backups antigos: {str(e)}")

    def scheduled_backup(self):
        """Realiza o backup automático e salva as informações do último backup."""
        try:
            logger.info("Iniciando backup agendado")
            backup_file = backup_database()  # Função que realiza o backup
            save_last_backup(backup_file)  # Salva as informações do último backup
            self.cleanup_old_backups()
            logger.info(f"Backup automático realizado: {backup_file}")


        except Exception as e:
            logger.error(f"Erro no backup agendado: {str(e)}")

    def setup_schedule(self):
        """Configura o agendamento baseado nas configurações"""
        schedule.clear()
        
        if not self.config["enabled"]:
            return
            
        job_time = self.config["time"]
        
        if self.config["schedule_type"] == "daily":
            schedule.every().day.at(job_time).do(self.scheduled_backup)
        
        elif self.config["schedule_type"] == "weekly":
            days = {
                "0": schedule.every().sunday,
                "1": schedule.every().monday,
                "2": schedule.every().tuesday,
                "3": schedule.every().wednesday,
                "4": schedule.every().thursday,
                "5": schedule.every().friday,
                "6": schedule.every().saturday
            }
            days[self.config["day"]].at(job_time).do(self.scheduled_backup)
        
        elif self.config["schedule_type"] == "monthly":
            schedule.every().month.at(job_time).do(self.scheduled_backup)

    def run_scheduler(self):
        """Executa o agendador em loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)

    def start(self):
        """Inicia o agendador"""
        if not self.running:
            self.running = True
            self.setup_schedule()
            self._schedule_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self._schedule_thread.start()
            logger.info("Agendador de backup iniciado")

    def stop(self):
        """Para o agendador"""
        self.running = False
        if self._schedule_thread:
            self._schedule_thread.join()
            logger.info("Agendador de backup parado")

    def update_config(self, new_config):
        """Atualiza a configuração e reinicia o agendador"""
        self.config.update(new_config)
        self.save_config()
        self.setup_schedule()
        logger.info("Configuração de backup atualizada")