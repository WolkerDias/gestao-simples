import locale
import datetime
import re
import unicodedata

# Função para formatar valores no padrão brasileiro de moeda (R$)
def format_brl(value: float) -> str:
    """
    Formata um valor numérico para o padrão de moeda brasileiro (R$).
    
    Parâmetros:
    value (float): Valor a ser formatado.
    
    Retorna:
    str: Valor formatado como moeda (R$).
    """
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Define o local para Brasil
    return locale.currency(value, grouping=True)  # Formata o valor como moeda com separador de milhar

def format_value_brl(value: float, decimals: int = 2) -> str:
    """
    Formata um valor numérico para o padrão brasileiro.
    
    Parâmetros:
    value (float): Valor a ser formatado.
    
    Retorna:
    str: Valor formatado com o número específico de casas decimais.
    """
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Define o local para Brasil
    return locale.format_string(f'%.{decimals}f', value, grouping=True)  # Formata o valor como moeda com separador de milhar


# Função para formatar valores como percentual
def format_percent(value: float, decimals: int = 2) -> str:
    """
    Formata um valor numérico como percentual.
    
    Parâmetros:
    value (float): Valor a ser formatado.
    decimals (int): Número de casas decimais (opcional, padrão é 2).
    
    Retorna:
    str: Valor formatado como percentual.
    """
    return f"{value:.{decimals}f}%"


# Função garantir que todos os números tenham exatamente 9 dígitos, com zeros à esquerda quando necessário, e usando o ponto como separador de milhar
def format_number(value: int) -> str:
    """
    Formata um número inteiro com 9 dígitos, adicionando zeros à esquerda se necessário,
    e utilizando ponto como separador de milhar no padrão brasileiro.
    
    Parâmetros:
    value (int): Valor a ser formatado (máximo 999.999.999).
    
    Retorna:
    str: Valor formatado com separadores de milhar e zeros à esquerda.
    """
    if value > 999_999_999:
        raise ValueError("O valor máximo permitido é 999.999.999")
    
    # Formata o número com zeros à esquerda e pontos como separadores de milhar
    formatted_value = f"{value:09d}"
    return f"{formatted_value[:3]}.{formatted_value[3:6]}.{formatted_value[6:9]}"


# Função para formatar data no padrão brasileiro (DD/MM/YYYY HH:MM:SS)
def format_datetime(value: str) -> str:
    """
    Formata uma data para o padrão brasileiro (DD/MM/YYYY HH:MM:SS).
    
    Parâmetros:
    value (str): Data no formato YYYY-MM-DD HH:MM:SS ou datetime.
    
    Retorna:
    str: Data formatada como DD/MM/YYYY HH:MM:SS.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value.strftime("%d/%m/%Y %H:%M:%S")


# Função para formatar tempo no formato HH:MM:SS
def format_time(seconds: int) -> str:
    """
    Formata um valor em segundos como um tempo no formato HH:MM:SS.
    
    Parâmetros:
    seconds (int): Valor em segundos.
    
    Retorna:
    str: Tempo formatado como HH:MM:SS.
    """
    return str(datetime.timedelta(seconds=seconds))


# Função para formatar número com casas decimais específicas
def format_decimal(value: float, decimals: int = 2) -> str:
    """
    Formata um valor numérico com um número específico de casas decimais.
    
    Parâmetros:
    value (float): Valor a ser formatado.
    decimals (int): Número de casas decimais (opcional, padrão é 2).
    
    Retorna:
    str: Valor formatado com o número específico de casas decimais.
    """
    return f"{value:.{decimals}f}"


# Função para limpar texto, removendo caracteres especiais e espaços extras
def clean_text(value: str) -> str:
    """
    Limpa um texto removendo caracteres especiais e espaços extras.
    
    Parâmetros:
    value (str): Texto a ser limpo.
    
    Retorna:
    str: Texto limpo.
    """
    value = re.sub(r'\s+', ' ', value)  # Substitui múltiplos espaços por um único
    value = re.sub(r'[^a-zA-Z0-9\s]', '', value)  # Remove caracteres especiais
    return value.strip()  # Remove espaços no início e no final

def clean_number(entrada: str) -> str:
    """
    Remove todos os caracteres não numéricos de uma string.

    Parâmetros:
        entrada (str): A string contendo caracteres alfanuméricos ou símbolos.

    Retorna:
        str: Uma string contendo apenas os números extraídos da entrada original.

    Exemplo:
        >>> clean_number("ABC123-456!789")
        '123456789'
    """
    return re.sub(r'\D', '', entrada)  # Remove tudo que não for número


# Função para formatar CNPJ no padrão brasileiro (XX.XXX.XXX/XXXX-XX)
def format_cnpj(cnpj: str) -> str:
    """
    Formata um CNPJ no padrão brasileiro (XX.XXX.XXX/XXXX-XX).
    
    Parâmetros:
    cnpj (str): CNPJ a ser formatado.
    
    Retorna:
    str: CNPJ formatado.
    """
    cnpj = re.sub(r'[^0-9]', '', cnpj)  # Remove qualquer coisa que não seja número
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def format_chave_acesso(chave: str) -> str:
    """
    Formata Chave de Acesso de Notas Fiscais no padrão (XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX).
    
    Parâmetros:
    chave (str): Chave de Acesso a ser formatada.
    
    Retorna:
    str: Chave de Acesso formatada.
    """
    chave = re.sub(r'[^0-9]', '', chave)  # Remove qualquer coisa que não seja número
    return ' '.join(chave[i:i+4] for i in range(0, 44, 4))

# Função para padronizar texto para salvar no banco de dados
def padronizar_texto(texto: str) -> str:
    """
    Padroniza um texto para salvar no banco de dados:
    - Converte para minúsculas
    - Remove espaços extras no início/fim
    - Mantém apenas um espaço entre palavras
    - Preserva acentuações

    Args:
        texto (str): Texto a ser processado

    Returns:
        str: Texto padronizado

    Exemplos:
        >>> padronizar_texto("  PRODUTO   AÇÚCAR  ")
        'produto açúcar'
        
        >>> padronizar_texto("São Paulo-HORTIFRUTI ")
        'são paulo-hortifruti'
    """
    # Mantém a acentuação original e normaliza para formato NFC
    texto_normalizado = unicodedata.normalize('NFC', texto)
    
    # Converte para minúsculas
    texto_minusculo = texto_normalizado.lower()
    
    # Remove espaços duplicados e espaços no início/fim
    texto_sem_espacos_extras = re.sub(r'\s+', ' ', texto_minusculo).strip()
    
    return texto_sem_espacos_extras