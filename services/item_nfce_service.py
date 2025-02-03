# services/item_nfce_service.py
from repositories.item_nfce_repository import ItemNFCeRepository
from models.item_nfce import ItemNFCe

class ItemNFCeService:
    def __init__(self):
        self.repository = ItemNFCeRepository()

    def listar_itens_por_nfce(self, nfce_id: int) -> list[ItemNFCe]:
        return self.repository.listar_por_nfce(nfce_id)

    def criar_item(self, item_data: dict) -> ItemNFCe:
        item = ItemNFCe(
            nfce_id=item_data['nfce_id'],
            codigo_produto_fornecedor=item_data.get('codigo_produto_fornecedor'),
            produto=item_data.get('produto'),
            descricao=item_data['descricao'],
            quantidade=item_data['quantidade'],
            unidade_medida=item_data['unidade_medida'],
            quantidade_por_grade=item_data.get('quantidade_por_grade'),
            valor=item_data['valor']
        )
        return self.repository.criar(item)

    def atualizar_item(self, item_id: int, item_data: dict) -> ItemNFCe:
        item = self.repository.buscar_por_id(item_id)
        if not item:
            raise ValueError("Item não encontrado")
        
        for key, value in item_data.items():
            setattr(item, key, value)
        
        return self.repository.atualizar(item)

    def deletar_item(self, item_id: int) -> None:
        self.repository.deletar(item_id)

    def buscar_item_por_id(self, item_id: int) -> ItemNFCe:
        item = self.repository.buscar_por_id(item_id)
        if not item:
            raise ValueError("Item não encontrado")
        return item