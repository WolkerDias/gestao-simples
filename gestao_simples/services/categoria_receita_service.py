# services/categoria_receita_service.py
from repositories.categoria_receita_repository import CategoriaReceitaRepository
#from utils.validacoes import validar_categoria_receita
from utils.message_handler import message_handler, MessageType
from utils.logger import logger

class CategoriaReceitaService:
    def __init__(self):
        self.repository = CategoriaReceitaRepository()
    
    def criar_categoria(self, dados_categoria: dict):
        """Cria uma nova categoria de receita com validações"""
        try:
            # Valida os dados da categoria
            #validar_categoria_receita(dados_categoria)
            
            # Verifica se já existe categoria com o mesmo nome
            categoria_existente = self.repository.buscar_por_nome(dados_categoria['nome'])
            if categoria_existente:
                message_handler.add_message(
                    MessageType.ERROR,
                    f"Já existe uma categoria com o nome '{dados_categoria['nome']}'"
                )
                raise ValueError(f"Categoria '{dados_categoria['nome']}' já existe")
            
            # Cria a categoria
            categoria = self.repository.criar(dados_categoria)
            
            message_handler.add_message(
                MessageType.SUCCESS,
                f"Categoria '{categoria.nome}' cadastrada com sucesso!"
            )
            
            return categoria
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro no serviço de criação de categoria: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao criar categoria. Tente novamente."
            )
            raise
    
    def listar_categorias(self):
        """Lista todas as categorias de receita com contagem de receitas"""
        try:
            categorias = self.repository.listar()
            logger.info(f"Listadas {len(categorias)} categorias de receita")
            return categorias
        except Exception as e:
            logger.error(f"Erro ao listar categorias: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao carregar lista de categorias."
            )
            raise
    
    def buscar_categoria_por_id(self, categoria_id: int):
        """Busca categoria por ID"""
        try:
            categoria = self.repository.buscar_por_id(categoria_id)
            if not categoria:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Categoria não encontrada."
                )
            return categoria
        except Exception as e:
            logger.error(f"Erro ao buscar categoria: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao buscar categoria."
            )
            raise
    
    def buscar_categoria_por_nome(self, nome: str):
        """Busca categoria por nome"""
        try:
            categoria = self.repository.buscar_por_nome(nome)
            return categoria
        except Exception as e:
            logger.error(f"Erro ao buscar categoria por nome: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao buscar categoria por nome."
            )
            raise
    
    def atualizar_categoria(self, categoria_id: int, dados_atualizacao: dict):
        """Atualiza uma categoria existente"""
        try:
            # Valida os dados de atualização
            #validar_categoria_receita(dados_atualizacao, atualizacao=True)
            
            # Verifica se o novo nome já existe (se o nome foi alterado)
            if 'nome' in dados_atualizacao:
                categoria_atual = self.repository.buscar_por_id(categoria_id)
                if categoria_atual and categoria_atual.nome != dados_atualizacao['nome']:
                    categoria_existente = self.repository.buscar_por_nome(dados_atualizacao['nome'])
                    if categoria_existente:
                        message_handler.add_message(
                            MessageType.ERROR,
                            f"Já existe uma categoria com o nome '{dados_atualizacao['nome']}'"
                        )
                        raise ValueError(f"Categoria '{dados_atualizacao['nome']}' já existe")
            
            categoria = self.repository.atualizar(categoria_id, dados_atualizacao)
            
            if categoria:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    "Categoria atualizada com sucesso!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Categoria não encontrada para atualização."
                )
            
            return categoria
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar categoria: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao atualizar categoria."
            )
            raise
    
    def deletar_categoria(self, categoria_id: int):
        """Remove uma categoria"""
        try:
            # Verifica se existem receitas vinculadas à categoria
            count_receitas = self.repository.contar_receitas_por_categoria(categoria_id)
            
            if count_receitas > 0:
                message_handler.add_message(
                    MessageType.ERROR,
                    f"Não é possível remover categoria com {count_receitas} receita(s) vinculada(s)."
                )
                raise ValueError("Categoria possui receitas vinculadas")
            
            sucesso = self.repository.deletar(categoria_id)
            
            if sucesso:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    "Categoria removida com sucesso!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Categoria não encontrada para remoção."
                )
            
            return sucesso
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro ao deletar categoria: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao remover categoria."
            )
            raise