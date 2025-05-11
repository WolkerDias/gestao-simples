# services/auditoria_service.py
from repositories.auditoria_repository import AuditoriaRepository
from services.inventario_estoque_service import InventarioEstoqueService
import streamlit as st

class AuditoriaService:
    def __init__(self):
        self.repository = AuditoriaRepository()
        self.inventario_service = InventarioEstoqueService()

    def obter_dados_auditoria(self, referencia_inventario: str = None):
        dados = self.repository.obter_dados_peps(referencia_inventario)           
        return dados

    def listar_referencias_inventarios(self):
        return [inv.referencia for inv in self.inventario_service.listar_inventarios()]    