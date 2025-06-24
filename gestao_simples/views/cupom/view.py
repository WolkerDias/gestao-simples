# views/cupom/view.py
import streamlit as st
from PIL import Image
import pandas as pd
from services.gemini_service import GeminiService
from services.fornecedor_service import FornecedorService
from services.nota_entrada_service import NotaEntradaService
from services.item_nota_entrada_service import ItemNotaEntradaService
from utils.message_handler import message_handler, MessageType
from utils.format import format_brl, format_cnpj, format_datetime, format_chave_acesso

class CupomView:
    def __init__(self):
        self.gemini_service = GeminiService()
        self.fornecedor_service = FornecedorService()
        self.nota_entrada_service = NotaEntradaService()
        self.item_service = ItemNotaEntradaService()
        
        # Cache de fornecedores para evitar múltiplas consultas
        self._fornecedores_cache = None
        self._cache_invalidated = False
        
        # Estados para controle de dialogs
        if 'cupom_state' not in st.session_state:
            st.session_state.cupom_state = 'capture'  # capture, processing, fornecedor_selection, matching_review, data_edit
        if 'cupom_data' not in st.session_state:
            st.session_state.cupom_data = None
   
        self.render()

    def _get_fornecedores_cached(self):
        """
        Retorna lista de fornecedores usando cache para evitar múltiplas consultas
        """
        if self._fornecedores_cache is None or self._cache_invalidated:
            self._fornecedores_cache = self.fornecedor_service.listar_fornecedores()
            self._cache_invalidated = False
        return self._fornecedores_cache

    def _invalidate_fornecedores_cache(self):
        """
        Invalida o cache quando um novo fornecedor é criado
        """
        self._cache_invalidated = True

    def render(self):
        st.title("📸 Leitor de Cupom Não Fiscal")

        message_handler.display_toast_message()
        
        # Teste de conexão com Gemini API
        if not self._test_gemini_connection():
            st.error("❌ Não foi possível conectar com a API do Gemini. Verifique as configurações.")
            st.info("💡 Certifique-se de que GEMINI_API_KEY está configurada nas variáveis de ambiente ou nos secrets do Streamlit.")
            return

        # Controle de estados dos dialogs
        if st.session_state.cupom_state == 'capture':
            self._render_capture_interface()
        elif st.session_state.cupom_state == 'matching_review':
            self._display_matching_approval_dialog()
        elif st.session_state.cupom_state == 'data_edit':
            self._display_cupom_data_dialog()
        elif st.session_state.cupom_state == 'processing':
            self._display_processing_dialog()
        elif st.session_state.cupom_state == 'fornecedor_selection':
            self._display_fornecedor_selection_dialog()            

    def _test_gemini_connection(self):
        """Testa conexão com Gemini API"""
        try:
            return self.gemini_service.test_connection()
        except Exception as e:
            st.error(f"Erro ao conectar com Gemini API: {str(e)}")
            return False

    def _render_capture_interface(self):
        """Renderiza a interface de captura de cupom"""

        # Seleção do modo de captura
        option_map = {
            0: ":material/upload: Upload de Imagem",
            1: ":material/camera: Câmera ao Vivo"
        }

        # Seleção do método de entrada de Cupom com valor inicial 0
        selection = st.segmented_control(
            "Método de Entrada de Cupom",
            options=option_map.keys(),
            format_func=lambda option: option_map[option],
            selection_mode="single",
            default=0
        )

        if selection == 0:
            input_file = self._handle_upload_mode()
        elif selection == 1:
            input_file = self._handle_camera_mode()
        
        if input_file is not None:
            self._process_cupom_image(Image.open(input_file))
        
    def _handle_upload_mode(self):
        key = st.session_state.get("file_uploader_key", 0)
        input_file = st.file_uploader(
            "Faça upload de uma imagem contendo o cupom:", 
            type=["jpg", "jpeg", "png"],
            key=f"uploader_{key}"
        )
        return input_file
   
    def _handle_camera_mode(self):
        # Adiciona estilos para a câmera
        self._add_camera_styles()
        
        # Input da câmera
        key = st.session_state.get("cupom_camera_key", 0)
        input_file = st.camera_input(
            "Capture uma imagem do cupom não fiscal:",
            key=f"cupom_camera_{key}",
            help="Posicione o cupom de forma que todos os itens e valores estejam visíveis e legíveis"
        )
        return input_file

    def _process_cupom_image(self, image):
        """Processa a imagem do cupom capturada"""
        try:
            # Mostra a imagem capturada
            with st.expander("🖼️ Imagem Capturada", expanded=False):
                st.image(image, caption="Cupom Capturado", use_container_width=True)
            
            # Armazena a imagem para processamento
            st.session_state.cupom_image = image
            st.session_state.cupom_state = 'processing'
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erro ao processar imagem do cupom: {str(e)}")

    def _find_existing_fornecedor(self, fornecedor_nome, fornecedor_cnpj):
        """
        Função auxiliar otimizada para centralizar a lógica de busca de fornecedor
        Usa cache local para evitar múltiplas consultas ao banco
        
        Args:
            fornecedor_nome: Nome do fornecedor extraído do cupom
            fornecedor_cnpj: CNPJ do fornecedor extraído do cupom
            
        Returns:
            Fornecedor ou None se não encontrado
        """
        fornecedor_encontrado = None
        
        # Primeira tentativa: busca por CNPJ (consulta otimizada)
        if fornecedor_cnpj:
            fornecedor_encontrado = self.fornecedor_service.buscar_fornecedor_por_cnpj(fornecedor_cnpj)
        
        # Segunda tentativa: busca por nome similar usando cache
        if not fornecedor_encontrado and fornecedor_nome != 'Fornecedor não identificado':
            fornecedores = self._get_fornecedores_cached()  # ✅ Usa cache
            for f in fornecedores:
                if self._similarity_match(fornecedor_nome.lower(), f.nome.lower()) > 0.8:
                    fornecedor_encontrado = f
                    break
        
        return fornecedor_encontrado

    @st.dialog("Revisão de Matching Inteligente", width="large")
    def _display_matching_approval_dialog(self):
        """Dialog para aprovação das sugestões de matching"""
        cupom_data = st.session_state.cupom_data
        matching_suggestions = cupom_data['matching_suggestions']
        
        st.info(f"📊 **{len(matching_suggestions)} sugestões de padronização** encontradas. Revise e aprove as que desejar aplicar.")
        
        # Estado para controlar quais sugestões foram aprovadas
        if 'matching_approval_state' not in st.session_state:
            st.session_state.matching_approval_state = {}
        
        approved_suggestions = set()
        
        # Exibe cada sugestão para aprovação
        for i, sugestao in enumerate(matching_suggestions):
            item_original = sugestao['item_original']
            item_sugerido = sugestao['item_sugerido']
            similarity_score = sugestao['similarity_score']
            changes = sugestao['changes']
            
            with st.container(border=True):
                # Header da sugestão
                
                st.write(f"**Item {i+1}:** {item_original['codigo_produto_fornecedor']} - {item_original['descricao']}")
                    
                # Score de similaridade com cor baseada no valor
                score_color = "🟢" if similarity_score >= 0.8 else "🟡" if similarity_score >= 0.6 else "🟠"
                
                # Detalhes das mudanças em formato mais compacto
                if changes:
                    st.write("**Mudanças propostas:**")
                    changes_text = []
                    for change in changes:
                        if change['from'] != change['to']:
                            changes_text.append(f"• **{change['label']}:** `{change['from']}` → `{change['to']}`")
                    
                    if changes_text:
                        for change_text in changes_text:
                            st.markdown(change_text)
                    else:
                        st.info("ℹ️ Apenas padronização de formatação")
                else:
                    st.info("ℹ️ Nenhuma mudança significativa detectada")
                
                # Checkbox para aprovação com estado persistente
                approve_key = f"approve_matching_{i}"
                default_value = similarity_score >= 0.8  # Auto-seleciona sugestões com alta similaridade
                
                # Inicializa o estado se não existir
                if approve_key not in st.session_state.matching_approval_state:
                    st.session_state.matching_approval_state[approve_key] = default_value
                
                if st.checkbox(
                    f"Aplicar esta sugestão (Similaridade: {similarity_score:.0%} {score_color})", 
                    key=approve_key,
                    value=st.session_state.matching_approval_state[approve_key]
                ):
                    approved_suggestions.add(sugestao['item_index'])
                    st.session_state.matching_approval_state[approve_key] = True
                else:
                    st.session_state.matching_approval_state[approve_key] = False
        
        st.markdown("---")
        
        # Resumo das aprovações
        if approved_suggestions:
            st.success(f"✅ **{len(approved_suggestions)} sugestões** selecionadas para aplicação")
        else:
            st.info("ℹ️ Nenhuma sugestão selecionada - os dados originais da IA serão mantidos")
        
        # Botões de ação
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("🎯 Aplicar Selecionado", type="primary", use_container_width=True):
                self._apply_matching_and_continue(approved_suggestions)
        
        with col2:
            if st.button("✅ Aprovar Todas", use_container_width=True):
                # Aprova todas as sugestões
                all_suggestions = {sugestao['item_index'] for sugestao in matching_suggestions}
                self._apply_matching_and_continue(all_suggestions)
        
        with col3:
            if st.button("🚫 Pular Matching", use_container_width=True):
                # Remove as sugestões e continua com dados originais
                if 'matching_suggestions' in st.session_state.cupom_data:
                    del st.session_state.cupom_data['matching_suggestions']
                self._clear_matching_state()
                st.session_state.cupom_state = 'data_edit'
                st.rerun()
        
        with col4:
            if st.button("🔄 Nova Captura", use_container_width=True):
                self._reset_to_capture()

    def _apply_matching_and_continue(self, approved_suggestions):
        """Aplica o matching aprovado e continua para a tela de edição"""
        try:
            # Aplica as sugestões aprovadas
            cupom_data_with_matching = self.gemini_service.apply_approved_matching(
                st.session_state.cupom_data, approved_suggestions
            )
            
            # Atualiza os dados no session state
            st.session_state.cupom_data = cupom_data_with_matching
            
            # Limpa o estado de aprovação
            self._clear_matching_state()
            
            # Muda para o estado de edição
            st.session_state.cupom_state = 'data_edit'
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erro ao aplicar matching: {str(e)}")

    @st.dialog("Novo Cupom Não Fiscal via IA", width="large")
    def _display_cupom_data_dialog(self):
        """Dialog para exibir os dados extraídos do cupom para revisão e edição"""
        cupom_data = st.session_state.cupom_data
        selected_fornecedor = st.session_state.get("selected_fornecedor_obj", cupom_data['fornecedor'])

        if 'matching_info' in cupom_data:
            matching_info = cupom_data['matching_info']
            if matching_info.get('itens_matchados', 0) > 0:
                st.success(f"🎯 **Matching Aplicado:** {matching_info['itens_matchados']} itens padronizados com sucesso!")
            else:
                st.info("ℹ️ **Matching não aplicado** - utilizando dados originais extraídos pela IA")

        st.info("⚠️ **Importante:** Revise todos os dados extraídos pela IA antes de salvar. A precisão pode variar dependendo da qualidade da imagem.")

        # 🏪 Fornecedor
        st.subheader("🏪 Dados do Fornecedor:")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            col1.write(f"**Nome:** {selected_fornecedor.nome}")
            cnpj_display = format_cnpj(selected_fornecedor.cnpj) if selected_fornecedor.cnpj else "Não informado"
            col2.write(f"**CNPJ:** {cnpj_display}")

        # 📄 Nota
        st.subheader("📄 Dados da Nota:")
        with st.container(border=True):
            if cupom_data['nota_entrada'].chave_acesso:
                st.write(f"**Chave de Acesso:** {format_chave_acesso(cupom_data['nota_entrada'].chave_acesso)}")
            col1, col2, col3 = st.columns([1, 1, 2])
            col1.write(f"**Número:** {cupom_data['nota_entrada'].numero_nota_entrada}")
            col2.write(f"**Série:** {cupom_data['nota_entrada'].serie_nota_entrada}")
            col3.write(f"**Data Emissão:** {format_datetime(cupom_data['nota_entrada'].data_emissao)}")

        # 🛒 Itens
        st.subheader("🛒 Itens do Cupom:")
        if 'matching_info' in cupom_data and cupom_data['matching_info'].get('itens_matchados', 0) > 0:
            st.success(f"✨ **{cupom_data['matching_info']['itens_matchados']} itens foram padronizados** com base no histórico do fornecedor!")

        st.info("✏️ Você pode editar diretamente na tabela abaixo. Clique nas células para modificar os valores.")
        itens_df = pd.DataFrame(cupom_data['itens'])

        edited_df = st.data_editor(
            itens_df,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )

        # ⚖️ Validações
        if not edited_df.empty:
            total_calc = (edited_df.quantidade * edited_df.valor).sum()
            total_original = cupom_data['nota_entrada'].total_nota_entrada
            diferenca = round(total_calc - total_original, 2)

            col1, col2, col3 = st.columns(3)
            col1.metric("**Total Original**", format_brl(total_original))
            col2.metric("**Total Calculado**", format_brl(total_calc), delta=f"{format_brl(diferenca)}", delta_color='off')
            if diferenca != 0:
                delta_pct = (diferenca / total_calc) * 100 if total_calc != 0 else 0
                col3.metric("**Diferença**", format_brl(diferenca), delta=f"{delta_pct:.2f}%", delta_color='normal')
            else:
                col3.metric("**Status**", "✅ Correto", delta="0%", delta_color='off')

            # 💾 Botões
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("💾 Salvar no Banco de Dados", type="primary", use_container_width=True):
                    edited_df.dropna(how='all', inplace=True, ignore_index=True)
                    self._save_cupom_to_database(cupom_data, edited_df, st.session_state.get("selected_fornecedor_id"))
            with col2:
                if st.button("🔄 Capturar Novo Cupom", use_container_width=True):
                    self._reset_to_capture()
        else:
            st.error("❌ Nenhum item foi identificado. Adicione pelo menos um item antes de salvar.")


    @st.dialog("Processando Cupom", width="medium")
    def _display_processing_dialog(self):
        """Dialog de processamento com status melhorado"""
        # Usa st.status para feedback estruturado
        with st.status("✨ Analisando cupom com IA...", expanded=True) as status:
            try:
                image = st.session_state.cupom_image

                # Etapa 1: Extração de dados
                st.write("🔄 Extraindo dados do cupom...")
                cupom_data = self.gemini_service.extract_cupom_data(image)

                if not cupom_data:
                    st.error("❌ Não foi possível extrair dados do cupom.")
                    status.update(label="❌ Falha na extração", state="error")
                    return

                st.write("✅ Dados extraídos com sucesso!")
                st.session_state.cupom_data = cupom_data

                # Etapa 2: Identificação do fornecedor (otimizada)
                st.write("🔍 Identificando fornecedor...")
                fornecedor_nome = cupom_data['fornecedor'].nome
                fornecedor_cnpj = cupom_data['fornecedor'].cnpj

                # ✅ OTIMIZAÇÃO: Uma única busca otimizada
                fornecedor_encontrado = self._find_existing_fornecedor_optimized(fornecedor_nome, fornecedor_cnpj)

                if fornecedor_encontrado:
                    st.write(f"✅ Fornecedor identificado: {fornecedor_encontrado.nome}")
                    st.session_state.selected_fornecedor_id = fornecedor_encontrado.id
                    # ✅ Armazena o objeto do fornecedor também
                    st.session_state.selected_fornecedor_obj = fornecedor_encontrado
                else:
                    st.write("⚠️ Fornecedor não identificado automaticamente")
                    st.session_state.selected_fornecedor_id = None

                # Sempre redireciona para a tela de seleção de fornecedor (com sugestão automática, se houver)
                status.update(label="✅ Processamento concluído - Seleção de fornecedor", state="complete")
                st.session_state.cupom_state = 'fornecedor_selection'

                # Auto-redireciona após 1 segundo
                import time
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"❌ Erro ao processar cupom: {str(e)}")
                status.update(label="❌ Erro no processamento", state="error")

                if st.button("🔄 Tentar Novamente"):
                    st.session_state.cupom_state = 'capture'
                    st.rerun()

    def _find_existing_fornecedor_optimized(self, fornecedor_nome, fornecedor_cnpj):
        """
        ✅ VERSÃO OTIMIZADA: Busca fornecedor com cache inteligente
        Evita múltiplas consultas ao banco de dados
        """
        # Primeira tentativa: busca por CNPJ (consulta direta ao banco)
        if fornecedor_cnpj:
            fornecedor_encontrado = self.fornecedor_service.buscar_fornecedor_por_cnpj(fornecedor_cnpj)
            if fornecedor_encontrado:
                return fornecedor_encontrado
        
        # Segunda tentativa: busca por nome similar usando cache
        if fornecedor_nome != 'Fornecedor não identificado':
            fornecedores = self._get_fornecedores_cached()  # ✅ Uma única consulta com cache
            for f in fornecedores:
                if self._similarity_match(fornecedor_nome.lower(), f.nome.lower()) > 0.8:
                    return f
        
        return None

    @st.dialog("Seleção de Fornecedor", width="large")
    def _display_fornecedor_selection_dialog(self):
        """
        ✅ OTIMIZAÇÃO: Dialog otimizado para seleção de fornecedor
        Usa cache para evitar múltiplas consultas
        """
        cupom_data = st.session_state.cupom_data

        # Mostra dados detectados
        with st.container(border=True):
            st.write("**Dados detectados no cupom:**")
            col1, col2 = st.columns(2)
            col1.write(f"**Nome:** {cupom_data['fornecedor'].nome}")
            cnpj_display = format_cnpj(cupom_data['fornecedor'].cnpj) if cupom_data['fornecedor'].cnpj else "Não identificado"
            col2.write(f"**CNPJ:** {cnpj_display}")

        # ✅ OTIMIZAÇÃO: Reutiliza fornecedor já encontrado ou busca com cache
        fornecedor_sugerido = None
        if st.session_state.get("selected_fornecedor_obj"):
            # Reutiliza o fornecedor já encontrado no processamento
            fornecedor_sugerido = st.session_state.selected_fornecedor_obj
        else:
            # Busca novamente apenas se necessário
            fornecedor_nome = cupom_data['fornecedor'].nome
            fornecedor_cnpj = cupom_data['fornecedor'].cnpj
            fornecedor_sugerido = self._find_existing_fornecedor_optimized(fornecedor_nome, fornecedor_cnpj)

        # ✅ OTIMIZAÇÃO: Prepara opções usando cache
        fornecedores = self._get_fornecedores_cached()  # Usa cache
        fornecedor_options = {f.id: f"{f.nome} - {format_cnpj(f.cnpj) if f.cnpj else 'Sem CNPJ'}" for f in fornecedores}

        default_index = None
        if fornecedor_sugerido:
            try:
                default_index = list(fornecedor_options.keys()).index(fornecedor_sugerido.id)
            except ValueError:
                default_index = None

        if fornecedor_sugerido:
            st.success(f"💡 **Sugestão automática:** {fornecedor_sugerido.nome} foi pré-selecionado com base nos dados do cupom")
        else:
            st.info("ℹ️ Nenhuma sugestão automática disponível - escolha manualmente ou continue sem seleção")

        selected_fornecedor_id = st.selectbox(
            "Selecione um fornecedor cadastrado:",
            options=list(fornecedor_options.keys()),
            format_func=lambda x: fornecedor_options[x],
            index=default_index,
            placeholder="Selecione para ativar matching inteligente"
        )

        if selected_fornecedor_id:
            fornecedor_selecionado = next((f for f in fornecedores if f.id == selected_fornecedor_id), None)
            if fornecedor_sugerido and selected_fornecedor_id == fornecedor_sugerido.id:
                st.info(f"🎯 **Fornecedor sugerido:** {fornecedor_selecionado.nome}")
            else:
                st.info(f"👤 **Fornecedor selecionado:** {fornecedor_selecionado.nome}")

        # Botões
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🎯 Confirmar e Continuar", type="primary", use_container_width=True, disabled=not selected_fornecedor_id):
                if selected_fornecedor_id:
                    st.session_state.selected_fornecedor_id = selected_fornecedor_id
                    st.session_state.selected_fornecedor_obj = fornecedor_selecionado  # ⬅️ armazenar objeto completo

                    cupom_data_with_matching = self.gemini_service.add_matching_suggestions(
                        st.session_state.cupom_data,
                        selected_fornecedor_id,
                        self.nota_entrada_service
                    )
                    st.session_state.cupom_data = cupom_data_with_matching

                    if 'matching_suggestions' in cupom_data_with_matching and cupom_data_with_matching['matching_suggestions']:
                        st.session_state.cupom_state = 'matching_review'
                    else:
                        st.session_state.cupom_state = 'data_edit'
                    st.rerun()

        with col2:
            if st.button("➡️ Continuar sem Matching", use_container_width=True):
                st.session_state.selected_fornecedor_id = None
                st.session_state.selected_fornecedor_obj = None
                st.session_state.cupom_state = 'data_edit'
                st.rerun()

        with col3:
            if st.button("🔄 Nova Captura", use_container_width=True):
                self._reset_to_capture()


    def _similarity_match(self, str1, str2):
        """Calcula similaridade entre duas strings"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()

    def _save_cupom_to_database(self, cupom_data, edited_df, selected_fornecedor_id=None):
        """
        ✅ OTIMIZAÇÃO: Salva os dados com menos consultas ao banco
        """
        try:
            # Verificar se o fornecedor já existe no banco de dados
            fornecedor = None
            
            # ✅ OTIMIZAÇÃO: Reutiliza fornecedor já carregado
            if selected_fornecedor_id and st.session_state.get("selected_fornecedor_obj"):
                fornecedor = st.session_state.selected_fornecedor_obj
                message_handler.add_message(
                    MessageType.INFO,
                    f"Usando fornecedor pré-selecionado: {fornecedor.nome}"
                )
            elif selected_fornecedor_id:
                # Busca apenas se não tiver no cache
                fornecedor = self.fornecedor_service.buscar_fornecedor_por_id(selected_fornecedor_id)
                message_handler.add_message(
                    MessageType.INFO,
                    f"Usando fornecedor pré-selecionado: {fornecedor.nome}"
                )
            else:
                # Caso contrário, procura por CNPJ
                if cupom_data['fornecedor'].cnpj:
                    fornecedor = self.fornecedor_service.buscar_fornecedor_por_cnpj(cupom_data['fornecedor'].cnpj)
            
            if not fornecedor:
                # Salva fornecedor
                fornecedor = self.fornecedor_service.criar_fornecedor(cupom_data['fornecedor'])
                # ✅ OTIMIZAÇÃO: Invalida cache após criação
                self._invalidate_fornecedores_cache()
                message_handler.add_message(
                    MessageType.SUCCESS,
                    f"Fornecedor {cupom_data['fornecedor'].nome} cadastrado com sucesso!"
                )
                
            # Atualiza NotaEntrada com o ID do fornecedor
            cupom_data['nota_entrada'].fornecedor_id = fornecedor.id
            cupom_data['nota_entrada'].url = "CUPOM_NAO_FISCAL_IA"  # Identificador especial
            if not cupom_data['nota_entrada'].chave_acesso:
                cupom_data['nota_entrada'].chave_acesso = None
            
            # Salva nota e itens atomicamente
            self.nota_entrada_service.criar_nota_entrada_atomica(
                cupom_data['nota_entrada'],
                edited_df.to_dict('records')
            )
            
            # Mensagem de sucesso com informações de matching
            success_msg = f"Cupom não fiscal processado e salvo com sucesso! Total: {format_brl(cupom_data['nota_entrada'].total_nota_entrada)}"
            if 'matching_info' in cupom_data:
                matching_info = cupom_data['matching_info']
                if matching_info.get('itens_matchados', 0) > 0:
                    success_msg += f" | {matching_info['itens_matchados']} itens padronizados"
            
            message_handler.add_message(
                MessageType.SUCCESS,
                success_msg
            )
            
            # Reset para nova captura
            self._reset_to_capture()
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar cupom: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                f"Erro ao salvar cupom: {str(e)}"
            )

    def _reset_to_capture(self):
        """Reseta completamente para o estado de captura"""
        # Limpa todos os estados relacionados ao cupom
        st.session_state.cupom_state = 'capture'
        st.session_state.cupom_data = None
        st.session_state.selected_fornecedor_id = None
        st.session_state.selected_fornecedor_obj = None  # ✅ Limpa objeto também
        
        # Clear the file uploader and camera input
        if "file_uploader_key" not in st.session_state:
            st.session_state["file_uploader_key"] = 0
        if "cupom_camera_key" not in st.session_state:
            st.session_state["cupom_camera_key"] = 0
        # Limpa a imagem armazenada
        if 'cupom_image' in st.session_state:
            del st.session_state.cupom_image
        
        st.session_state["file_uploader_key"] += 1
        st.session_state["cupom_camera_key"] += 1
        
        # Limpa o estado das sugestões aprovadas
        self._clear_matching_state()
        
        # ✅ OTIMIZAÇÃO: Invalida cache para próxima sessão
        self._invalidate_fornecedores_cache()
        
        st.rerun()

    def _clear_matching_state(self):
        """Limpa o estado das aprovações de matching"""
        if 'matching_approval_state' in st.session_state:
            del st.session_state.matching_approval_state

    def _add_camera_styles(self):
        """Adiciona estilos CSS para a câmera"""
        st.markdown(
            """
            <style>
            [data-testid="stCameraInput"] video {
                border: 4px solid #1f77b4;
                border-radius: 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
                margin: auto;
                display: block;
            }
            
            [data-testid="stCameraInput"] button {
                background-color: #1f77b4;
                color: white;
                border: none;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                margin: 10px auto;
                display: block;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            [data-testid="stCameraInput"] button:hover {
                background-color: #0d5aa7;
                transform: scale(1.05);
                transition: all 0.2s;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )