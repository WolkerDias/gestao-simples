# views/configuracoes/backup_view.py
import streamlit as st
from config.database import backup_database
import os
from datetime import datetime
from utils.logger import logger
from utils.backup_scheduler import BackupScheduler
from services.restore_service import save_last_backup, load_last_backup, load_last_restore
from utils.message_handler import message_handler, MessageType
from config.settings import BACKUP_DIR
from views.configuracoes.restore import confirm_restore_dialog

class BackupView:
    def __init__(self):
        self.scheduler = BackupScheduler()
        self.run()


    def _show_manual_backup(self):
        """Exibe a seção de backup manual."""
        st.write("Execute um backup manual do banco de dados.")
        
        if st.button("Fazer Backup", type="primary", icon=":material/database:"):
            try:
                backup_file = backup_database()
                
                # Salva as informações do último backup
                save_last_backup(backup_file)
                
                # Exibir detalhes do backup
                backup_size = os.path.getsize(backup_file) / (1024 * 1024)  # Convert to MB
                
            except Exception as e:
                st.error(f"Erro ao criar backup: {str(e)}")
                logger.error(f"Backup creation error: {str(e)}")

    def _show_backup_settings(self):
        """Exibe e gerencia as configurações de backup automático"""
        st.write("Configure o agendamento de backups automáticos.")
        
        config = self.scheduler.config
        
        # Expander para as configurações de backup automático
        #with st.expander("Configure o agendamento de backups automáticos.", expanded=True):
        with st.container(border=True):
            # Toggle para habilitar/desabilitar backup automático
            enabled = st.toggle("Habilitar Backup Automático", config["enabled"])
            
            # Se o backup automático estiver habilitado, exibe as configurações
            if enabled:
                # Tipo de agendamento
                schedule_type = st.selectbox(
                    "Frequência",
                    options=["daily", "weekly", "monthly"],
                    index=["daily", "weekly", "monthly"].index(config["schedule_type"])
                )
                
                # Horário
                time = st.time_input(
                    "Horário do Backup",
                    datetime.strptime(config["time"], "%H:%M").time(),
                    step=300 # intervalo de tempo em segundos
                )
                
                # Dia (para weekly e monthly)
                if schedule_type == "weekly":
                    day = st.selectbox(
                        "Dia da Semana",
                        options=["0", "1", "2", "3", "4", "5", "6"],
                        index=int(config["day"]),
                        format_func=lambda x: ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"][int(x)]
                    )
                elif schedule_type == "monthly":
                    day = st.selectbox(
                        "Dia do Mês",
                        options=[str(i) for i in range(1, 29)],
                        index=int(config["day"]) - 1
                    )
                else:
                    day = "1"

                st.divider()
                
                # Toggle para habilitar/desabilitar o método de retenção de backups
                retention_enabled = st.toggle("Remover backups antigos", config.get("retention_enabled", False))
                
                # Se o método de retenção estiver habilitado, exibe as opções
                if retention_enabled:
                    # Método de retenção de backups
                    retention_method = st.radio(
                        "Método de Retenção de Backups",
                        options=["Dias", "Quantidade de Backups"],
                        index=0 if config.get("retention_method", "Dias") == "Dias" else 1
                    )
                    
                    if retention_method == "Dias":
                        retain_value = st.number_input(
                            "Dias para manter backups",
                            min_value=1,
                            max_value=365,
                            value=config.get("retain_days", 30)
                        )
                    else:
                        retain_value = st.number_input(
                            "Quantidade de Backups a serem mantidos",
                            min_value=1,
                            max_value=100,
                            value=config.get("retain_count", 10)
                        )
                else:
                    retention_method = "Dias"  # Valor padrão se o método de retenção estiver desabilitado
                    retain_value = config.get("retain_days", 30)  # Valor padrão
            
            # Salvar configurações
            if st.button("Salvar Configurações"):
                new_config = {
                    "enabled": enabled,
                    "schedule_type": schedule_type if enabled else config["schedule_type"],
                    "time": time.strftime("%H:%M") if enabled else config["time"],
                    "day": day if enabled else config["day"],
                    "retention_enabled": retention_enabled if enabled else config.get("retention_enabled", False),
                    "retention_method": retention_method if enabled and retention_enabled else config.get("retention_method", "Dias"),
                    "retain_days": retain_value if enabled and retention_enabled and retention_method == "Dias" else config.get("retain_days", 30),
                    "retain_count": retain_value if enabled and retention_enabled and retention_method == "Quantidade de Backups" else config.get("retain_count", 10)
                }
                
                self.scheduler.update_config(new_config)
                st.toast("Configurações salvas com sucesso!", icon="✅")

            
    def _show_existing_backups(self):
        """Lista os backups existentes dentro de um container."""
        
        # Cria um container para os backups existentes
        with st.container(border=True, height=500):
            st.subheader("Backups Existentes")
            
            if os.path.exists(BACKUP_DIR):
                backups = sorted(
                    [f for f in os.listdir(BACKUP_DIR) if f.endswith('.sql')],
                    key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x)),
                    reverse=True
                )
                
                if backups:
                    for i, backup in enumerate(backups):
                        backup_path = os.path.join(BACKUP_DIR, backup)
                        backup_size = os.path.getsize(backup_path) / (1024 * 1024)  # Convert to MB
                        backup_date = datetime.fromtimestamp(os.path.getmtime(backup_path))
                        
                        
                        # Apenas o primeiro expander será inicialmente expandido
                        with st.expander(f"Backup: {backup}", expanded=(i == 0)):
                            st.write(f"Tamanho: {backup_size:.2f} MB")
                            st.write(f"Data: {backup_date.strftime('%d/%m/%Y %H:%M:%S')}")
                            
                            col1, col2 = st.columns(2)
                            
                            # Botão de Download
                            with col1:
                                with open(backup_path, 'rb') as f:
                                    st.download_button(
                                        label="📥 Download Backup",
                                        data=f,
                                        file_name=backup,
                                        mime="application/sql",
                                        key=f"download_{backup}",  # Chave única para o botão
                                        help="Clique para baixar este backup",  # Texto de ajuda
                                        use_container_width=True,  # Ocupa toda a largura do container
                                        type="secondary",  # Estilo secundário (cor menos destacada)
                                    )
                            
                            # Botão de Restauração
                            with col2:
                                if st.button(
                                    "🔄 Restaurar Backup",
                                    key=f"restore_{backup}",  # Chave única para o botão
                                    help="Clique para restaurar este backup",  # Texto de ajuda
                                    use_container_width=True,  # Ocupa toda a largura do container
                                    type="secondary",  # Estilo secundário (cor menos destacada)
                                ):
                                    # Abre o diálogo de confirmação
                                    confirm_restore_dialog(backup_path)
                else:
                    st.info("Nenhum backup encontrado.")
            else:
                st.info("Diretório de backups não encontrado, realize o primeiro backup.")
                
    def run(self):
        st.title("Backup e restauração de dados")
        message_handler.display_toast_message()  
        
        with st.expander(f"Últimas alterações"):
            # Exibe a última restauração e o último backup lado a lado
            col1, col2 = st.columns(2)
            
            with col1:
                # Último Backup (manual ou automático)
                last_backup = load_last_backup()
                if last_backup:
                    st.subheader("Último backup feito")
                    st.write(f"- Arquivo: {last_backup['file']}")
                    st.write(f"- Tamanho: {last_backup['size']:.2f} MB")
                    st.write(f"- Data: {last_backup['date']}")
                else:
                    st.subheader("Último backup feito")
                    st.info("Nenhum backup criado.")

            with col2:
                # Última Restauração
                last_restore = load_last_restore()
                if last_restore:
                    st.subheader("Última restauração de backup")
                    st.write(f"- Arquivo: {last_restore['file']}")
                    st.write(f"- Data: {last_restore['date']}")
                else:
                    st.subheader("Última restauração de backup")
                    st.info("Nenhuma restauração realizada.")
            

        with st.container(border=True):
            
            # Tabs para separar backup manual e configurações
            tab1, tab2 = st.tabs([ "Backup Manual e Restauração", "Configurações de Backup Automático"])
            
            with tab1:
                self._show_manual_backup()
                self._show_existing_backups()
            
            with tab2:
                self._show_backup_settings()