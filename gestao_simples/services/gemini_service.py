# services/gemini_service.py
import google.generativeai as genai
from PIL import Image
import json
import os
from datetime import datetime
from models.nota_entrada import NotaEntrada
from models.fornecedor import Fornecedor
from utils.logger import logger
import streamlit as st
from difflib import SequenceMatcher
import re

class GeminiService:
    def __init__(self):
        # Configurar a API key do Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        gemini_model = os.getenv('GEMINI_MODEL')
        if not api_key:
            # Fallback para configuração via Streamlit secrets
            api_key = st.secrets.get("GEMINI_API_KEY", None)
            gemini_model = st.secrets.get("GEMINI_MODEL")

        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente ou secrets do Streamlit")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(gemini_model)

    def add_matching_suggestions(self, cupom_data, fornecedor_id, nota_entrada_service):
        """
        Adiciona sugestões de matching aos dados já extraídos do cupom
        
        Args:
            cupom_data: Dados já extraídos do cupom
            fornecedor_id: ID do fornecedor para buscar itens históricos
            nota_entrada_service: Service para buscar itens históricos
            
        Returns:
            dict: Dados do cupom com sugestões de matching adicionadas
        """
        try:
            # Faz uma cópia dos dados para não modificar o original
            cupom_data_with_matching = cupom_data.copy()
            
            # Gera sugestões de matching
            cupom_data_with_matching = self._generate_matching_suggestions(
                cupom_data_with_matching, fornecedor_id, nota_entrada_service
            )
            
            return cupom_data_with_matching

        except Exception as e:
            logger.error(f"Erro ao adicionar sugestões de matching: {str(e)}")
            # Em caso de erro, retorna dados originais sem sugestões
            cupom_data['matching_suggestions'] = []
            return cupom_data

    def extract_cupom_data(self, image):
        """
        Extrai dados do cupom não fiscal usando a Gemini API
        
        Args:
            image: Imagem PIL do cupom
            
        Returns:
            dict: Dados estruturados do cupom no formato esperado
        """
        try:
            prompt = """
            Analise esta imagem de cupom não fiscal e extraia os seguintes dados em formato JSON:

            {
                "fornecedor": {
                    "nome": "nome do estabelecimento/loja",
                    "cnpj": "CNPJ se disponível (apenas números) ou None se não encontrado"
                },
                "nota_entrada": {
                    "chave_acesso": "chave de acesso se disponível ou None",
                    "numero_nota_entrada": "número da nota/cupom",
                    "serie_nota_entrada": "série se disponível ou '1'",
                    "data_emissao": "data no formato DD/MM/YYYY HH:MM:SS",
                    "total_nota_entrada": valor_total_numerico,
                    "modelo": 65
                },
                "itens": [
                    {
                        "codigo_produto_fornecedor": "código do produto (geralmente aparece no início da linha que contém o nome do produto)",
                        "descricao": "descrição do produto",
                        "quantidade": quantidade_numerica,
                        "unidade_medida": "UN, KG, L, etc.",
                        "valor": valor_unitario_numerico
                    }
                ]
            }

            INSTRUÇÕES IMPORTANTES:
            - Extraia TODOS os itens visíveis no cupom
            - Cada item pode ocupar **três linhas consecutivas**:
                🔹 Linha 1: código e nome do produto (ex: '49 FILE KG')
                🔹 Linha 2: quantidade e preço unitário
                🔹 Linha 3: parte decimal do **total do item (valor total pago)**

            - Se a linha 2 já contiver o total com a parte decimal, ignore a linha 3.
            - Sempre agrupe as linhas consecutivas referentes ao mesmo produto.
            - Para valores monetários:
                🔸 Use **apenas ponto como separador decimal**
                🔸 **Não use separador de milhar**
                🔸 **Exemplo correto:** 15.99 (e não 15,99 ou 1.599,00)
                🔸 **Os valores devem refletir o preço real do produto, não valores inflacionados**
            - Para datas, use o formato DD/MM/YYYY HH:MM:SS
            - Se não encontrar algum campo, use null ou valores padrão apropriados
            - Para quantidade, assuma 3 casas decimais, se não especificada, assuma 1
            - Para unidade_medida, se não especificada, use "UN"
            - Seja preciso com os valores e descrições dos produtos
            - Retorne APENAS o JSON, sem texto adicional
            """

            response = self.model.generate_content([prompt, image])
            
            # Limpa a resposta removendo possíveis markdown
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()

            # Parse do JSON
            data = json.loads(json_text)
            
            # Valida e processa os dados
            processed_data = self._process_gemini_response(data)
            
            logger.info("Dados do cupom extraídos com sucesso")
            return processed_data

        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON da resposta do Gemini: {str(e)}")
            logger.error(f"Resposta recebida: {response.text}")
            raise Exception(f"Resposta da API não está em formato JSON válido: {str(e)}")
        
        except Exception as e:
            logger.error(f"Erro ao processar cupom com Gemini API: {str(e)}")
            raise Exception(f"Erro ao processar cupom: {str(e)}")

    def _generate_matching_suggestions(self, cupom_data, fornecedor_id, nota_entrada_service):
        """
        Gera sugestões de matching para aprovação do usuário
        
        Args:
            cupom_data: Dados extraídos do cupom
            fornecedor_id: ID do fornecedor
            nota_entrada_service: Service para buscar itens históricos
            
        Returns:
            dict: Dados do cupom com sugestões de matching
        """
        try:
            # Busca itens históricos do fornecedor
            itens_historicos = nota_entrada_service.listar_itens_unicos_por_fornecedor(fornecedor_id)
            
            if not itens_historicos:
                # Se não há itens históricos, retorna dados originais
                cupom_data['matching_suggestions'] = []
                return cupom_data
            
            sugestoes_matching = []
            
            for i, item_gemini in enumerate(cupom_data['itens']):
                melhor_match = None
                melhor_score = 0
                
                # Compara com cada item histórico
                for item_historico in itens_historicos:
                    score = self._calculate_similarity_score(item_gemini, item_historico)
                    
                    if score > melhor_score and score >= 0.6:  # Threshold de 60% para sugestões
                        melhor_match = item_historico
                        melhor_score = score
                
                if melhor_match:
                    sugestao = {
                        'item_index': i,
                        'item_original': item_gemini.copy(),
                        'item_sugerido': {
                            'codigo_produto_fornecedor': melhor_match['codigo'],
                            'descricao': melhor_match['descricao'],
                            'quantidade': item_gemini['quantidade'],  # Mantém quantidade do cupom
                            'unidade_medida': melhor_match['unidade'],
                            'valor': item_gemini['valor']  # Mantém valor do cupom
                        },
                        'similarity_score': melhor_score,
                        'changes': self._get_item_changes(item_gemini, melhor_match)
                    }
                    sugestoes_matching.append(sugestao)
            
            cupom_data['matching_suggestions'] = sugestoes_matching
            return cupom_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar sugestões de matching: {str(e)}")
            # Em caso de erro, retorna dados originais
            cupom_data['matching_suggestions'] = []
            return cupom_data

    def _get_item_changes(self, item_original, item_historico):
        """
        Identifica as mudanças que serão feitas no item
        
        Args:
            item_original: Item extraído pelo Gemini
            item_historico: Item do histórico
            
        Returns:
            list: Lista de mudanças
        """
        changes = []
        
        if item_original.get('codigo_produto_fornecedor', '') != item_historico.get('codigo', ''):
            changes.append({
                'field': 'codigo_produto_fornecedor',
                'from': item_original.get('codigo_produto_fornecedor', ''),
                'to': item_historico.get('codigo', ''),
                'label': 'Código'
            })
        
        if item_original.get('descricao', '') != item_historico.get('descricao', ''):
            changes.append({
                'field': 'descricao',
                'from': item_original.get('descricao', ''),
                'to': item_historico.get('descricao', ''),
                'label': 'Descrição'
            })
        
        if item_original.get('unidade_medida', '') != item_historico.get('unidade', ''):
            changes.append({
                'field': 'unidade_medida',
                'from': item_original.get('unidade_medida', ''),
                'to': item_historico.get('unidade', ''),
                'label': 'Unidade'
            })
        
        return changes

    def apply_approved_matching(self, cupom_data, approved_suggestions):
        """
        Aplica as sugestões de matching aprovadas pelo usuário
        
        Args:
            cupom_data: Dados originais do cupom
            approved_suggestions: Lista de índices das sugestões aprovadas
            
        Returns:
            dict: Dados do cupom com matching aplicado
        """
        try:
            if 'matching_suggestions' not in cupom_data:
                return cupom_data
            
            itens_modificados = cupom_data['itens'].copy()
            matching_aplicado = 0
            
            for sugestao in cupom_data['matching_suggestions']:
                item_index = sugestao['item_index']
                
                if item_index in approved_suggestions:
                    # Aplica a sugestão aprovada
                    itens_modificados[item_index] = sugestao['item_sugerido']
                    matching_aplicado += 1
                    
                    logger.info(f"Matching aplicado para item {item_index}: {sugestao['item_original']['descricao']} -> {sugestao['item_sugerido']['descricao']}")
            
            # Atualiza os dados do cupom
            cupom_data['itens'] = itens_modificados
            cupom_data['matching_info'] = {
                'total_itens': len(cupom_data['itens']),
                'sugestoes_disponiveis': len(cupom_data['matching_suggestions']),
                'itens_matchados': matching_aplicado,
                'itens_originais': len(cupom_data['itens']) - matching_aplicado
            }
            
            # Remove as sugestões já processadas
            del cupom_data['matching_suggestions']
            
            return cupom_data
            
        except Exception as e:
            logger.error(f"Erro ao aplicar matching aprovado: {str(e)}")
            return cupom_data

    def _merge_with_existing_items(self, cupom_data, fornecedor_id, nota_entrada_service):
        """
        Compara itens extraídos com itens já cadastrados e faz o merge inteligente
        
        Args:
            cupom_data: Dados extraídos do cupom
            fornecedor_id: ID do fornecedor
            nota_entrada_service: Service para buscar itens históricos
            
        Returns:
            dict: Dados do cupom com itens mesclados
        """
        try:
            # Busca itens históricos do fornecedor
            itens_historicos = nota_entrada_service.listar_itens_unicos_por_fornecedor(fornecedor_id)
            
            if not itens_historicos:
                # Se não há itens históricos, retorna dados originais
                return cupom_data
            
            itens_mesclados = []
            itens_matchados = set()  # Para rastrear quais itens históricos já foram usados
            
            for item_gemini in cupom_data['itens']:
                melhor_match = None
                melhor_score = 0
                melhor_index = -1
                
                # Compara com cada item histórico
                for i, item_historico in enumerate(itens_historicos):
                    if i in itens_matchados:
                        continue  # Pula itens já matchados
                    
                    score = self._calculate_similarity_score(item_gemini, item_historico)
                    
                    if score > melhor_score and score >= 0.7:  # Threshold de 70% de similaridade
                        melhor_match = item_historico
                        melhor_score = score
                        melhor_index = i
                
                if melhor_match:
                    # Usa dados do item histórico com valores atualizados do Gemini
                    item_final = {
                        'codigo_produto_fornecedor': melhor_match['codigo'],
                        'descricao': melhor_match['descricao'],  # Usa descrição padronizada
                        'quantidade': item_gemini['quantidade'],  # Usa quantidade do cupom
                        'unidade_medida': melhor_match['unidade'],  # Usa unidade padronizada
                        'valor': item_gemini['valor']  # Usa valor atual do cupom
                    }
                    itens_matchados.add(melhor_index)
                    
                    logger.info(f"Item matchado: {item_gemini['descricao']} -> {melhor_match['descricao']} (Score: {melhor_score:.2f})")
                else:
                    # Usa dados originais do Gemini
                    item_final = item_gemini
                    logger.info(f"Item novo: {item_gemini['descricao']}")
                
                itens_mesclados.append(item_final)
            
            # Substitui itens originais pelos mesclados
            cupom_data['itens'] = itens_mesclados
            cupom_data['matching_info'] = {
                'total_itens': len(cupom_data['itens']),
                'itens_matchados': len(itens_matchados),
                'itens_novos': len(cupom_data['itens']) - len(itens_matchados)
            }
            
            return cupom_data
            
        except Exception as e:
            logger.error(f"Erro ao mesclar itens: {str(e)}")
            # Em caso de erro, retorna dados originais
            return cupom_data

    def _calculate_similarity_score(self, item_gemini, item_historico):
        """
        Calcula score de similaridade entre item do Gemini e item histórico
        
        Args:
            item_gemini: Item extraído pelo Gemini
            item_historico: Item do histórico do fornecedor
            
        Returns:
            float: Score de 0 a 1 indicando similaridade
        """
        score_total = 0
        peso_total = 0
        
        # 1. Comparação de código (peso 40%)
        codigo_gemini = self._normalize_string(item_gemini.get('codigo_produto_fornecedor', ''))
        codigo_historico = self._normalize_string(item_historico.get('codigo', ''))
        
        if codigo_gemini and codigo_historico:
            if codigo_gemini == codigo_historico:
                score_codigo = 1.0
            else:
                score_codigo = SequenceMatcher(None, codigo_gemini, codigo_historico).ratio()
            score_total += score_codigo * 0.4
            peso_total += 0.4
        
        # 2. Comparação de descrição (peso 50%)
        desc_gemini = self._normalize_string(item_gemini.get('descricao', ''))
        desc_historico = self._normalize_string(item_historico.get('descricao', ''))
        
        if desc_gemini and desc_historico:
            # Usa SequenceMatcher para comparação de strings
            score_descricao = SequenceMatcher(None, desc_gemini, desc_historico).ratio()
            
            # Bonus para palavras-chave em comum
            palavras_gemini = set(desc_gemini.split())
            palavras_historico = set(desc_historico.split())
            palavras_comuns = palavras_gemini.intersection(palavras_historico)
            
            if palavras_comuns:
                bonus = len(palavras_comuns) / max(len(palavras_gemini), len(palavras_historico))
                score_descricao = min(1.0, score_descricao + bonus * 0.2)
            
            score_total += score_descricao * 0.5
            peso_total += 0.5
        
        # 3. Comparação de unidade de medida (peso 10%)
        unidade_gemini = self._normalize_string(item_gemini.get('unidade_medida', ''))
        unidade_historico = self._normalize_string(item_historico.get('unidade', ''))
        
        if unidade_gemini and unidade_historico:
            score_unidade = 1.0 if unidade_gemini == unidade_historico else 0.0
            score_total += score_unidade * 0.1
            peso_total += 0.1
        
        # Calcula score final
        if peso_total > 0:
            return score_total / peso_total
        else:
            return 0.0

    def _normalize_string(self, text):
        """
        Normaliza string para comparação (remove acentos, espaços extras, etc.)
        
        Args:
            text: String para normalizar
            
        Returns:
            str: String normalizada
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove espaços extras e converte para minúsculo
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        
        # Remove caracteres especiais comuns
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized

    def _process_gemini_response(self, data):
        """
        Processa a resposta da Gemini API para o formato esperado pelo sistema
        
        Args:
            data: Dict com dados extraídos pela Gemini API
            
        Returns:
            dict: Dados processados no formato esperado
        """
        try:
            # Processa dados do fornecedor
            fornecedor_data = data.get('fornecedor', {})
            fornecedor = Fornecedor(
                nome=fornecedor_data.get('nome', 'Fornecedor não identificado'),
                cnpj=fornecedor_data.get('cnpj') or ''
            )

            # Processa dados da nota
            nota_data = data.get('nota_entrada', {})
            
            # Converte data para datetime
            data_emissao_str = nota_data.get('data_emissao', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            try:
                data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                # Fallback se formato de data estiver incorreto
                data_emissao = datetime.now()

            nota_entrada = NotaEntrada(
                modelo=nota_data.get('modelo', 65),  # 65 para cupons não fiscais
                chave_acesso=nota_data.get('chave_acesso') or '',
                fornecedor_id=None,  # Será definido após salvar o fornecedor
                data_emissao=data_emissao,
                numero_nota_entrada=str(nota_data.get('numero_nota_entrada', '1')),
                serie_nota_entrada=str(nota_data.get('serie_nota_entrada', '1')),
                total_nota_entrada=float(nota_data.get('total_nota_entrada', 0))
            )

            # Processa itens
            itens_data = data.get('itens', [])
            itens = []
            
            for item_data in itens_data:
                item = {
                    'codigo_produto_fornecedor': item_data.get('codigo_produto_fornecedor', ''),
                    'descricao': item_data.get('descricao', 'Produto não identificado'),
                    'quantidade': float(item_data.get('quantidade', 1)),
                    'unidade_medida': item_data.get('unidade_medida', 'UN'),
                    'valor': float(item_data.get('valor', 0))
                }
                itens.append(item)

            # Validação: se não há itens, cria um item genérico
            if not itens:
                itens.append({
                    'codigo_produto_fornecedor': '',
                    'descricao': 'Item não identificado',
                    'quantidade': 1.0,
                    'unidade_medida': 'UN',
                    'valor': nota_entrada.total_nota_entrada
                })

            return {
                'fornecedor': fornecedor,
                'nota_entrada': nota_entrada,
                'itens': itens
            }

        except Exception as e:
            logger.error(f"Erro ao processar resposta da Gemini API: {str(e)}")
            raise Exception(f"Erro ao processar dados extraídos: {str(e)}")

    def test_connection(self):
        """
        Testa a conexão com a Gemini API
        
        Returns:
            bool: True se conectado com sucesso
        """
        try:
            response = self.model.generate_content("Teste de conexão")
            return True
        except Exception as e:
            logger.error(f"Erro ao testar conexão com Gemini API: {str(e)}")
            return False