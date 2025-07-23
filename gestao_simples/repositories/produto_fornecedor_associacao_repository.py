# repositories/produto_fornecedor_associacao_repository.py
from repositories.base_repository import BaseRepository
from models.produto_fornecedor_associacao import ProdutoFornecedorAssociacao
from config.database import SessionLocal
from sqlalchemy.orm import joinedload
from sqlalchemy import text
from typing import List
from utils.logger import logger
import time

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

    def criar_lote(self, associacoes: List[ProdutoFornecedorAssociacao]) -> int:
        """
        Cria múltiplas associações em lote usando bulk_insert_mappings para máxima performance
        """
        try:
            inicio = time.time()
            
            with SessionLocal() as session:
                # Converte objetos para dicionários
                dados_lote = []
                for associacao in associacoes:
                    dados_lote.append({
                        'produto_id': associacao.produto_id,
                        'fornecedor_id': associacao.fornecedor_id,
                        'quantidade_por_grade': associacao.quantidade_por_grade,
                        'codigo_produto_fornecedor': associacao.codigo_produto_fornecedor,
                        'descricao_produto_fornecedor': associacao.descricao_produto_fornecedor,
                        'data_criacao': associacao.data_criacao if hasattr(associacao, 'data_criacao') else None,
                        'data_atualizacao': associacao.data_atualizacao if hasattr(associacao, 'data_atualizacao') else None
                    })
                
                # Usa bulk_insert_mappings para inserção eficiente
                session.bulk_insert_mappings(ProdutoFornecedorAssociacao, dados_lote)
                session.commit()
                
                duracao = time.time() - inicio
                logger.info(f"Lote de {len(associacoes)} associações criado em {duracao:.3f}s")
                
                return len(associacoes)
                
        except Exception as e:
            logger.error(f"Erro na criação em lote: {str(e)}")
            session.rollback()
            raise

    def atualizar_lote(self, updates: List[dict]) -> int:
        """
        Atualiza múltiplas associações em lote
        """
        try:
            inicio = time.time()
            
            with SessionLocal() as session:
                session.bulk_update_mappings(ProdutoFornecedorAssociacao, updates)
                session.commit()
                
                duracao = time.time() - inicio
                logger.info(f"Lote de {len(updates)} associações atualizado em {duracao:.3f}s")
                
                return len(updates)
                
        except Exception as e:
            logger.error(f"Erro na atualização em lote: {str(e)}")
            session.rollback()
            raise

    def deletar_lote(self, ids: List[int]) -> int:
        """
        Deleta múltiplas associações em lote
        """
        try:
            inicio = time.time()
            
            with SessionLocal() as session:
                session.query(ProdutoFornecedorAssociacao).filter(
                    ProdutoFornecedorAssociacao.id.in_(ids)
                ).delete(synchronize_session=False)
                session.commit()
                
                duracao = time.time() - inicio
                logger.info(f"Lote de {len(ids)} associações deletado em {duracao:.3f}s")
                
                return len(ids)
                
        except Exception as e:
            logger.error(f"Erro na deleção em lote: {str(e)}")
            session.rollback()
            raise

    def listar_com_paginacao(self, pagina: int = 1, itens_por_pagina: int = 50):
        """
        Lista associações com paginação para melhor performance em grandes volumes
        """
        try:
            with SessionLocal() as session:
                offset = (pagina - 1) * itens_por_pagina
                
                query = session.query(ProdutoFornecedorAssociacao).options(
                    joinedload(ProdutoFornecedorAssociacao.produto),
                    joinedload(ProdutoFornecedorAssociacao.fornecedor)
                )
                
                total = query.count()
                associacoes = query.offset(offset).limit(itens_por_pagina).all()
                
                return {
                    'associacoes': associacoes,
                    'total': total,
                    'pagina': pagina,
                    'itens_por_pagina': itens_por_pagina,
                    'total_paginas': (total + itens_por_pagina - 1) // itens_por_pagina
                }
                
        except Exception as e:
            logger.error(f"Erro na listagem paginada: {str(e)}")
            raise

    def buscar_associacoes_por_fornecedor_lote(self, fornecedor_ids: List[int]):
        """
        Busca associações para múltiplos fornecedores de uma vez
        """
        try:
            with SessionLocal() as session:
                return session.query(ProdutoFornecedorAssociacao).options(
                    joinedload(ProdutoFornecedorAssociacao.produto),
                    joinedload(ProdutoFornecedorAssociacao.fornecedor)
                ).filter(
                    ProdutoFornecedorAssociacao.fornecedor_id.in_(fornecedor_ids)
                ).all()
                
        except Exception as e:
            logger.error(f"Erro na busca por fornecedores em lote: {str(e)}")
            raise

    def obter_estatisticas_raw(self) -> dict:
        """
        Obtém estatísticas usando SQL bruto para máxima performance
        """
        try:
            with SessionLocal() as session:
                query = text("""
                    SELECT 
                        COUNT(*) as total_associacoes,
                        COUNT(DISTINCT fornecedor_id) as fornecedores_unicos,
                        COUNT(DISTINCT produto_id) as produtos_unicos,
                        AVG(quantidade_por_grade) as media_quantidade,
                        MIN(quantidade_por_grade) as min_quantidade,
                        MAX(quantidade_por_grade) as max_quantidade
                    FROM produto_fornecedor_associacao
                """)
                
                resultado = session.execute(query).fetchone()
                
                return {
                    'total_associacoes': resultado.total_associacoes or 0,
                    'fornecedores_unicos': resultado.fornecedores_unicos or 0,
                    'produtos_unicos': resultado.produtos_unicos or 0,
                    'media_quantidade': float(resultado.media_quantidade or 0),
                    'min_quantidade': float(resultado.min_quantidade or 0),
                    'max_quantidade': float(resultado.max_quantidade or 0)
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {}

    def verificar_duplicatas(self, fornecedor_id: int, codigo: str, descricao: str) -> bool:
        """
        Verifica se já existe uma associação com os mesmos critérios
        """
        try:
            with SessionLocal() as session:
                existe = session.query(ProdutoFornecedorAssociacao).filter(
                    ProdutoFornecedorAssociacao.fornecedor_id == fornecedor_id,
                    ProdutoFornecedorAssociacao.codigo_produto_fornecedor == codigo,
                    ProdutoFornecedorAssociacao.descricao_produto_fornecedor == descricao
                ).first() is not None
                
                return existe
                
        except Exception as e:
            logger.error(f"Erro ao verificar duplicatas: {str(e)}")
            return False