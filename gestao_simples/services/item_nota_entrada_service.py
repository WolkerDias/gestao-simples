# services/item_nota_entrada_service.py
from repositories.item_nota_entrada_repository import ItemNotaEntradaRepository
from models.item_nota_entrada import ItemNotaEntrada

class ItemNotaEntradaService:
    def __init__(self):
        self.repository = ItemNotaEntradaRepository()

    def listar_itens_por_nota_entrada(self, nota_entrada_id: int) -> list[ItemNotaEntrada]:
        return self.repository.listar_por_nota_entrada(nota_entrada_id)

    def criar_item(self, item: ItemNotaEntrada, session=None) -> ItemNotaEntrada:
        if session:
            return self.repository.criar(item, session=session)
        return self.repository.criar(item)

    def atualizar_item(self, item: ItemNotaEntrada, session=None) -> ItemNotaEntrada:
        if session:
            return self.repository.atualizar(item, session=session)
        return self.repository.atualizar(item)

    def deletar_item(self, item_id: int, session=None) -> None:
        if session:
            self.repository.deletar(item_id, session=session)
        else:
            self.repository.deletar(item_id)

    def buscar_item_por_id(self, item_id: int, session=None) -> ItemNotaEntrada:
        item = self.repository.buscar_por_id(item_id, session=session)
        if not item:
            raise ValueError("Item não encontrado")
        return item