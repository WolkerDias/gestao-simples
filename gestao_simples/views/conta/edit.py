# views/conta/edit.py
import streamlit as st
from models.conta import Conta
from services.conta_service import ContaService

def show_edit_conta(conta: Conta):
    """Exibe o formulário de edição de conta"""
    if not conta:
        st.error("Conta não encontrada")
        return
    
    conta_service = ContaService()
    
    st.header("✏️ Editar Conta")
    st.subheader(f"Editando: {conta.nome}")
    
    with st.form("form_edit_conta"):
        nome = st.text_input(
            "Nome*", 
            value=conta.nome,
            placeholder="Ex: Banco X, Carteira, Poupança...",
            max_chars=100,
            help="Nome da conta (máximo 100 caracteres)"
        )
        
        tipo = st.selectbox(
            "Tipo*",
            options=["Banco", "Carteira", "Poupança", "Investimento", "Outro"],
            index=["Banco", "Carteira", "Poupança", "Investimento", "Outro"].index(conta.tipo),
            help="Selecione o tipo da conta"
        )
        
        saldo_inicial = st.number_input(
            "Saldo Inicial (R$)*", 
            min_value=0.00, 
            value=float(conta.saldo_inicial),
            format="%.2f",
            help="Saldo inicial da conta em reais"
        )
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            submit_button = st.form_submit_button(
                "💾 Salvar Alterações", 
                use_container_width=True,
                type="primary"
            )
            
        with col_btn2:
            cancel_button = st.form_submit_button(
                "❌ Cancelar", 
                use_container_width=True
            )
        
        # Processamento do formulário
        if submit_button:
            try:
                # Valida campos obrigatórios
                if not nome.strip():
                    st.error("O nome é obrigatório")
                    return
                
                # Prepara dados para atualização
                dados_atualizacao = {
                    'nome': nome.strip(),
                    'tipo': tipo,
                    'saldo_inicial': saldo_inicial
                }
                
                # Atualiza a conta
                conta_atualizada = conta_service.atualizar_conta(conta.id, dados_atualizacao)
                
                if conta_atualizada:
                    st.success("Conta atualizada com sucesso!")
                    st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao atualizar conta: {str(e)}")
        
        if cancel_button:
            st.rerun()
    
    # Informações adicionais
    st.divider()
    
    with st.expander("ℹ️ Informações da Conta"):
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.write("**ID da Conta:**")
            st.write(conta.id)
            
        with col_info2:
            if hasattr(conta, 'created_at') and conta.created_at:
                st.write("**Data de Criação:**")
                st.write(conta.created_at.strftime('%d/%m/%Y %H:%M'))
        
        if hasattr(conta, 'updated_at') and conta.updated_at:
            st.write("**Última Atualização:**")
            st.write(conta.updated_at.strftime('%d/%m/%Y %H:%M'))