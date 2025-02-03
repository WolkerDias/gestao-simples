# app.py
import streamlit as st
from views.qrcode.view import QRCodeView
from views.nfce.list import NFCeListView
from views.fornecedor.list import FornecedorListView
from views.configuracoes.backup_view import BackupView
from config.database import engine
from models.base import Base
from utils.logger import logger
from utils.backup_scheduler import BackupScheduler

# Configurar página
st.set_page_config(
    page_title="Sistema de Gestão",
    page_icon="🏪",
    layout="wide"
)

# Initialize database when app starts
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    st.error("Failed to initialize database. Check the logs for details.")
    logger.error(f"Database initialization failed: {str(e)}")

# Initialize and start backup scheduler
scheduler = BackupScheduler()
scheduler.start()

pages = {
    "Gestão de Estoque": [
        st.Page(QRCodeView, title="Leitor de QR Code", icon=":material/qr_code:"),
        st.Page(NFCeListView, title="Notas Fiscais", icon=":material/receipt_long:"),
        #st.Page(ProdutoView, title="Produtos", icon=":material/shopping_cart:"),
        st.Page(FornecedorListView, title="Fornecedores", icon=":material/store:"),
    ],
    "Configurações": [
        st.Page(BackupView, title="Backup e Restauração", icon=":material/database:"),
    ]
}

pg = st.navigation(pages)
pg.run()