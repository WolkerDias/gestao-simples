# views/auth/list.py
import streamlit as st
import pandas as pd
from utils.message_handler import message_handler, MessageType
from services.auth_service import AuthService
from config.settings import DEFAULT_PASSWORD
from views.auth.register import register_view
from views.auth.view import show_view_usuario
from views.auth.delete import confirm_delete_dialog

class UsuarioListView:
    def __init__(self):
        self.auth_service = AuthService()
        self.render()

    def render(self):
        st.title("📦 Gestão de Usuários")
        message_handler.display_toast_message()        

        # Botões de ação
        columns = st.columns([2, 2, 2, 2], vertical_alignment="center")

        with columns[0]:
            if st.button("Novo Usuário", use_container_width=True, icon=":material/add_circle_outline:", help="Cadastrar novo usuário"):
                register_view()
        # Preparar dados
        usuarios = self.auth_service.listar_usuarios()

        if not usuarios:
            st.info("Nenhum usuario cadastrado")
            return
        
        df_usuarios = pd.DataFrame([{
            'ID': u.id, 
            'Nome': u.nome, 
            'E-mail': u.email,
            'Tipo': "Administrador" if u.is_admin else "Usuário",
            'Ativo': "Sim" if u.ativo else "Não",
        } for u in usuarios])


        # Renderizar DataFrame com seleção
        usuario = st.dataframe(
            df_usuarios,
            use_container_width=True,
            key="data",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
        )
        
        # Ações para linha selecionada
        selected_row = usuario.selection.rows
        if selected_row:
            disabled = False
        else:
            disabled = True

        with columns[1]:
            if st.button("👁️ Detalhes", use_container_width=True, disabled=disabled, help="Selecione um item para ver detalhes"):
                usuario_id = df_usuarios.loc[selected_row]['ID'].values[0]
                usuario = self.auth_service.buscar_usuario_por_id(usuario_id)
                show_view_usuario(usuario)

        with columns[2]:
            with st.popover("Resetar Senha", use_container_width=True, disabled=disabled, help="Selecione um item para alterar a senha", icon="🔑"):
                st.write("**Atenção!**")
                info = st.empty()
                info.warning(f"A nova senha do usuário selecionado será: \n\n**{DEFAULT_PASSWORD}**", icon="⚠️")
                if st.button("Resetar", disabled=disabled, use_container_width=True, type="primary"):
                    try:
                        usuario_id = df_usuarios.loc[selected_row]['ID'].values[0]
                        usuario = self.auth_service.buscar_usuario_por_id(usuario_id)
                        self.auth_service.atualizar_senha(usuario, DEFAULT_PASSWORD)
                        info.success(f"Senha do usuário **{usuario.nome}** resetada para: \n\n{DEFAULT_PASSWORD}", icon="✅")

                    except Exception as e:
                        info.error(f"Erro ao resetar senha: {e}", icon="❌")

        with columns[3]:
            if st.button("🗑️ Excluir", use_container_width=True, disabled=disabled, help="Selecione um item para ver excluir"):
                usuario_id = df_usuarios.loc[selected_row]['ID'].values[0]
                usuario_nome = df_usuarios.loc[selected_row]['Nome'].values[0]
                confirm_delete_dialog(usuario_id, usuario_nome, self.auth_service)
