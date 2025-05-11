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
    
    if errors:
        # Log todos os erros
        for error in errors:
            logger.error(f"Erro de validação do produto: {error}")
        # Levanta exceção com todos os erros
        raise ValidationError("Erro na validação do produto", errors)
    
def validar_nota_entrada(nota_entrada):
    errors = []
    
    if not nota_entrada.fornecedor_id:
        errors.append("Fornecedor é obrigatório")

    if nota_entrada.numero_nota_entrada:
        if int(nota_entrada.numero_nota_entrada) > 999999999:
            errors.append("O valor máximo permitido para o Número da Nota de entrada é 999.999.999")
    
#    if not nota_entrada.chave_acesso:
#        errors.append("Chave de acesso é obrigatória")
#    elif len(nota_entrada.chave_acesso) != 44:
#        errors.append("Chave de acesso deve ter 44 caracteres")
        
    if not nota_entrada.data_emissao:
        errors.append("Data de emissão é obrigatória")
        
    if errors:
        raise ValidationError("Erro na validação da Nota de entrada", errors)

def validar_item_nota_entrada(item):
    """
    Valida os dados de um item da Nota de entrada.
    Raises:
        ValidationError: Se houver erros de validação.
    """
    errors = []
    
    if not item.descricao:
        errors.append("Descrição do item é obrigatória")
        
    if not item.quantidade or item.quantidade <= 0:
        errors.append("Quantidade deve ser maior que zero")
        
    if not item.valor or item.valor <= 0:
        errors.append("Valor deve ser maior que zero")
        
    if not item.unidade_medida:
        errors.append("Unidade de medida é obrigatória")
        
    if errors:
        raise ValidationError("Erro na validação do item", errors)

def validar_quantidade_positiva(quantidade: float):
    """
    Valida se a quantidade é um valor positivo.
    
    Args:
        quantidade (float): Valor a ser validado.
        
    Raises:
        ValidationError: Se a quantidade for menor ou igual a zero.
    """
    if quantidade <= 0:
        error_msg = "Quantidade deve ser maior que zero"
        logger.error(f"Erro de validação: {error_msg}")
        raise ValidationError(error_msg)
    
def validar_formato_referencia(referencia: str):
    """
    Valida se a referência está no formato MM/AAAA.
    Exemplo: "04/2025"
    """    
    # Verifica comprimento, quantidade de barras e posição
    if (len(referencia) != 7 
        or referencia.count('/') != 1 
        or referencia[2] != '/'):
        raise ValidationError("Formato de referência inválido. Use MM/AAAA.")
    else:
        mes, ano = referencia.split('/')
        if not mes.isdigit() or not ano.isdigit():
            raise ValidationError("Mês e ano em referência devem ser números.")
        else:
            mes_num = int(mes)
            if mes_num < 1 or mes_num > 12:
                raise ValidationError("Mês em referência deve em estar entre 01 e 12.")