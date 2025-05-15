# views/configuracoes/database_view.py
import streamlit as st
import os
from config.settings import DB_CONFIG
from utils.logger import logger
from dotenv import load_dotenv, find_dotenv, set_key


class DatabaseConfigView:
    def __init__(self, is_authenticated=True):
        """Inicializa a classe com as configurações atuais do banco de dados"""
        self.db_type = DB_CONFIG.get('type', 'mysql')
        self.db_user = DB_CONFIG.get('user', '')
        self.db_password = DB_CONFIG.get('password', '') if is_authenticated else ''
        self.db_host = DB_CONFIG.get('host', 'localhost')
        self.db_name = DB_CONFIG.get('database', '')
        self.db_port = DB_CONFIG.get('port', '')
        self.render()

    def _render_form(self):
        """Renderiza o formulário de configuração do banco de dados"""
        with st.form("database_config_form"):
            st.subheader("Tipo de Banco de Dados")

            # Seleção do tipo de banco
            new_db_type = st.radio(
                "Selecione o tipo de banco de dados:",
                ["mysql", "postgres"],
                index=0 if self.db_type == "mysql" else 1,
                format_func=lambda x: "MySQL" if x == "mysql" else "PostgreSQL",
                horizontal=True
            )

            # Campos comuns
            col1, col2 = st.columns(2)
            with col1:
                new_db_user = st.text_input("Usuário", value=self.db_user)
            with col2:
                new_db_password = st.text_input("Senha", type="password", value=self.db_password)

            col1, col2 = st.columns(2)
            with col1:
                new_db_host = st.text_input("Host", value=self.db_host)
            with col2:
                new_db_name = st.text_input("Nome do Banco", value=self.db_name)

            # Campo de porta
            new_db_port = st.text_input(
                "Porta (opcional)",
                value=self.db_port,
                help="porta padrão (MySQL: 3306, PostgreSQL: 5432)"
            )

            st.warning("""
            **⚠️ Atenção!** Modificar estas configurações requer reinicialização da aplicação para ter efeito.
            Certifique-se de que o banco de dados está configurado e acessível antes de salvar.
            """)

            submit = st.form_submit_button("Salvar Configurações", use_container_width=True)
            return submit, {
                'type': new_db_type,
                'user': new_db_user,
                'password': new_db_password,
                'host': new_db_host,
                'database': new_db_name,
                'port': new_db_port
            }

    def _save_config(self, config):
        """Salva as configurações no arquivo .env"""
        try:
            # Encontrar o arquivo .env
            dotenv_path = find_dotenv()
            if not dotenv_path:
                st.error("Arquivo .env não encontrado. Impossível salvar as configurações.")
                return False

            # Atualizar variáveis no .env
            set_key(dotenv_path, "DB_TYPE", config['type'])
            set_key(dotenv_path, "DB_USER", config['user'])
            set_key(dotenv_path, "DB_PASSWORD", config['password'])
            set_key(dotenv_path, "DB_HOST", config['host'])
            set_key(dotenv_path, "DB_NAME", config['database'])

            # Porta só é salva se for fornecida
            if config['port']:
                set_key(dotenv_path, "DB_PORT", config['port'])

            st.success("Configurações salvas com sucesso. Reinicie a aplicação para aplicar as mudanças.")
            logger.info(
                f"Database configuration updated. Type: {config['type']}, "
                f"User: {config['user']}, Host: {config['host']}, DB: {config['database']}"
            )
            load_dotenv(override=True)
            return True

        except Exception as e:
            st.error(f"Erro ao salvar configurações: {str(e)}")
            logger.error(f"Error saving database config: {str(e)}")
            return False


    def render(self):
        """Renderiza a view completa de configuração do banco de dados"""
        st.header("Configuração do Banco de Dados")

        # Renderizar formulário e processar submissão
        submit, config = self._render_form()
        if submit:
            self._save_config(config)