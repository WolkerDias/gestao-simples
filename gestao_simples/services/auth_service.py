# services/auth_service.py
import jwt
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional
from utils.validacoes import ValidationError
from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS, DEFAULT_PASSWORD, DEFAULT_USER_EMAIL
from utils.logger import logger

class AuthService:
    def __init__(self):
        self.usuario_repo = UsuarioRepository()
    
    def criar_token(self, usuario: Usuario) -> str:
        payload = {
            "sub": str(usuario.id),
            "email": usuario.email,
            "is_admin": usuario.is_admin,
            "exp": datetime.now(tz=ZoneInfo('UTC')) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def verificar_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.error("Token expirado")
            raise
        except jwt.InvalidTokenError:
            logger.error("Token inválido")
            raise

    def autenticar(self, email: str, senha: str) -> Usuario:
        usuario = self.usuario_repo.buscar_por_email(email)
        if not usuario or not usuario.verificar_senha(senha):
            raise ValueError("Credenciais inválidas")
        if not usuario.ativo:
            raise ValueError("Usuário desativado")
        return usuario

    def criar_admin_inicial(self):
        try:
            if not self.usuario_repo.buscar_por_email(DEFAULT_USER_EMAIL):
                admin = Usuario(
                    nome="Admin",
                    email=DEFAULT_USER_EMAIL,
                    is_admin=True
                )
                admin.senha = DEFAULT_PASSWORD  # Usa o setter para gerar o hash
                self.usuario_repo.criar(admin)
                logger.info("Admin inicial criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar admin: {str(e)}")
            raise

    def criar_usuario(self, dados):
        try:
            usuario = self.usuario_repo.criar(dados)
            logger.info(f"Usuário {usuario.nome} criado com sucesso")
            return usuario
        except ValidationError as e:
            logger.error(f"Erro de validação ao criar usuário: {e.errors}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {str(e)}")
            raise Exception(f"Erro ao criar usuário: {str(e)}")
    
    def listar_usuarios(self):
        try:
            usuarios = self.usuario_repo.listar()
            if not usuarios:
                raise ValueError("Nenhum usuário encontrado")
            return usuarios
        except Exception as e:
            logger.error(f"Erro ao listar usuários: {str(e)}")
            raise Exception(f"Erro ao listar usuários: {str(e)}")
        
    def buscar_usuario_por_id(self, usuario_id: int) -> Usuario:
        try:
            usuario = self.usuario_repo.buscar_por_id(usuario_id)
            if not usuario:
                raise ValueError("Usuário não encontrado")
            return usuario
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {str(e)}")
            raise Exception(f"Erro ao buscar usuário: {str(e)}")
        
    def atualizar_usuario(self, usuario: Usuario):
        try:
            usuario_atualizado = self.usuario_repo.atualizar(usuario)
            logger.info(f"Usuário {usuario.nome} atualizado com sucesso")
            return usuario_atualizado
        except ValidationError as e:
            logger.error(f"Erro de validação ao atualizar usuário: {e.errors}")
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar usuário: {str(e)}")
            raise Exception(f"Erro ao atualizar usuário: {str(e)}")
        
    def deletar_usuario(self, usuario_id: int):
        try:
            self.usuario_repo.deletar(usuario_id)
        except Exception as e:
            logger.error(f"Erro ao deletar usuário: {str(e)}")
            raise Exception(f"Erro ao deletar usuário: {str(e)}")
        
    def atualizar_senha(self, usuario: Usuario, nova_senha: str):
        try:
            usuario.senha = nova_senha
            self.usuario_repo.atualizar(usuario)
            logger.info(f"Senha do usuário {usuario.nome} atualizada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao atualizar senha: {str(e)}")
            raise Exception(f"Erro ao atualizar senha: {str(e)}")