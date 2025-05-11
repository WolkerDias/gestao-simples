# repositories/inventario_estoque_repository.py
from models.inventario_estoque import InventarioEstoque
from models.item_inventario import ItemInventario
from config.database import SessionLocal
from repositories.base_repository import BaseRepository
from sqlalchemy.orm import joinedload
from datetime import datetime

class InventarioEstoqueRepository(BaseRepository):
    def __init__(self):
        super().__init__(InventarioEstoque)

    def adicionar_item(self, inventario_id: int, produto_id: int, quantidade: float):
        item = ItemInventario(
            inventario_id=inventario_id,
            produto_id=produto_id,
            quantidade_contada=quantidade
        )
        with SessionLocal() as session:
            session.add(item)
            session.commit()
            return item
        
    def atualizar(self, inventario_id: int, dados):
        with SessionLocal() as session:
            inventario = session.query(InventarioEstoque).get(inventario_id)
            if not inventario:
                raise Exception("Inventário não encontrado")
            
            inventario.referencia = dados.referencia
            inventario.data_inicio_contagem = dados.data_inicio_contagem
            inventario.observacoes = dados.observacoes
            session.commit()
            return inventario        
        
    def encerrar_contagem(self, inventario_id: int, data_fim: datetime):
        with SessionLocal() as session:
            inventario = session.query(InventarioEstoque).get(inventario_id)
            
            if not inventario:
                raise Exception("Inventário não encontrado")
                
            inventario.data_fim_contagem = data_fim
            session.commit()
            return inventario        

    def listar_itens_por_inventario(self, inventario_id: int):
        with SessionLocal() as session:
            return (
                session.query(ItemInventario)
                .options(joinedload(ItemInventario.produto))  # Carrega o relacionamento
                .filter(ItemInventario.inventario_id == inventario_id)
                .all()
            )

    def buscar_por_referencia(self, referencia: str):
        with SessionLocal() as session:
            return (
                session.query(InventarioEstoque)
                .filter(InventarioEstoque.referencia == referencia)
                .first()
                )

    def listar(self):
        with SessionLocal() as session:
            return (
                session.query(InventarioEstoque)
                .options(joinedload(InventarioEstoque.itens))  # Carrega os itens junto
                .all()
            )
        
    def remover_item(self, item_id: int):
        with SessionLocal() as session:
            item = session.query(ItemInventario).get(item_id)
            if item:
                session.delete(item)
                session.commit()

    def buscar_por_id(self, inventario_id: int):
        with SessionLocal() as session:
            return (
                session.query(InventarioEstoque)
                .options(
                    joinedload(InventarioEstoque.itens)
                    .joinedload(ItemInventario.produto)  # Carrega os itens e seus produtos
                )
                .filter(InventarioEstoque.id == inventario_id)
                .first()
            )