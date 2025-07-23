# utils/suggestion_optimizer.py
from difflib import SequenceMatcher
from typing import List, Dict, Tuple
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import logger

class SuggestionOptimizer:
    """
    Classe para otimizar o processamento de sugestões de associação
    usando técnicas de cache, processamento paralelo e normalização de texto
    """
    
    def __init__(self):
        self.cache_similaridade = {}
        self.cache_normalizacao = {}
        self.lock = threading.Lock()
        
    def normalizar_texto(self, texto: str) -> str:
        """Normaliza texto para melhorar a comparação"""
        if texto in self.cache_normalizacao:
            return self.cache_normalizacao[texto]
            
        # Remove caracteres especiais, espaços extras e converte para minúsculas
        texto_limpo = re.sub(r'[^\w\s]', ' ', texto.lower())
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
        
        # Remove palavras muito comuns que não agregam na comparação
        stop_words = {'de', 'da', 'do', 'para', 'com', 'em', 'na', 'no', 'a', 'o', 'e', 'ou'}
        palavras = [p for p in texto_limpo.split() if p not in stop_words and len(p) > 2]
        
        resultado = ' '.join(palavras)
        self.cache_normalizacao[texto] = resultado
        return resultado
    
    def calcular_similaridade_cache(self, texto1: str, texto2: str) -> float:
        """Calcula similaridade usando cache para evitar recálculos"""
        # Cria chave ordenada para cache bidirecional
        chave = tuple(sorted([texto1, texto2]))
        
        if chave in self.cache_similaridade:
            return self.cache_similaridade[chave]
        
        # Normaliza textos
        texto1_norm = self.normalizar_texto(texto1)
        texto2_norm = self.normalizar_texto(texto2)
        
        # Calcula similaridade
        similaridade = SequenceMatcher(None, texto1_norm, texto2_norm).ratio()
        
        # Armazena no cache
        with self.lock:
            self.cache_similaridade[chave] = similaridade
            
        return similaridade
    
    def processar_sugestoes_paralelo(self, 
                                   descricao_atual: str, 
                                   associacoes_cache: Dict, 
                                   produtos_cache: Dict, 
                                   limite_sugestoes: int = 3,
                                   threshold_similaridade: float = 0.5) -> List[Dict]:
        """
        Processa sugestões usando processamento paralelo para melhor performance
        Retorna apenas sugestões com similaridade >= threshold
        """
        try:
            inicio = time.time()
            
            # Divide o trabalho em chunks para processamento paralelo
            items_cache = list(associacoes_cache.items())
            chunk_size = max(1, len(items_cache) // 4)  # 4 threads
            chunks = [items_cache[i:i + chunk_size] for i in range(0, len(items_cache), chunk_size)]
            
            todas_sugestoes = []
            
            # Processa chunks em paralelo
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for chunk in chunks:
                    future = executor.submit(
                        self._processar_chunk, 
                        descricao_atual, 
                        chunk, 
                        produtos_cache, 
                        threshold_similaridade
                    )
                    futures.append(future)
                
                # Coleta resultados
                for future in as_completed(futures):
                    sugestoes_chunk = future.result()
                    todas_sugestoes.extend(sugestoes_chunk)
            
            # Filtra apenas sugestões >= threshold e ordena pela maior similaridade
            sugestoes_filtradas = [s for s in todas_sugestoes if s['similaridade'] >= threshold_similaridade]
            sugestoes_filtradas.sort(key=lambda x: x['similaridade'], reverse=True)
            
            # Limita resultados
            sugestoes_finais = sugestoes_filtradas[:limite_sugestoes]
            
            duracao = time.time() - inicio
            logger.info(f"Sugestões processadas em paralelo: {len(sugestoes_finais)} de {len(items_cache)} itens em {duracao:.3f}s (threshold: {threshold_similaridade})")
            
            return sugestoes_finais
            
        except Exception as e:
            logger.error(f"Erro no processamento paralelo de sugestões: {str(e)}")
            return []
    
    def _processar_chunk(self, 
                        descricao_atual: str, 
                        chunk: List[Tuple], 
                        produtos_cache: Dict, 
                        threshold_similaridade: float) -> List[Dict]:
        """Processa um chunk de dados para encontrar sugestões"""
        sugestoes = []
        
        for descricao_cache, associacoes in chunk:
            similaridade = self.calcular_similaridade_cache(descricao_atual, descricao_cache)
            
            # Só processa se similaridade >= threshold
            if similaridade >= threshold_similaridade:
                
                # Encontra a associação com maior similaridade para esta descrição
                melhor_associacao = None
                melhor_similaridade = 0
                
                for associacao in associacoes:
                    # Calcula similaridade específica para cada associação
                    sim_especifica = self.calcular_similaridade_cache(descricao_atual, associacao['descricao'])
                    
                    if sim_especifica >= threshold_similaridade and sim_especifica > melhor_similaridade:
                        melhor_similaridade = sim_especifica
                        melhor_associacao = associacao
                
                # Usa a associação com maior similaridade
                if melhor_associacao:
                    produto = produtos_cache.get(melhor_associacao['produto_id'])
                    
                    if produto:
                        sugestoes.append({
                            'produto': produto,
                            'quantidade_por_grade': melhor_associacao['quantidade_por_grade'],
                            'similaridade': melhor_similaridade,
                            'descricao_referencia': melhor_associacao['descricao']
                        })
        
        return sugestoes
    
    def processar_sugestoes_lote(self, 
                               items_nao_associados: List[Dict], 
                               associacoes_cache: Dict, 
                               produtos_cache: Dict,
                               threshold_similaridade: float = 0.5) -> Dict[str, List[Dict]]:
        """
        Processa sugestões para múltiplos itens de uma vez (processamento em lote)
        Retorna apenas sugestões com similaridade >= threshold
        """
        try:
            inicio = time.time()
            resultado = {}
            
            # Processa cada item
            for item in items_nao_associados:
                descricao = item['descricao']
                sugestoes = self.processar_sugestoes_paralelo(
                    descricao, 
                    associacoes_cache, 
                    produtos_cache,
                    limite_sugestoes=3,
                    threshold_similaridade=threshold_similaridade
                )
                
                # Só adiciona se há sugestões >= threshold
                if sugestoes:
                    chave_item = f"{item['fornecedor_id']}_{item['codigo_produto_fornecedor']}"
                    resultado[chave_item] = sugestoes
            
            duracao = time.time() - inicio
            logger.info(f"Processamento em lote concluído: {len(resultado)} itens com sugestões >= {threshold_similaridade} em {duracao:.2f}s")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no processamento em lote: {str(e)}")
            return {}
    
    def limpar_cache(self):
        """Limpa os caches para liberar memória"""
        with self.lock:
            self.cache_similaridade.clear()
            self.cache_normalizacao.clear()
            logger.info("Cache de sugestões limpo")
    
    def estatisticas_cache(self) -> Dict:
        """Retorna estatísticas do cache"""
        return {
            'similaridade_entries': len(self.cache_similaridade),
            'normalizacao_entries': len(self.cache_normalizacao),
            'memoria_estimada_kb': (len(self.cache_similaridade) + len(self.cache_normalizacao)) * 0.1
        }