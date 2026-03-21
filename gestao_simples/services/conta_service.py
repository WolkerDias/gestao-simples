# services/conta_service.py
from repositories.conta_repository import ContaRepository
#from utils.validacoes import validar_conta
from utils.message_handler import message_handler, MessageType
from utils.logger import logger

class ContaService:
    def __init__(self):
        self.repository = ContaRepository()
    
    def criar_conta(self, dados_conta: dict):
        """Cria uma nova conta com validações"""
        try:
            # Valida os dados da conta
            #validar_conta(dados_conta)
            
            # Verifica se já existe conta com o mesmo nome
            conta_existente = self.repository.buscar_por_nome(dados_conta['nome'])
            if conta_existente:
                message_handler.add_message(
                    MessageType.ERROR,
                    f"Já existe uma conta com o nome '{dados_conta['nome']}'"
                )
                raise ValueError(f"Conta '{dados_conta['nome']}' já existe")
            
            # Cria a conta
            conta = self.repository.criar(dados_conta)
            
            message_handler.add_message(
                MessageType.SUCCESS,
                f"Conta '{conta.nome}' cadastrada com sucesso!"
            )
            
            return conta
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro no serviço de criação de conta: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao criar conta. Tente novamente."
            )
            raise
    
    def listar_contas(self):
        """Lista todas as contas"""
        try:
            contas = self.repository.listar()
            logger.info(f"Listadas {len(contas)} contas")
            return contas
        except Exception as e:
            logger.error(f"Erro ao listar contas: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao carregar lista de contas."
            )
            raise
    
    def buscar_conta_por_id(self, conta_id: int):
        """Busca conta por ID"""
        try:
            conta = self.repository.buscar_por_id(conta_id)
            if not conta:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Conta não encontrada."
                )
            return conta
        except Exception as e:
            logger.error(f"Erro ao buscar conta: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao buscar conta."
            )
            raise
    
    def buscar_conta_por_nome(self, nome: str):
        """Busca conta por nome"""
        try:
            conta = self.repository.buscar_por_nome(nome)
            return conta
        except Exception as e:
            logger.error(f"Erro ao buscar conta por nome: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao buscar conta por nome."
            )
            raise
    
    def listar_contas_por_tipo(self, tipo: str):
        """Lista contas por tipo"""
        try:
            contas = self.repository.listar_por_tipo(tipo)
            logger.info(f"Listadas {len(contas)} contas do tipo '{tipo}'")
            return contas
        except Exception as e:
            logger.error(f"Erro ao listar contas por tipo: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao carregar contas por tipo."
            )
            raise
    
    def atualizar_conta(self, conta_id: int, dados_atualizacao: dict):
        """Atualiza uma conta existente"""
        try:
            # Valida os dados de atualização
            validar_conta(dados_atualizacao, atualizacao=True)
            
            # Verifica se o novo nome já existe (se o nome foi alterado)
            if 'nome' in dados_atualizacao:
                conta_atual = self.repository.buscar_por_id(conta_id)
                if conta_atual and conta_atual.nome != dados_atualizacao['nome']:
                    conta_existente = self.repository.buscar_por_nome(dados_atualizacao['nome'])
                    if conta_existente:
                        message_handler.add_message(
                            MessageType.ERROR,
                            f"Já existe uma conta com o nome '{dados_atualizacao['nome']}'"
                        )
                        raise ValueError(f"Conta '{dados_atualizacao['nome']}' já existe")
            
            conta = self.repository.atualizar(conta_id, dados_atualizacao)
            
            if conta:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    "Conta atualizada com sucesso!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Conta não encontrada para atualização."
                )
            
            return conta
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar conta: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao atualizar conta."
            )
            raise
    
    def deletar_conta(self, conta_id: int):
        """Remove uma conta"""
        try:
            # Verifica se existem receitas ou despesas vinculadas à conta
            conta = self.repository.buscar_por_id(conta_id)
            if conta and (conta.receitas or conta.despesas):
                message_handler.add_message(
                    MessageType.ERROR,
                    "Não é possível remover conta que possui receitas ou despesas vinculadas."
                )
                raise ValueError("Conta possui transações vinculadas")
            
            sucesso = self.repository.deletar(conta_id)
            
            if sucesso:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    "Conta removida com sucesso!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Conta não encontrada para remoção."
                )
            
            return sucesso
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro ao deletar conta: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao remover conta."
            )
            raise
    
    def obter_saldo_atual(self, conta_id: int):
        """Obtém o saldo atual da conta"""
        try:
            saldo = self.repository.calcular_saldo_atual(conta_id)
            return saldo
        except Exception as e:
            logger.error(f"Erro ao obter saldo da conta: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao calcular saldo da conta."
            )
            raise
    
    def listar_contas_com_saldo(self):
        """Lista todas as contas com seus respectivos saldos atuais"""
        try:
            contas = self.repository.listar()
            contas_com_saldo = []
            
            for conta in contas:
                saldo_atual = self.repository.calcular_saldo_atual(conta.id)
                conta_info = {
                    'id': conta.id,
                    'nome': conta.nome,
                    'tipo': conta.tipo,
                    'saldo_inicial': float(conta.saldo_inicial or 0.0),
                    'saldo_atual': saldo_atual
                }
                contas_com_saldo.append(conta_info)
            
            return contas_com_saldo
        except Exception as e:
            logger.error(f"Erro ao listar contas com saldo: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao carregar contas com saldos."
            )
            raise