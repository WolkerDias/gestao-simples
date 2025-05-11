# services/inventario_estoque_service.py
from repositories.inventario_estoque_repository import InventarioEstoqueRepository
from utils.validacoes import ValidationError, validar_quantidade_positiva, validar_formato_referencia
from datetime import datetime

class InventarioEstoqueService:
    def __init__(self):
        self.repository = InventarioEstoqueRepository()

    def criar_inventario(self, dados):
        validar_formato_referencia(dados.referencia)       
    
        # Verifica se a referência já existe
        if self.repository.buscar_por_referencia(dados.referencia):
            raise ValidationError(f"Já existe um inventário com a referência '{dados.referencia}'.")
        
        return self.repository.criar(dados)
        
    def atualizar_inventario(self, inventario_id: int, dados):
        validar_formato_referencia(dados.referencia)
        
        # Verifica se a referência já existe (excluindo o próprio inventário)
        existing = self.repository.buscar_por_referencia(dados.referencia)
        if existing and existing.id != inventario_id:
            raise ValidationError(f"Já existe um inventário com a referência '{dados.referencia}'.")
        
        return self.repository.atualizar(inventario_id, dados)    

    def encerrar_contagem(self, inventario_id: int, data_fim: datetime = None):
        try:
            return self.repository.encerrar_contagem(
                inventario_id,
                data_fim
            )
        except Exception as e:
            if "Contagem já encerrada" in str(e):
                raise ValidationError(str(e)) from e
            raise ValidationError(f"Erro ao encerrar contagem: {str(e)}") from e 

    def adicionar_item(self, inventario_id: int, produto_id: int, quantidade: float):
        validar_quantidade_positiva(quantidade)
        return self.repository.adicionar_item(inventario_id, produto_id, quantidade)
    
    def listar_inventarios(self):
        return self.repository.listar()

    def buscar_inventario_por_id(self, inventario_id: int):
        return self.repository.buscar_por_id(inventario_id)

    def listar_itens(self, inventario_id: int):
        return self.repository.listar_itens_por_inventario(inventario_id)
    
    def deletar_inventario(self, inventario_id: int):
        self.repository.deletar(inventario_id)        
        
    def remover_item(self, item_id: int):
        self.repository.remover_item(item_id)