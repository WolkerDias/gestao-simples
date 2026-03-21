# utils/validacoes.py
from utils.logger import logger
from datetime import date
from decimal import Decimal

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
        

def validar_receita(dados: dict, atualizacao: bool = False):
    """Valida os dados de uma receita"""
    erros = []
    
    # Validação da descrição
    if 'descricao' in dados:
        if not dados['descricao'] or not dados['descricao'].strip():
            erros.append("Descrição é obrigatória")
        elif len(dados['descricao'].strip()) > 200:
            erros.append("Descrição deve ter no máximo 200 caracteres")
    elif not atualizacao:
        erros.append("Descrição é obrigatória")
    
    # Validação do valor
    if 'valor' in dados:
        try:
            valor = Decimal(str(dados['valor']))
            if valor <= 0:
                erros.append("Valor deve ser maior que zero")
        except (ValueError, TypeError):
            erros.append("Valor deve ser um número válido")
    elif not atualizacao:
        erros.append("Valor é obrigatório")
    
    # Validação da data de recebimento
    if 'data_recebimento' in dados:
        if not isinstance(dados['data_recebimento'], date):
            try:
                # Tenta converter string para date se necessário
                if isinstance(dados['data_recebimento'], str):
                    dados['data_recebimento'] = date.fromisoformat(dados['data_recebimento'])
            except ValueError:
                erros.append("Data de recebimento deve estar no formato válido")
    elif not atualizacao:
        erros.append("Data de recebimento é obrigatória")
    
    # Validação da categoria
    if 'categoria_id' in dados:
        if not isinstance(dados['categoria_id'], int) or dados['categoria_id'] <= 0:
            erros.append("Categoria deve ser selecionada")
    elif not atualizacao:
        erros.append("Categoria é obrigatória")
    
    # Validação das observações (opcional)
    if 'observacoes' in dados and dados['observacoes']:
        if len(dados['observacoes']) > 1000:
            erros.append("Observações devem ter no máximo 1000 caracteres")
    
    if erros:
        raise ValueError(f"Dados inválidos: {'; '.join(erros)}")

def validar_despesa(dados: dict, atualizacao: bool = False):
    """Valida os dados de uma despesa"""
    erros = []
    
    # Validação da descrição
    if 'descricao' in dados:
        if not dados['descricao'] or not dados['descricao'].strip():
            erros.append("Descrição é obrigatória")
        elif len(dados['descricao'].strip()) > 200:
            erros.append("Descrição deve ter no máximo 200 caracteres")
    elif not atualizacao:
        erros.append("Descrição é obrigatória")
    
    # Validação do valor
    if 'valor' in dados:
        try:
            valor = Decimal(str(dados['valor']))
            if valor <= 0:
                erros.append("Valor deve ser maior que zero")
        except (ValueError, TypeError):
            erros.append("Valor deve ser um número válido")
    elif not atualizacao:
        erros.append("Valor é obrigatório")
    
    # Validação da data de vencimento
    if 'data_vencimento' in dados:
        if not isinstance(dados['data_vencimento'], date):
            try:
                # Tenta converter string para date se necessário
                if isinstance(dados['data_vencimento'], str):
                    dados['data_vencimento'] = date.fromisoformat(dados['data_vencimento'])
            except ValueError:
                erros.append("Data de vencimento deve estar no formato válido")
    elif not atualizacao:
        erros.append("Data de vencimento é obrigatória")
    
    # Validação da data de pagamento (opcional)
    if 'data_pagamento' in dados and dados['data_pagamento']:
        if not isinstance(dados['data_pagamento'], date):
            try:
                if isinstance(dados['data_pagamento'], str):
                    dados['data_pagamento'] = date.fromisoformat(dados['data_pagamento'])
            except ValueError:
                erros.append("Data de pagamento deve estar no formato válido")
    
    # Validação da categoria
    if 'categoria_id' in dados:
        if not isinstance(dados['categoria_id'], int) or dados['categoria_id'] <= 0:
            erros.append("Categoria deve ser selecionada")
    elif not atualizacao:
        erros.append("Categoria é obrigatória")
    
    # Validação das observações (opcional)
    if 'observacoes' in dados and dados['observacoes']:
        if len(dados['observacoes']) > 1000:
            erros.append("Observações devem ter no máximo 1000 caracteres")
    
    # Validação do status pago
    if 'paga' in dados and dados['paga'] and not dados.get('data_pagamento'):
        erros.append("Data de pagamento é obrigatória quando despesa está marcada como paga")
    
    if erros:
        raise ValueError(f"Dados inválidos: {'; '.join(erros)}")