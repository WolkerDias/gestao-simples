# app.py
import streamlit as st
import jwt
from sqlalchemy.exc import OperationalError, DatabaseError
from models.usuario import Usuario
from views.auth.list import UsuarioListView
from views.qrcode.view import QRCodeView
from views.cupom.view import CupomView
from views.produto.list import ProdutoListView
from views.produto.associacao.list import AssociacoesListView
from views.nota_entrada.list import NotaEntradaListView
from views.estoque.inventario.list import InventarioListView
from views.estoque.auditoria.list import AuditoriaListView
from views.fornecedor.list import FornecedorListView
from views.configuracoes.backup_view import BackupView
from views.configuracoes.database_view import DatabaseConfigView
from config.database import engine
from models.base import Base
from utils.logger import logger
from utils.backup_scheduler import BackupScheduler
from services.auth_service import AuthService
from views.auth.login import login_view
from views.auth.register import register_view
from views.auth.change_password import change_password_view
from dotenv import load_dotenv

load_dotenv()

# Configurar página DEVE SER A PRIMEIRA COISA
st.set_page_config(
    page_title="Sistema de Gestão",
    page_icon="🏪",
    layout="wide"
)

# Estado para rastrear falha de conexão
if 'db_connection_failed' not in st.session_state:
    st.session_state.db_connection_failed = False

# Initialize database
try:
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
except (OperationalError, DatabaseError) as e:
    st.session_state.db_connection_failed = True
    logger.error(f"Erro de conexão com o banco de dados: {str(e)}")
except Exception as e:
    st.error("Falha ao inicializar o banco de dados. Verifique os registros de log para obter detalhes.", icon=":material/database:")
    logger.error(f"Falha na inicialização do banco de dados: {str(e)}")
    st.stop()  # Para a execução se for um erro inesperado

# Estrutura principal da aplicação
if st.session_state.db_connection_failed:
    # Exibir DatabaseConfigView diretamente, mas sem exibir a senha
    st.error(
        "Não foi possível conectar ao banco de dados. "
        "Por favor, verifique as configurações abaixo e reinicie a aplicação após salvar.",
        icon=":material/database:"
    )
    
    DatabaseConfigView(is_authenticated=False)
else:
    # Initialize backup scheduler
    if 'backup_scheduler' not in st.session_state:
        st.session_state.backup_scheduler = BackupScheduler()
        st.session_state.backup_scheduler.start()

    # Inicializar Auth Service
    auth_service = AuthService()
    auth_service.criar_admin_inicial()

    # CSS Customizado
    st.markdown("""
        <style>
            h1 { font-size: 1.5rem !important; margin: 0.1rem 0 !important; }
            h2 { font-size: 1.4rem !important; margin: 0.1rem 0 !important; }
            h3 { font-size: 1.2rem !important; margin: 0.1rem 0 !important; }
            .block-container { padding: 1.2rem !important; }
        </style>
    """, unsafe_allow_html=True)

    if 'token' not in st.session_state:
        login_view()
    else:
        try:
            # Verificar token
            auth_service.verificar_token(st.session_state.token)

            # Páginas
            pages = {
                "GESTÃO DE ESTOQUE": [
                    st.Page(ProdutoListView, title="Produtos", icon=":material/shopping_cart:"),
                    st.Page(AssociacoesListView, title="Produtos Associados", icon=":material/queue:"),
                    st.Page(InventarioListView, title="Inventários", icon=":material/list:"),
                    st.Page(AuditoriaListView, title="Auditorias", icon=":material/analytics:"),
                    st.Page(FornecedorListView, title="Fornecedores", icon=":material/store:"),
                ],
                "COMPRAS": [        
                    st.Page(NotaEntradaListView, title="Notas Fiscais", icon=":material/receipt_long:"),
                    st.Page(CupomView, title="Cupons Não Fiscais", icon=":material/receipt:"),
                    st.Page(QRCodeView, title="Leitor de QR Code", icon=":material/qr_code:"),
                ],
                "CONFIGURAÇÕES": [
                    st.Page(UsuarioListView, title="Usuários", icon=":material/account_circle:"),
                    st.Page(BackupView, title="Backup e Restauração", icon=":material/database:"),
                    st.Page(DatabaseConfigView, title="Configuração de Banco", icon=":material/settings_applications:"),
                ]
            }

            # Verificação de permissão para páginas administrativas
            if not st.session_state.usuario.get("is_admin"):
                # Remover páginas restritas a admin
                del pages["GESTÃO DE ESTOQUE"][4]  # Fornecedores
                del pages["COMPRAS"]
                del pages["CONFIGURAÇÕES"]

            # Menu do usuário na sidebar
            with st.sidebar:
                with st.popover(st.session_state.usuario.get("nome"), icon=":material/account_circle:", use_container_width=True):
                    if st.session_state.usuario.get("is_admin"):
                        st.write("🔑 Administrador")
                    else:
                        st.write("👤 Usuário")

                    if st.button("Alterar Senha", use_container_width=True, icon=":material/edit:"):
                        change_password_view()

                    if st.button("Sair", use_container_width=True, icon=":material/logout:"):
                        del st.session_state.token
                        del st.session_state.usuario
                        st.rerun()

            pg = st.navigation(pages)
            pg.run()

        except jwt.ExpiredSignatureError:
            st.write("")
            st.write("")
            st.error("Sessão expirada. Faça login novamente.")
            del st.session_state.token
        except Exception as e:
            st.error("Erro de autenticação")
            logger.error(f"Auth error: {str(e)}")
            del st.session_state.token