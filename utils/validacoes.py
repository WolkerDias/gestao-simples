# utils/validacoes.py
from utils.logger import logger

class ValidationError(ValueError):
    """Erro customizado para validações que permite múltiplos erros"""
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []

def validar_fornecedor(fornecedor):
    """
    Valida os dados do fornecedor
    Raises:
        ValidationError: Se houver erros de validação
    """
    errors = []
    
    if not fornecedor.nome:
        errors.append("Nome do fornecedor é obrigatório")
    
    if not fornecedor.cnpj:
        errors.append("CNPJ é obrigatório")
    elif not fornecedor.cnpj.replace(".", "").replace("/", "").replace("-", "").isdigit():
        errors.append("CNPJ deve conter apenas números e caracteres especiais")
    
    if errors:
        # Log todos os erros
        for error in errors:
            logger.error(f"Erro de validação do fornecedor: {error}")
        # Levanta exceção com todos os erros
        raise ValidationError("Erro na validação do fornecedor", errors)

def validar_produto(produto):
    """
    Valida os dados do produto
    Raises:
        ValidationError: Se houver erros de validação
    """
    errors = []
    
    if not produto.nome:
        errors.append("Nome do produto é obrigatório")
    
    if produto.preco < 0:
        errors.append("Preço não pode ser negativo")
    
    if errors:
        # Log todos os erros
        for error in errors:
            logger.error(f"Erro de validação do produto: {error}")
        # Levanta exceção com todos os erros
        raise ValidationError("Erro na validação do produto", errors)