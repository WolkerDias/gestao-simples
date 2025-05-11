# services/nota_entrada_service.py
from repositories.nota_entrada_repository import NotaEntradaRepository
from utils.validacoes import validar_nota_entrada,validar_item_nota_entrada, ValidationError
from utils.logger import logger
from utils.message_handler import message_handler, MessageType
from config.database import SessionLocal
from services.item_nota_entrada_service import ItemNotaEntradaService
from models.item_nota_entrada import ItemNotaEntrada
from sqlalchemy.exc import IntegrityError



class NotaEntradaService:
    def __init__(self):
        self.repository = NotaEntradaRepository()
        self.item_service = ItemNotaEntradaService()        

    def criar_nota_entrada_atomica(self, nota_entrada_data, itens_data):
        session = SessionLocal()
        try:
            session.begin()
            
            # Verificar se a chave de acesso já existe
            if nota_entrada_data.chave_acesso:
                if self.repository.buscar_por_chave_acesso(nota_entrada_data.chave_acesso, session=session):
                    raise ValidationError("Chave de acesso já cadastrada.")
            
            # Criar NotaEntrada
            nota_entrada = self.repository.criar(nota_entrada_data, session=session)
            
            # Forçar o flush para gerar o ID da NotaEntrada
            session.flush()
            
            # Criar Itens
            for item_data in itens_data:
                item_data['nota_entrada_id'] = nota_entrada.id
                novo_item = ItemNotaEntrada(**item_data)
                self.item_service.criar_item(novo_item, session=session)
            
            session.commit()
            # Se chegou aqui, deu sucesso
            message_handler.add_message(
                MessageType.SUCCESS,
                f"NotaEntrada {nota_entrada.id} cadastrada com sucesso!"
            )
            return nota_entrada
        except ValidationError as e:
            session.rollback()
            raise
        except IntegrityError as e:
            session.rollback()
            if "Duplicate entry" in str(e.orig):
                raise ValidationError("Chave de acesso já existe. Utilize uma chave única.")
            raise
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def atualizar_nota_entrada_atomica(self, nota_entrada, itens_data, ids_para_excluir=None):
        session = SessionLocal()
        try:
            # Inicia a transação explicitamente
            session.begin()
            
            # Atualiza NotaEntrada usando merge para anexar ao contexto da sessão
            nota_entrada_atualizada = session.merge(nota_entrada)
            
            # Exclui itens removidos
            if ids_para_excluir:
                for item_id in ids_para_excluir:
                    item = session.query(ItemNotaEntrada).get(item_id)
                    if item:
                        session.delete(item)
            
            # Processa atualizações e novos itens
            for item_data in itens_data:
                if item_data['id']:  # Item existente
                    item = session.query(ItemNotaEntrada).get(item_data['id'])
                    for key, value in item_data.items():
                        if key not in ['id', '_sa_instance_state']:
                            setattr(item, key, value)
                else:  # Novo item
                    novo_item = ItemNotaEntrada(**item_data)
                    session.add(novo_item)
            
            # Confirma TODAS as operações de uma vez
            session.commit()
            success_msg = f"NotaEntrada atualizada com sucesso"
            logger.info(success_msg)
            message_handler.add_message(
                MessageType.SUCCESS,
                success_msg
            )
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()  # Garante o fechamento da sessão
        
    def criar_nota_entrada(self, dados):
        try:
            nota_entrada = self.repository.criar(dados)
            success_msg = f"NotaEntrada cadastrado com sucesso"
            logger.info(success_msg)
            message_handler.add_message(
                MessageType.SUCCESS,
                success_msg
            )
            return nota_entrada
        except ValidationError as e:
            logger.error(f"Erro de validação ao criar NotaEntrada: {e.errors}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar NotaEntrada: {str(e)}")
            raise Exception(f"Erro ao criar NotaEntrada: {str(e)}")
        
    def listar_notas_entrada(self):
        return self.repository.listar()
    
    def buscar_nota_entrada_por_id(self, id):
        return self.repository.buscar_por_id(id)
    
    def atualizar_nota_entrada(self, dados):
        return self.repository.atualizar(dados)
    
    def deletar_nota_entrada(self, id):
        return self.repository.deletar(id)
    
    def listar_itens_unicos_por_fornecedor(self, fornecedor_id: int)-> list:
        session = SessionLocal()
        try:
            # Usa o repositório para buscar NotaEntradas ordenadas
            notas_entrada = self.repository.listar_por_fornecedor_ordenado(fornecedor_id, session=session)
            
            itens_unicos = {}
            for nota_entrada in notas_entrada:
                for item in nota_entrada.itens:
                    if item.codigo_produto_fornecedor:
                        # Chave composta para garantir unicidade
                        key = (
                            item.codigo_produto_fornecedor,
                            item.unidade_medida,
                            item.descricao
                        )
                        if key not in itens_unicos:
                            itens_unicos[key] = {
                                'codigo': item.codigo_produto_fornecedor,
                                'descricao': item.descricao,
                                'unidade': item.unidade_medida,
                                'valor': item.valor,
                                'data_emissao': nota_entrada.data_emissao
                            }
                            
            # Ordena os itens por descrição
            itens_ordenados = sorted(
                itens_unicos.values(), 
                key=lambda x: x['descricao'].lower()  # Ordenação case-insensitive
            )
            
            return itens_ordenados
        finally:
            session.close()