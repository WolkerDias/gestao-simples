# views/produto/associacao/create.py
import streamlit as st
from difflib import SequenceMatcher
from services.produto_fornecedor_associacao_service import ProdutoFornecedorAssociacaoService
from services.produto_service import ProdutoService
from utils.message_handler import message_handler, MessageType
from utils.suggestion_optimizer import SuggestionOptimizer
from utils.logger import logger
import time

service = ProdutoFornecedorAssociacaoService()
produto_service = ProdutoService()
suggestion_optimizer = SuggestionOptimizer()


@st.dialog("📥 Fila de Associação de Produtos", width="large")
def show_create_associacao(itens_nao_associados=None):
    # Cache para otimizar performance
    if 'associacoes_cache' not in st.session_state:
        st.session_state.associacoes_cache = {}
    if 'produtos_cache' not in st.session_state:
        st.session_state.produtos_cache = {}
    if 'sugestoes_lote_cache' not in st.session_state:
        st.session_state.sugestoes_lote_cache = {}

    # Recarrega a lista ao iniciar/recarregar a página
    if itens_nao_associados:
        st.session_state.itens_fila = itens_nao_associados
    elif 'itens_fila' not in st.session_state:
        st.session_state.itens_fila = service.listar_todos_itens_nao_associados()
    if 'indice_atual' not in st.session_state:
        st.session_state.indice_atual = 0

    if 'form_id' not in st.session_state:
        st.session_state.form_id = 0

    # Carrega dados no cache se ainda não estão carregados
    _carregar_cache()
    
    # Processa sugestões em lote se ainda não foi feito
    _processar_sugestoes_lote()

    if not st.session_state.itens_fila:
        message_handler.add_message(
            MessageType.SUCCESS,
            f"Todos os itens foram associados! 🎉"
        )        
        st.rerun()
        return

    item_atual = st.session_state.itens_fila[st.session_state.indice_atual]
    produtos = list(st.session_state.produtos_cache.values())

    # Busca sugestões do cache em lote ou gera individualmente
    sugestoes = _obter_sugestoes_item(item_atual)

    # Seção de Sugestões Automáticas
    produto_selecionado = None
    quantidade_default = 1.0

    if sugestoes:        
        # Prepara opções para o segmented_control
        opcoes_sugestoes = []
        for sugestao in sugestoes:
            similaridade_pct = int(sugestao['similaridade'] * 100)
            if similaridade_pct >= 80:
                emoji = "🟢"
            elif similaridade_pct >= 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            opcoes_sugestoes.append(f"{emoji} {sugestao['descricao_referencia']}")
        
        # Segmented control para seleção de sugestões
        sugestao_selecionada = st.segmented_control(
            label="Selecione uma sugestão:",
            options=opcoes_sugestoes,
            default=opcoes_sugestoes[0],  # Primeira sugestão como padrão
            key=f"sugestao_segmented_{st.session_state.form_id}",
            help="Clique em uma das sugestões automáticas para associar rapidamente"
        )

        # Identifica qual sugestão foi selecionada
        if sugestao_selecionada:
            indice_selecionado = opcoes_sugestoes.index(sugestao_selecionada)
            if indice_selecionado < len(sugestoes):
                sugestao_escolhida = sugestoes[indice_selecionado]
                produto_selecionado = sugestao_escolhida['produto']
                quantidade_default = sugestao_escolhida['quantidade_por_grade']
                
                # Mostra similaridade selecionada
                similaridade = sugestao_escolhida['similaridade']
                if similaridade >= 0.8:
                    cor = "green"
                elif similaridade >= 0.6:
                    cor = "orange"
                else:
                    cor = "red"        

    # Formulário de Associação
    with st.form(key=f"associar_form_{st.session_state.form_id}", border=True):

        # Card do Item
        st.markdown(f"#### 🧾 Fornecedor: **{item_atual['fornecedor_id']} - {item_atual['fornecedor_nome']}**")
        st.markdown(f"**Item: {item_atual['codigo_produto_fornecedor']} | {item_atual['descricao']} | {item_atual['unidade']}**", help="Item a ser associado")
    
        # Encontra o índice do produto selecionado
        produto_index = None
        if produto_selecionado:
            # Mostra informações da sugestão escolhida
            st.markdown(f"#### Similaridade entre os itens: :{cor}[{similaridade*100:.2f}%]")
            st.badge(item_atual['descricao'], icon=":material/input:", color="blue")
            st.badge(sugestao_escolhida['descricao_referencia'], icon=":material/inventory:", color=cor)
            
            # Tenta encontrar o índice do produto selecionado
            try:
                produto_index = produtos.index(produto_selecionado)
            except ValueError:
                produto_index = None            

        col1, col2 = st.columns([0.7, 0.3])

        produto_final = col1.selectbox(
            "Produto Padrão",
            key=f"produto_selecionado_{st.session_state.form_id}",
            placeholder="Selecione um produto",
            options=produtos,
            format_func=lambda p: f"{p.nome} - {p.unidade_medida}",
            index=produto_index
        )

        quantidade = col2.number_input(
            "Quantidade por Grade",
            key=f"quantidade_{st.session_state.form_id}",
            min_value=0.01, 
            step=0.01, 
            value=quantidade_default, 
            format="%.3f"
        )

        if st.form_submit_button("💾 Salvar Associação", use_container_width=True, type="primary"):
            if produto_final is None:
                st.error("Selecione um produto para associar.")
            else:
                _salvar_associacao(item_atual, produto_final.id, quantidade)
                return


    # Controles de Navegação
    col_controls = st.columns([0.33333, 0.33333, 0.33333], vertical_alignment="center")

    if col_controls[0].button("⏮️ Item Anterior", disabled=st.session_state.indice_atual == 0, use_container_width=True):
        _retroceder_item()

    col_controls[1].button(f"**Item {st.session_state.indice_atual + 1} de {len(st.session_state.itens_fila)}**", use_container_width=True, type="tertiary")

    if col_controls[2].button("Próximo Item ⏭️", disabled=st.session_state.indice_atual == len(st.session_state.itens_fila) - 1, use_container_width=True):
        _avancar_item()

    st.divider()  
    # Estatísticas e controle de cache  
    stats = suggestion_optimizer.estatisticas_cache()
    with st.expander(f"📊 Cache: {stats['similaridade_entries']} similaridades | {stats['memoria_estimada_kb']:.1f}KB", expanded=False):
        
        col_stats = st.columns([0.5, 0.5])
        
        with col_stats[0]:
            if st.button("🗑️ Limpar Cache", use_container_width=True, help="Limpa cache de sugestões para liberar memória"):
                _limpar_caches()
        
        with col_stats[1]:
            if st.button("🔄 Reprocessar", use_container_width=True, help="Reprocessa sugestões para todos os itens"):
                _reprocessar_sugestoes()        

