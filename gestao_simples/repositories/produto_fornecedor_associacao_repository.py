# repositories/produto_fornecedor_associacao_repository.py
from repositories.base_repository import BaseRepository
from models.produto_fornecedor_associacao import ProdutoFornecedorAssociacao
from config.database import SessionLocal
from sqlalchemy.orm import joinedload

class ProdutoFornecedorAssociacaoRepository(BaseRepository):
    def __init__(self):
        super().__init__(ProdutoFornecedorAssociacao)

    def listar(self):
        with SessionLocal() as session:
            return session.query(ProdutoFornecedorAssociacao).options(
                joinedload(ProdutoFornecedorAssociacao.produto),
                joinedload(ProdutoFornecedorAssociacao.fornecedor)
                ).all()

    def buscar_por_criterios(self, fornecedor_id, codigo, descricao):
        with SessionLocal() as session:
            return session.query(ProdutoFornecedorAssociacao).filter(
                ProdutoFornecedorAssociacao.fornecedor_id == fornecedor_id,
                ProdutoFornecedorAssociacao.codigo_produto_fornecedor == codigo,
                ProdutoFornecedorAssociacao.descricao_produto_fornecedor == descricao
            ).first()

    def listar_nao_associados(self, fornecedor_id):
        # Implemente conforme a lógica de negócio
        pass