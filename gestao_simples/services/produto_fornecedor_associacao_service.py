# services/produto_fornecedor_associacao_service.py
from repositories.produto_fornecedor_associacao_repository import ProdutoFornecedorAssociacaoRepository
from models.produto_fornecedor_associacao import ProdutoFornecedorAssociacao 
from services.nota_entrada_service import NotaEntradaService
from services.fornecedor_service import FornecedorService
from utils.logger import logger
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

class ProdutoFornecedorAssociacaoService:
    def __init__(self):
        self.repository = ProdutoFornecedorAssociacaoRepository()
        self.nota_entrada_service = NotaEntradaService()
        # Cache interno para otimização
        self._cache_associacoes = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutos

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
            resultado = self.repository.criar(associacao)
            
            # Invalida cache após criação
            self._invalidar_cache()
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao criar associação: {str(e)}")
            raise

    def criar_associacoes_lote(self, lista_dados: List[dict]) -> Dict[str, any]:
        """
        Cria múltiplas associações em lote para melhor performance
        """
        try:
            inicio = time.time()
            sucessos = 0
            erros = []
            
            # Processa em lotes de 50 para não sobrecarregar o banco
            tamanho_lote = 50
            
            for i in range(0, len(lista_dados), tamanho_lote):
                lote = lista_dados[i:i + tamanho_lote]
                
                try:
                    # Cria instâncias das models
                    associacoes = []
                    for dados in lote:
                        associacao = ProdutoFornecedorAssociacao(
                            produto_id=dados['produto_id'],
                            fornecedor_id=dados['fornecedor_id'],
                            quantidade_por_grade=dados['quantidade_por_grade'],
                            codigo_produto_fornecedor=dados['codigo_produto_fornecedor'],
                            descricao_produto_fornecedor=dados['descricao_produto_fornecedor']
                        )
                        associacoes.append(associacao)
                    
                    # Salva lote via repository (método bulk_create deve ser implementado)
                    if hasattr(self.repository, 'criar_lote'):
                        self.repository.criar_lote(associacoes)
                    else:
                        # Fallback: criação individual
                        for associacao in associacoes:
                            self.repository.criar(associacao)
                    
                    sucessos += len(lote)
                    
                except Exception as e:
                    erro_msg = f"Erro no lote {i//tamanho_lote + 1}: {str(e)}"
                    erros.append(erro_msg)
                    logger.error(erro_msg)
            
            # Invalida cache após operações em lote
            self._invalidar_cache()
            
            duracao = time.time() - inicio
            resultado = {
                'sucessos': sucessos,
                'erros': erros,
                'duracao': duracao,
                'total_processado': len(lista_dados)
            }
            
            logger.info(f"Criação em lote concluída: {sucessos} sucessos, {len(erros)} erros em {duracao:.2f}s")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na criação em lote: {str(e)}")
            raise

    def listar_associacoes(self, usar_cache: bool = True):
        """Lista associações com opção de cache"""
        if usar_cache and self._cache_valido():
            return self._cache_associacoes
            
        associacoes = self.repository.listar()
        
        if usar_cache:
            self._atualizar_cache(associacoes)
            
        return associacoes

    def buscar_associacao_por_id(self, associacao_id: int):
        return self.repository.buscar_por_id(associacao_id)

    def atualizar_associacao(self, associacao_id: int, dados: dict):
        associacao = self.repository.buscar_por_id(associacao_id)
        for key, value in dados.items():
            setattr(associacao, key, value)
        
        resultado = self.repository.atualizar(associacao)
        self._invalidar_cache()
        return resultado

    def deletar_associacao(self, associacao_id: int):
        self.repository.deletar(associacao_id)
        self._invalidar_cache()

    def listar_todos_itens_nao_associados(self, usar_processamento_paralelo: bool = True):
        """
        Lista itens não associados com opção de processamento paralelo
        """
        try:
            inicio = time.time()
            todos_fornecedores = self._get_fornecedores_com_itens()

            # Carrega todas as associações existentes de uma vez
            todas_associacoes = self.listar_associacoes(usar_cache=True)

            associacoes_index = {
                (a.fornecedor_id, a.codigo_produto_fornecedor, a.descricao_produto_fornecedor): True
                for a in todas_associacoes
            }
            
            if usar_processamento_paralelo and len(todos_fornecedores) > 5:
                itens_nao_associados = self._processar_fornecedores_paralelo(
                    todos_fornecedores, 
                    associacoes_index
                )
            else:
                itens_nao_associados = self._processar_fornecedores_sequencial(
                    todos_fornecedores, 
                    associacoes_index
                )
            
            duracao = time.time() - inicio
            logger.info(f"Itens não associados encontrados: {len(itens_nao_associados)} - Duração: {duracao:.2f}s")
            return itens_nao_associados
            
        except Exception as e:
            logger.error(f"Erro ao listar itens não associados: {str(e)}")
            return []

    def _processar_fornecedores_paralelo(self, fornecedores: List, associacoes_index: Dict) -> List[Dict]:
        """Processa fornecedores em paralelo para melhor performance"""
        itens_nao_associados = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Cria futures para cada fornecedor
            futures = {
                executor.submit(self._processar_fornecedor, fornecedor, associacoes_index): fornecedor
                for fornecedor in fornecedores
            }
            
            # Coleta resultados conforme completam
            for future in as_completed(futures):
                try:
                    itens_fornecedor = future.result()
                    itens_nao_associados.extend(itens_fornecedor)
                except Exception as e:
                    fornecedor = futures[future]
                    logger.error(f"Erro ao processar fornecedor {fornecedor.id}: {str(e)}")
        
        return itens_nao_associados

    def _processar_fornecedores_sequencial(self, fornecedores: List, associacoes_index: Dict) -> List[Dict]:
        """Processa fornecedores sequencialmente (fallback)"""
        itens_nao_associados = []
        
        for fornecedor in fornecedores:
            try:
                itens_fornecedor = self._processar_fornecedor(fornecedor, associacoes_index)
                itens_nao_associados.extend(itens_fornecedor)
            except Exception as e:
                logger.error(f"Erro ao processar fornecedor {fornecedor.id}: {str(e)}")
        
        return itens_nao_associados

    def _processar_fornecedor(self, fornecedor, associacoes_index: Dict) -> List[Dict]:
        """Processa um fornecedor específico"""
        itens_fornecedor_nao_associados = []
        itens_fornecedor = self.nota_entrada_service.listar_itens_unicos_por_fornecedor(fornecedor.id)

        for item in itens_fornecedor:
            chave = (fornecedor.id, item['codigo'], item['descricao'])
            if chave not in associacoes_index:
                itens_fornecedor_nao_associados.append({
                    "fornecedor_id": fornecedor.id,
                    "fornecedor_nome": fornecedor.nome,
                    "codigo_produto_fornecedor": item['codigo'],
                    "descricao": item['descricao'],
                    "unidade": item['unidade']
                })
        
        return itens_fornecedor_nao_associados

    def _get_fornecedores_com_itens(self):
        """Obtém fornecedores que possuem itens"""
        return FornecedorService().listar_fornecedores()

    def _cache_valido(self) -> bool:
        """Verifica se o cache ainda está válido"""
        if self._cache_associacoes is None or self._cache_timestamp is None:
            return False
        
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def _atualizar_cache(self, associacoes):
        """Atualiza o cache interno"""
        self._cache_associacoes = associacoes
        self._cache_timestamp = time.time()

    def _invalidar_cache(self):
        """Invalida o cache interno"""
        self._cache_associacoes = None
        self._cache_timestamp = None

    def obter_estatisticas_associacoes(self) -> Dict:
        """Retorna estatísticas das associações"""
        try:
            associacoes = self.listar_associacoes()
            
            stats = {
                'total_associacoes': len(associacoes),
                'fornecedores_unicos': len(set(a.fornecedor_id for a in associacoes)),
                'produtos_unicos': len(set(a.produto_id for a in associacoes)),
                'media_quantidade_por_grade': sum(a.quantidade_por_grade for a in associacoes) / len(associacoes) if associacoes else 0,
                'cache_status': 'ativo' if self._cache_valido() else 'inativo'
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {}