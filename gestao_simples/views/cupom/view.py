# views/cupom/view.py
import streamlit as st
from PIL import Image
import pandas as pd
from services.gemini_service import GeminiService
from services.fornecedor_service import FornecedorService
from services.nota_entrada_service import NotaEntradaService
from services.item_nota_entrada_service import ItemNotaEntradaService
from utils.message_handler import message_handler, MessageType
from utils.format import format_brl, format_cnpj
from datetime import datetime
from utils.validacoes import validar_fornecedor, validar_nota_entrada, validar_item_nota_entrada, ValidationError

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
        """Dialog para exibir os dados extraídos do cupom para revisão e edição com validação"""
        cupom_data = st.session_state.cupom_data
        selected_fornecedor = st.session_state.get("selected_fornecedor_obj", cupom_data['fornecedor'])

        st.info("⚠️ **Importante:** Revise todos os dados extraídos pela IA antes de salvar. A precisão pode variar dependendo da qualidade da imagem.")

        # Inicializa estado de validação se não existir
        if 'validation_errors' not in st.session_state:
            st.session_state.validation_errors = {}

        # Fornecedor
        st.subheader("🏪 Dados do Fornecedor:")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            col1.write(f"**Nome:** {selected_fornecedor.nome}")
            cnpj_display = format_cnpj(selected_fornecedor.cnpj) if selected_fornecedor.cnpj else "Não informado"
            col2.write(f"**CNPJ:** {cnpj_display}")

            # Validação do fornecedor em tempo real
            try:
                validar_fornecedor(selected_fornecedor)
                if 'fornecedor' in st.session_state.validation_errors:
                    del st.session_state.validation_errors['fornecedor']
            except ValidationError as e:
                st.session_state.validation_errors['fornecedor'] = e.errors
                for error in e.errors:
                    st.error(f"❌ Fornecedor: {error}")

        # Nota
        st.subheader("📄 Dados da Nota:")
        with st.container(border=True):
            if cupom_data['nota_entrada'].chave_acesso:
                cupom_data['nota_entrada'].chave_acesso = st.text_input(
                    "Chave de Acesso",
                    value=cupom_data['nota_entrada'].chave_acesso,
                    help="Chave de acesso da nota fiscal, se disponível",
                    key="chave_acesso_input"
                )
            
            col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
            cupom_data['nota_entrada'].modelo = col1.text_input(
                "Modelo", 
                value=cupom_data['nota_entrada'].modelo,
                key="modelo_input"
            )
            
            cupom_data['nota_entrada'].numero_nota_entrada = col2.text_input(
                "Número da Nota", 
                value=cupom_data['nota_entrada'].numero_nota_entrada,
                key="numero_nota_input"
            )
            
            cupom_data['nota_entrada'].serie_nota_entrada = col3.text_input(
                "Série da Nota", 
                value=cupom_data['nota_entrada'].serie_nota_entrada,
                key="serie_nota_input"
            )

            # Input de data/hora com segundos
            datetime_str = col4.text_input(
                "Data de Emissão",
                value=cupom_data['nota_entrada'].data_emissao.strftime("%d/%m/%Y %H:%M:%S"),
                help="Data e hora de emissão da nota fiscal. Use o formato DD/MM/AAAA HH:MM:SS",
                key="data_emissao_input"
            )

            # Validação e conversão da data
            try:
                if datetime_str != cupom_data['nota_entrada'].data_emissao.strftime("%d/%m/%Y %H:%M:%S"):
                    cupom_data['nota_entrada'].data_emissao = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                st.error(f"❌ Formato de data inválido. Use DD/MM/AAAA HH:MM:SS. \nEx. {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

            # Validação da nota de entrada
            nota_errors = []
            
            # Validações específicas dos campos da nota
            if not cupom_data['nota_entrada'].modelo or cupom_data['nota_entrada'].modelo.strip() == "":
                nota_errors.append("Modelo é obrigatório")
                
            if not cupom_data['nota_entrada'].numero_nota_entrada or cupom_data['nota_entrada'].numero_nota_entrada.strip() == "":
                nota_errors.append("Número da Nota é obrigatório")
            else:
                try:
                    numero = int(cupom_data['nota_entrada'].numero_nota_entrada)
                    if numero > 999999999:
                        nota_errors.append("O valor máximo permitido para o Número da Nota é 999.999.999")
                except (ValueError, TypeError):
                    nota_errors.append("Número da Nota deve ser um número válido")
                    
            if not cupom_data['nota_entrada'].serie_nota_entrada or cupom_data['nota_entrada'].serie_nota_entrada.strip() == "":
                nota_errors.append("Série da Nota é obrigatória")
                
            if not cupom_data['nota_entrada'].data_emissao:
                nota_errors.append("Data de Emissão é obrigatória")
            
            try:
                # Temporariamente define o fornecedor_id para validação
                original_fornecedor_id = cupom_data['nota_entrada'].fornecedor_id
                cupom_data['nota_entrada'].fornecedor_id = selected_fornecedor.id if hasattr(selected_fornecedor, 'id') else 1
                
                validar_nota_entrada(cupom_data['nota_entrada'])
                
                # Restaura o valor original
                cupom_data['nota_entrada'].fornecedor_id = original_fornecedor_id
                
            except ValidationError as e:
                nota_errors.extend(e.errors)
            
            # Exibe erros da nota
            if nota_errors:
                st.session_state.validation_errors['nota_entrada'] = nota_errors
                for error in nota_errors:
                    st.error(f"❌ Nota: {error}")
            else:
                if 'nota_entrada' in st.session_state.validation_errors:
                    del st.session_state.validation_errors['nota_entrada']

        # Itens
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

        # Validação dos itens
        itens_errors = []
        if not edited_df.empty:
            for idx, row in edited_df.iterrows():
                item_errors = []
                
                # Validação da descrição
                if not row.get('descricao') or str(row.get('descricao')).strip() == "" or pd.isna(row.get('descricao')):
                    item_errors.append("Descrição é obrigatória")
                
                # Validação da quantidade
                quantidade = row.get('quantidade')
                if pd.isna(quantidade) or quantidade is None:
                    item_errors.append("Quantidade é obrigatória")
                else:
                    try:
                        quantidade_float = float(quantidade)
                        if quantidade_float <= 0:
                            item_errors.append("Quantidade deve ser maior que zero")
                    except (ValueError, TypeError):
                        item_errors.append("Quantidade deve ser um número válido")
                
                # Validação do valor
                valor = row.get('valor')
                if pd.isna(valor) or valor is None:
                    item_errors.append("Valor é obrigatório")
                else:
                    try:
                        valor_float = float(valor)
                        if valor_float <= 0:
                            item_errors.append("Valor deve ser maior que zero")
                    except (ValueError, TypeError):
                        item_errors.append("Valor deve ser um número válido")
                
                # Validação da unidade de medida
                if not row.get('unidade_medida') or str(row.get('unidade_medida')).strip() == "" or pd.isna(row.get('unidade_medida')):
                    item_errors.append("Unidade de medida é obrigatória")
                
                # Validação do código do produto fornecedor
                if not row.get('codigo_produto_fornecedor') or str(row.get('codigo_produto_fornecedor')).strip() == "" or pd.isna(row.get('codigo_produto_fornecedor')):
                    item_errors.append("Código do produto fornecedor é obrigatório")
                
                # Se houver erros neste item, adiciona à lista geral
                if item_errors:
                    for error in item_errors:
                        itens_errors.append(f"Item {idx + 1}: {error}")
                
                # Também usa a validação original como backup
                try:
                    item_temp = type('Item', (), {
                        'descricao': row.get('descricao', ''),
                        'quantidade': row.get('quantidade', 0),
                        'valor': row.get('valor', 0),
                        'unidade_medida': row.get('unidade_medida', ''),
                        'codigo_produto_fornecedor': row.get('codigo_produto_fornecedor', '')
                    })()
                    
                    validar_item_nota_entrada(item_temp)
                except ValidationError as e:
                    for error in e.errors:
                        error_msg = f"Item {idx + 1}: {error}"
                        if error_msg not in itens_errors:  # Evita duplicatas
                            itens_errors.append(error_msg)

        # Exibe erros dos itens
        if itens_errors:
            st.session_state.validation_errors['itens'] = itens_errors
            st.error("❌ **Erros nos itens:**")
            for error in itens_errors:
                st.error(f"• {error}")
        else:
            if 'itens' in st.session_state.validation_errors:
                del st.session_state.validation_errors['itens']

        # Validações e cálculos
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

            # Verifica se há erros de validação
            has_validation_errors = bool(st.session_state.validation_errors)
            
            # Exibe resumo dos erros se houver
            if has_validation_errors:
                st.error("❌ **Corrija os erros acima antes de salvar:**")
                total_errors = sum(len(errors) if isinstance(errors, list) else 1 
                                for errors in st.session_state.validation_errors.values())
                st.error(f"📊 Total de erros: **{total_errors}**")

            # Botões
            col1, col2 = st.columns([1, 1])
            with col1:
                save_button = st.button(
                    "💾 Salvar no Banco de Dados", 
                    type="primary", 
                    use_container_width=True,
                    disabled=has_validation_errors  # Desabilita se houver erros
                )
                
                if save_button:
                    if not has_validation_errors:
                        edited_df.dropna(how='all', inplace=True, ignore_index=True)
                        self._save_cupom_to_database(cupom_data, edited_df, st.session_state.get("selected_fornecedor_id"))
                    else:
                        st.error("❌ Corrija todos os erros de validação antes de salvar!")
                        
            with col2:
                if st.button("🔄 Capturar Novo Cupom", use_container_width=True):
                    self._reset_to_capture()
        else:
            st.error("❌ Nenhum item foi identificado. Adicione pelo menos um item antes de salvar.")
            st.session_state.validation_errors['itens'] = ["Nenhum item identificado"]


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

                # Uma única busca otimizada
                fornecedor_encontrado = self._find_existing_fornecedor_optimized(fornecedor_nome, fornecedor_cnpj)

                if fornecedor_encontrado:
                    st.write(f"✅ Fornecedor identificado: {fornecedor_encontrado.nome}")
                    st.session_state.selected_fornecedor_id = fornecedor_encontrado.id
                    # Armazena o objeto do fornecedor também
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
        Busca fornecedor com cache inteligente
        Evita múltiplas consultas ao banco de dados
        """
        # Primeira tentativa: busca por CNPJ (consulta direta ao banco)
        if fornecedor_cnpj:
            fornecedor_encontrado = self.fornecedor_service.buscar_fornecedor_por_cnpj(fornecedor_cnpj)
            if fornecedor_encontrado:
                return fornecedor_encontrado
        
        # Segunda tentativa: busca por nome similar usando cache
        if fornecedor_nome != 'Fornecedor não identificado':
            fornecedores = self._get_fornecedores_cached()  # Uma única consulta com cache
            for f in fornecedores:
                if fornecedor_nome and f.nome and self._similarity_match(fornecedor_nome.lower(), f.nome.lower()) > 0.8:
                    return f
        
        return None

    @st.dialog("Seleção de Fornecedor", width="large")
    def _display_fornecedor_selection_dialog(self):
        """
        Dialog otimizado para seleção de fornecedor
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

        # Reutiliza fornecedor já encontrado ou busca com cache
        fornecedor_sugerido = None
        if st.session_state.get("selected_fornecedor_obj"):
            # Reutiliza o fornecedor já encontrado no processamento
            fornecedor_sugerido = st.session_state.selected_fornecedor_obj
        else:
            # Busca novamente apenas se necessário
            fornecedor_nome = cupom_data['fornecedor'].nome
            fornecedor_cnpj = cupom_data['fornecedor'].cnpj
            fornecedor_sugerido = self._find_existing_fornecedor_optimized(fornecedor_nome, fornecedor_cnpj)

        # Prepara opções usando cache
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
        Salva os dados com validação completa antes da persistência
        """
        try:
            # VALIDAÇÃO FINAL ANTES DE SALVAR
            validation_errors = []
            
            # Valida fornecedor
            fornecedor = None
            if selected_fornecedor_id and st.session_state.get("selected_fornecedor_obj"):
                fornecedor = st.session_state.selected_fornecedor_obj
            elif selected_fornecedor_id:
                fornecedor = self.fornecedor_service.buscar_fornecedor_por_id(selected_fornecedor_id)
            else:
                if cupom_data['fornecedor'].cnpj:
                    fornecedor = self.fornecedor_service.buscar_fornecedor_por_cnpj(cupom_data['fornecedor'].cnpj)
            
            if not fornecedor:
                try:
                    validar_fornecedor(cupom_data['fornecedor'])
                    fornecedor = self.fornecedor_service.criar_fornecedor(cupom_data['fornecedor'])
                    self._invalidate_fornecedores_cache()
                    message_handler.add_message(
                        MessageType.SUCCESS,
                        f"Fornecedor {cupom_data['fornecedor'].nome} cadastrado com sucesso!"
                    )
                except ValidationError as e:
                    validation_errors.extend([f"Fornecedor: {error}" for error in e.errors])
            
            # Valida nota de entrada
            cupom_data['nota_entrada'].fornecedor_id = fornecedor.id if fornecedor else None
            cupom_data['nota_entrada'].url = "CUPOM_NAO_FISCAL_IA"
            if not cupom_data['nota_entrada'].chave_acesso:
                cupom_data['nota_entrada'].chave_acesso = None
            
            # Validações específicas dos campos da nota
            if not cupom_data['nota_entrada'].modelo or cupom_data['nota_entrada'].modelo.strip() == "":
                validation_errors.append("Nota: Modelo é obrigatório")
                
            if not cupom_data['nota_entrada'].numero_nota_entrada or cupom_data['nota_entrada'].numero_nota_entrada.strip() == "":
                validation_errors.append("Nota: Número da Nota é obrigatório")
            else:
                try:
                    numero = int(cupom_data['nota_entrada'].numero_nota_entrada)
                    if numero > 999999999:
                        validation_errors.append("Nota: O valor máximo permitido para o Número da Nota é 999.999.999")
                except (ValueError, TypeError):
                    validation_errors.append("Nota: Número da Nota deve ser um número válido")
                    
            if not cupom_data['nota_entrada'].serie_nota_entrada or cupom_data['nota_entrada'].serie_nota_entrada.strip() == "":
                validation_errors.append("Nota: Série da Nota é obrigatória")
                
            if not cupom_data['nota_entrada'].data_emissao:
                validation_errors.append("Nota: Data de Emissão é obrigatória")
                
            try:
                validar_nota_entrada(cupom_data['nota_entrada'])
            except ValidationError as e:
                validation_errors.extend([f"Nota: {error}" for error in e.errors])
            
            # Valida todos os itens
            itens_validados = []
            for idx, item_dict in enumerate(edited_df.to_dict('records')):
                item_errors = []
                
                # Validação detalhada de cada campo
                if not item_dict.get('descricao') or str(item_dict.get('descricao')).strip() == "" or pd.isna(item_dict.get('descricao')):
                    item_errors.append("Descrição é obrigatória")
                
                # Validação da quantidade
                quantidade = item_dict.get('quantidade')
                if pd.isna(quantidade) or quantidade is None:
                    item_errors.append("Quantidade é obrigatória")
                else:
                    try:
                        quantidade_float = float(quantidade)
                        if quantidade_float <= 0:
                            item_errors.append("Quantidade deve ser maior que zero")
                    except (ValueError, TypeError):
                        item_errors.append("Quantidade deve ser um número válido")
                
                # Validação do valor
                valor = item_dict.get('valor')
                if pd.isna(valor) or valor is None:
                    item_errors.append("Valor é obrigatório")
                else:
                    try:
                        valor_float = float(valor)
                        if valor_float <= 0:
                            item_errors.append("Valor deve ser maior que zero")
                    except (ValueError, TypeError):
                        item_errors.append("Valor deve ser um número válido")
                
                # Validação da unidade de medida
                if not item_dict.get('unidade_medida') or str(item_dict.get('unidade_medida')).strip() == "" or pd.isna(item_dict.get('unidade_medida')):
                    item_errors.append("Unidade de medida é obrigatória")
                
                # Validação do código do produto fornecedor
                if not item_dict.get('codigo_produto_fornecedor') or str(item_dict.get('codigo_produto_fornecedor')).strip() == "" or pd.isna(item_dict.get('codigo_produto_fornecedor')):
                    item_errors.append("Código do produto fornecedor é obrigatório")
                
                # Se houver erros, adiciona à lista de erros
                if item_errors:
                    for error in item_errors:
                        validation_errors.append(f"Item {idx + 1}: {error}")
                else:
                    # Só adiciona à lista de validados se não houver erros
                    itens_validados.append(item_dict)
                
                # Também usa a validação original como backup
                try:
                    item_temp = type('Item', (), item_dict)()
                    validar_item_nota_entrada(item_temp)
                except ValidationError as e:
                    for error in e.errors:
                        error_msg = f"Item {idx + 1}: {error}"
                        if error_msg not in validation_errors:  # Evita duplicatas
                            validation_errors.append(error_msg)
            
            # Se houver erros de validação, não salva
            if validation_errors:
                st.error("❌ **Erros de validação encontrados:**")
                for error in validation_errors:
                    st.error(f"• {error}")
                message_handler.add_message(
                    MessageType.ERROR,
                    f"Não foi possível salvar devido a {len(validation_errors)} erro(s) de validação"
                )
                return
            
            # Se chegou até aqui, todos os dados estão válidos - prossegue com o salvamento
            # Se não havia itens validados devido a erros, usa todos os itens do DataFrame
            if not itens_validados and not validation_errors:
                itens_validados = edited_df.to_dict('records')
            
            # Atualiza a nota de entrada com o total calculado
            total_nota_entrada = float((edited_df['quantidade'] * edited_df['valor']).sum())
            cupom_data['nota_entrada'].total_nota_entrada = total_nota_entrada

            self.nota_entrada_service.criar_nota_entrada_atomica(
                cupom_data['nota_entrada'],
                itens_validados
            )
            
            # Mensagem de sucesso
            success_msg = f"Cupom não fiscal processado e salvo com sucesso! Total: {format_brl(cupom_data['nota_entrada'].total_nota_entrada)}"
            if 'matching_info' in cupom_data:
                matching_info = cupom_data['matching_info']
                if matching_info.get('itens_matchados', 0) > 0:
                    success_msg += f" | {matching_info['itens_matchados']} itens padronizados"
            
            message_handler.add_message(MessageType.SUCCESS, success_msg)
            
            # Limpa erros de validação e reseta para nova captura
            if 'validation_errors' in st.session_state:
                del st.session_state.validation_errors
            self._reset_to_capture()
            
        except Exception as e:
            error_msg = f"Erro inesperado ao salvar cupom: {str(e)}"
            st.error(f"❌ {error_msg}")
            message_handler.add_message(MessageType.ERROR, error_msg)

    def _reset_to_capture(self):
        """Reseta completamente para o estado de captura"""
        # Limpa todos os estados relacionados ao cupom
        st.session_state.cupom_state = 'capture'
        st.session_state.cupom_data = None
        st.session_state.selected_fornecedor_id = None
        st.session_state.selected_fornecedor_obj = None
        
        # Limpa erros de validação
        if 'validation_errors' in st.session_state:
            del st.session_state.validation_errors
        
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
        
        # Invalida cache para próxima sessão
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