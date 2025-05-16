# services/produto_fornecedor_associacao_service.py
from repositories.produto_fornecedor_associacao_repository import ProdutoFornecedorAssociacaoRepository
from models.produto_fornecedor_associacao import ProdutoFornecedorAssociacao 
from services.nota_entrada_service import NotaEntradaService
from services.fornecedor_service import FornecedorService
from utils.logger import logger
import time

class ProdutoFornecedorAssociacaoService:
    def __init__(self):
        self.repository = ProdutoFornecedorAssociacaoRepository()
        self.nota_entrada_service = NotaEntradaService()

    def criar_associacao(self, dados: dict):
        try:
            # Cria uma instância da model com os dados
            associacao = ProdutoFornecedorAssociacao(
                produto_id=dados['produto_id'],
                fornecedor_id=dados['fornecedor_id'],
                quantidade_por_grade=dados['quantidade_por_grade'],
                codigo_produto_fornecedor=dados['codigo_produto_fornecedor'],
                descricao_produto_fornecedor=dados['descricao_produto_fornecedor']
            )
            
            # Salva via repository
            return self.repository.criar(associacao)
            
        except Exception as e:
            logger.error(f"Erro ao criar associação: {str(e)}")
            raise        

    def listar_associacoes(self):
        return self.repository.listar()

    def buscar_associacao_por_id(self, associacao_id: int):
        return self.repository.buscar_por_id(associacao_id)

    def atualizar_associacao(self, associacao_id: int, dados: dict):
        associacao = self.repository.buscar_por_id(associacao_id)
        for key, value in dados.items():
            setattr(associacao, key, value)
        self.repository.atualizar(associacao)
        return associacao

    def deletar_associacao(self, associacao_id: int):
        self.repository.deletar(associacao_id)        

    def listar_todos_itens_nao_associados(self):
        inicio = time.time()
        todos_fornecedores = self._get_fornecedores_com_itens()

        # Carrega todas as associações existentes de uma vez
        todas_associacoes = self.repository.listar()

        associacoes_index = {
            (a.fornecedor_id, a.codigo_produto_fornecedor, a.descricao_produto_fornecedor): True
            for a in todas_associacoes
        }
                
        itens_nao_associados = []
        
        for fornecedor in todos_fornecedores:
            itens_fornecedor = self.nota_entrada_service.listar_itens_unicos_por_fornecedor(fornecedor.id)

            for item in itens_fornecedor:
                chave = (fornecedor.id, item['codigo'], item['descricao'])
                if chave not in associacoes_index:
                    itens_nao_associados.append({
                        "fornecedor_id": fornecedor.id,
                        "fornecedor_nome": fornecedor.nome,
                        "codigo_produto_fornecedor": item['codigo'],
                        "descricao": item['descricao'],
                        "unidade": item['unidade']
                    })
                
        logger.info(f"Itens não associados encontrados: {len(itens_nao_associados)} - Duração da busca: {time.time() - inicio:.2f}s")
        return itens_nao_associados

    def _get_fornecedores_com_itens(self):
        # Implemente conforme seu modelo de dados
        return FornecedorService().listar_fornecedores()