def _carregar_cache():
    """Carrega dados necessários no cache para otimizar performance"""
    try:
        if not st.session_state.associacoes_cache:
            inicio = time.time()
            associacoes = service.listar_associacoes()
            
            # Indexa associações por descrição para busca rápida
            for assoc in associacoes:
                chave = assoc.descricao_produto_fornecedor.lower().strip()
                if chave not in st.session_state.associacoes_cache:
                    st.session_state.associacoes_cache[chave] = []
                st.session_state.associacoes_cache[chave].append({
                    'produto_id': assoc.produto_id,
                    'produto_nome': assoc.produto.nome if assoc.produto else '',
                    'quantidade_por_grade': assoc.quantidade_por_grade,
                    'descricao': assoc.descricao_produto_fornecedor
                })
            
            logger.info(f"Cache de associações carregado: {len(associacoes)} registros em {time.time() - inicio:.2f}s")

        if not st.session_state.produtos_cache:
            inicio = time.time()
            produtos = produto_service.listar_produtos()
            st.session_state.produtos_cache = {p.id: p for p in produtos}
            logger.info(f"Cache de produtos carregado: {len(produtos)} registros em {time.time() - inicio:.2f}s")
            
    except Exception as e:
        logger.error(f"Erro ao carregar cache: {str(e)}")

def _processar_sugestoes_lote():
    """Processa sugestões em lote para todos os itens não associados"""
    try:
        if not st.session_state.sugestoes_lote_cache and st.session_state.itens_fila:
            inicio = time.time()
            
            # Processa sugestões para todos os itens de uma vez
            st.session_state.sugestoes_lote_cache = suggestion_optimizer.processar_sugestoes_lote(
                st.session_state.itens_fila,
                st.session_state.associacoes_cache,
                st.session_state.produtos_cache
            )
            
            duracao = time.time() - inicio
            logger.info(f"Cache de sugestões em lote criado em {duracao:.2f}s")
            
    except Exception as e:
        logger.error(f"Erro ao processar sugestões em lote: {str(e)}")

def _obter_sugestoes_item(item_atual):
    """Obtém sugestões para o item atual (do cache em lote ou gera individualmente)"""
    try:
        chave_item = f"{item_atual['fornecedor_id']}_{item_atual['codigo_produto_fornecedor']}"
        
        # Tenta buscar do cache em lote primeiro
        if chave_item in st.session_state.sugestoes_lote_cache:
            return st.session_state.sugestoes_lote_cache[chave_item]
        
        # Se não encontrou no cache, gera individualmente
        return suggestion_optimizer.processar_sugestoes_paralelo(
            item_atual['descricao'],
            st.session_state.associacoes_cache,
            st.session_state.produtos_cache,
            limite_sugestoes=3,
            threshold_similaridade=0.5
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter sugestões para item: {str(e)}")
        return []

def _salvar_associacao(item, produto_id, quantidade):
    """Salva a associação no banco de dados"""
    try:
        dados = {
            'produto_id': produto_id,
            'fornecedor_id': item['fornecedor_id'],
            'quantidade_por_grade': quantidade,
            'codigo_produto_fornecedor': item['codigo_produto_fornecedor'],
            'descricao_produto_fornecedor': item['descricao']
        }

        service.criar_associacao(dados)
        
        # Atualiza o cache com a nova associação
        _atualizar_cache_associacao(dados)
        
        # Limpa cache de sugestões em lote para forçar recálculo
        st.session_state.sugestoes_lote_cache = {}
        
        # Remove item da fila
        st.session_state.itens_fila.pop(st.session_state.indice_atual)

        # Atualiza a lista e reinicia o processo
        st.session_state.itens_fila = service.listar_todos_itens_nao_associados()
        st.session_state.form_id += 1
        
        st.rerun(scope="fragment")
        
    except Exception as e:
        logger.error(f"Erro ao salvar associação: {str(e)}")
        st.error(f"Erro ao salvar associação: {str(e)}")

def _atualizar_cache_associacao(dados):
    """Atualiza o cache de associações com a nova associação criada"""
    try:
        chave = dados['descricao_produto_fornecedor'].lower().strip()
        produto = st.session_state.produtos_cache.get(dados['produto_id'])
        
        if produto:
            nova_associacao = {
                'produto_id': dados['produto_id'],
                'produto_nome': produto.nome,
                'quantidade_por_grade': dados['quantidade_por_grade'],
                'descricao': dados['descricao_produto_fornecedor']
            }
            
            if chave not in st.session_state.associacoes_cache:
                st.session_state.associacoes_cache[chave] = []
            st.session_state.associacoes_cache[chave].append(nova_associacao)
            
    except Exception as e:
        logger.error(f"Erro ao atualizar cache: {str(e)}")

def _limpar_caches():
    """Limpa todos os caches para liberar memória"""
    try:
        suggestion_optimizer.limpar_cache()
        st.session_state.associacoes_cache = {}
        st.session_state.produtos_cache = {}
        st.session_state.sugestoes_lote_cache = {}
        
        message_handler.add_message(
            MessageType.SUCCESS,
            "Cache limpo com sucesso! 🧹"
        )
        st.rerun()
        
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        st.error("Erro ao limpar cache")

def _reprocessar_sugestoes():
    """Força o reprocessamento de todas as sugestões"""
    try:
        st.session_state.sugestoes_lote_cache = {}
        _processar_sugestoes_lote()
        
        message_handler.add_message(
            MessageType.SUCCESS,
            "Sugestões reprocessadas! 🔄"
        )
        st.rerun()
        
    except Exception as e:
        logger.error(f"Erro ao reprocessar sugestões: {str(e)}")
        st.error("Erro ao reprocessar sugestões")

def _avancar_item():
    if st.session_state.indice_atual < len(st.session_state.itens_fila) - 1:
        st.session_state.indice_atual += 1
        st.session_state.form_id += 1
    st.rerun(scope="fragment")

def _retroceder_item():
    if st.session_state.indice_atual > 0:
        st.session_state.indice_atual -= 1
        st.session_state.form_id += 1
    st.rerun(scope="fragment")