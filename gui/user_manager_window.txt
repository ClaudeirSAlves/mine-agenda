import tkinter as tk
from tkinter import messagebox, ttk

from config import Config, logger 
from services import UserService # Para interagir com os dados dos usuários
# MainWindow não é importada aqui para evitar ciclos. A referência à janela pai é passada.

class UserManagerWindow:
    def __init__(self, parent_main_window_instance): 
        self.parent_main_window = parent_main_window_instance # Referência à instância da MainWindow
        self.users_data = UserService.load_users() # Carrega os usuários atuais
        
        self.window = tk.Toplevel(parent_main_window_instance.root) 
        self.window.title("Gerenciador de Usuários")
        
        window_width = 700 # Ajustado para melhor visualização
        window_height = 450
        # Centraliza em relação à janela pai (MainWindow)
        parent_x = parent_main_window_instance.root.winfo_x()
        parent_y = parent_main_window_instance.root.winfo_y()
        parent_width = parent_main_window_instance.root.winfo_width()
        parent_height = parent_main_window_instance.root.winfo_height()
        
        center_x = parent_x + (parent_width - window_width) // 2
        center_y = parent_y + (parent_height - window_height) // 2
        self.window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.window.minsize(600, 400)

        self.window.transient(parent_main_window_instance.root) 
        self.window.grab_set() # Torna esta janela modal

        # Tenta definir ícone para a janela (usa o de usuário ou o padrão da app)
        user_icon_path = Config.ICON_USER
        if user_icon_path and user_icon_path.exists():
             try: self.window.iconbitmap(str(user_icon_path))
             except Exception as e: logger.warning(f"Não foi possível carregar o ícone ({user_icon_path}): {e}")
        elif Config.ICON_PATH.exists(): # Fallback para o ícone principal
            try: self.window.iconbitmap(str(Config.ICON_PATH))
            except Exception as e: logger.warning(f"Não foi possível carregar o ícone padrão ({Config.ICON_PATH}): {e}")

        self.setup_ui_elements() # Renomeado para clareza
        self.refresh_user_list_display() # Renomeado

    def setup_ui_elements(self):
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(main_frame, text="Usuários Cadastrados", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))

        self.user_list_treeview = ttk.Treeview(
            list_frame,
            columns=('username', 'level', 'email'),
            show='headings'
        )
        self.user_list_treeview.heading('username', text='Nome de Usuário')
        self.user_list_treeview.heading('level', text='Nível de Acesso')
        self.user_list_treeview.heading('email', text='E-mail')

        self.user_list_treeview.column('username', width=150, anchor=tk.W)
        self.user_list_treeview.column('level', width=100, anchor=tk.W)
        self.user_list_treeview.column('email', width=250, anchor=tk.W, stretch=tk.YES)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.user_list_treeview.yview)
        self.user_list_treeview.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_list_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        button_actions_frame = ttk.Frame(main_frame)
        button_actions_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_actions_frame, text="Novo Usuário", command=self.open_user_form_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_actions_frame, text="Editar Selecionado", command=lambda: self.open_user_form_dialog(edit_mode=True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_actions_frame, text="Alterar Senha", command=self.open_change_password_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_actions_frame, text="Remover Selecionado", command=self.confirm_delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_actions_frame, text="Fechar", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    def refresh_user_list_display(self):
        for item in self.user_list_treeview.get_children():
            self.user_list_treeview.delete(item)
        
        self.users_data = UserService.load_users() # Recarrega para garantir dados atualizados

        for username, user_details_dict in sorted(self.users_data.items()):
            self.user_list_treeview.insert('', 'end', iid=username, values=( # Usa username como iid
                username,
                user_details_dict.get('level', 'operador').capitalize(),
                user_details_dict.get('email', '')
            ))

    def _center_child_dialog(self, child_dialog: tk.Toplevel, width: int, height: int):
        self.window.update_idletasks() # Garante que as dimensões da janela pai (UserManagerWindow) estejam corretas
        parent_x = self.window.winfo_x()
        parent_y = self.window.winfo_y()
        parent_width = self.window.winfo_width()
        parent_height = self.window.winfo_height()
        
        dialog_x = parent_x + (parent_width - width) // 2
        dialog_y = parent_y + (parent_height - height) // 2
        
        child_dialog.geometry(f'{width}x{height}+{dialog_x}+{dialog_y}')
        child_dialog.resizable(False, False)
        child_dialog.transient(self.window) # Define como transiente da janela UserManager
        child_dialog.grab_set() # Torna modal em relação à UserManagerWindow

    def open_user_form_dialog(self, edit_mode: bool = False):
        selected_username: str | None = None
        user_to_edit_data: dict | None = None

        if edit_mode:
            selected_items = self.user_list_treeview.selection()
            if not selected_items:
                messagebox.showwarning("Ação Requerida", "Por favor, selecione um usuário para editar.", parent=self.window)
                return
            selected_username = self.user_list_treeview.item(selected_items[0])['iid'] # iid é o username
            if selected_username not in self.users_data:
                messagebox.showerror("Erro Interno", "Usuário selecionado não encontrado nos dados.", parent=self.window)
                return
            user_to_edit_data = self.users_data[selected_username]
        
        dialog_title = "Editar Usuário" if edit_mode else "Novo Usuário"
        dialog = tk.Toplevel(self.window)
        dialog.title(dialog_title)
        # Altura maior para acomodar todos os campos, incluindo confirmação de senha se novo
        dialog_height = 380 if not edit_mode else 280 
        self._center_child_dialog(dialog, width=450, height=dialog_height)

        form_frame = ttk.Frame(dialog, padding=15)
        form_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Nome de Usuário:").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        username_entry = ttk.Entry(form_frame, width=40)
        username_entry.grid(row=0, column=1, pady=(0,5), sticky=tk.EW)
        if edit_mode and selected_username:
            username_entry.insert(0, selected_username)
            username_entry.config(state=tk.DISABLED) # Não permite editar nome de usuário

        if not edit_mode: # Campos de senha apenas para novo usuário
            ttk.Label(form_frame, text="Senha:").grid(row=1, column=0, sticky=tk.W, pady=5)
            password_entry = ttk.Entry(form_frame, show="*", width=40)
            password_entry.grid(row=1, column=1, pady=5, sticky=tk.EW)

            ttk.Label(form_frame, text="Confirmar Senha:").grid(row=2, column=0, sticky=tk.W, pady=5)
            confirm_password_entry = ttk.Entry(form_frame, show="*", width=40)
            confirm_password_entry.grid(row=2, column=1, pady=5, sticky=tk.EW)
            current_row = 3
        else:
            current_row = 1 # Pula campos de senha para edição (senha é alterada em diálogo separado)

        ttk.Label(form_frame, text="Nível de Acesso:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
        level_var = tk.StringVar(value=user_to_edit_data['level'] if edit_mode and user_to_edit_data else "operador")
        level_radio_frame = ttk.Frame(form_frame)
        radio_operador = ttk.Radiobutton(level_radio_frame, text="Operador", variable=level_var, value="operador")
        radio_admin = ttk.Radiobutton(level_radio_frame, text="Administrador", variable=level_var, value="admin")
        radio_operador.pack(side=tk.LEFT, padx=(0,10))
        radio_admin.pack(side=tk.LEFT)
        level_radio_frame.grid(row=current_row, column=1, pady=5, sticky=tk.W)
        current_row += 1
        
        # Impede rebaixar o admin principal ou se auto-rebaixar se for o único admin
        if edit_mode and selected_username == 'admin':
            radio_operador.config(state=tk.DISABLED)
            level_var.set('admin')


        ttk.Label(form_frame, text="E-mail:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
        email_entry = ttk.Entry(form_frame, width=40)
        email_entry.grid(row=current_row, column=1, pady=5, sticky=tk.EW)
        if edit_mode and user_to_edit_data:
            email_entry.insert(0, user_to_edit_data.get('email', ''))
        current_row += 1

        form_frame.columnconfigure(1, weight=1) # Coluna dos entries expande

        action_button_frame = ttk.Frame(form_frame)
        action_button_frame.grid(row=current_row, column=0, columnspan=2, pady=(15,0), sticky=tk.EW)

        def on_save():
            username = username_entry.get().strip()
            level = level_var.get()
            email = email_entry.get().strip()

            if not username:
                messagebox.showerror("Validação", "O nome de usuário é obrigatório.", parent=dialog)
                return
            
            if edit_mode: # Edição de usuário existente
                if not selected_username or selected_username not in self.users_data: # Sanity check
                    messagebox.showerror("Erro Interno", "Usuário para edição não identificado.", parent=dialog)
                    return
                
                # Não permitir que o admin principal seja rebaixado (dupla verificação)
                if selected_username == 'admin' and level != 'admin':
                    messagebox.showerror("Restrição", "O usuário 'admin' principal não pode ser rebaixado.", parent=dialog)
                    level_var.set('admin') # Restaura
                    return

                self.users_data[selected_username]['level'] = level
                self.users_data[selected_username]['email'] = email
                log_message = f"Usuário '{selected_username}' atualizado."
            
            else: # Novo usuário
                password = password_entry.get() # Não usa strip() em senhas
                confirm_password = confirm_password_entry.get()

                if not password:
                    messagebox.showerror("Validação", "A senha é obrigatória para novos usuários.", parent=dialog)
                    return
                if password != confirm_password:
                    messagebox.showerror("Validação", "As senhas não coincidem.", parent=dialog)
                    return
                if username in self.users_data:
                    messagebox.showerror("Validação", f"O nome de usuário '{username}' já existe.", parent=dialog)
                    return
                
                self.users_data[username] = {
                    'password_hash': UserService.hash_password(password),
                    'level': level,
                    'email': email
                }
                log_message = f"Novo usuário '{username}' criado."

            try:
                UserService.save_users(self.users_data)
                self.refresh_user_list_display() # Atualiza a lista na janela UserManager
                logger.info(f"{log_message} (Operador: {self.parent_main_window.username})")
                dialog.destroy()
            except Exception as e_save:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados do usuário: {e_save}", parent=dialog)
                logger.error(f"Erro ao salvar dados do usuário {username}: {e_save}", exc_info=True)

        ttk.Button(action_button_frame, text="Salvar", command=on_save).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)
        
        if not edit_mode: username_entry.focus_set()
        else: email_entry.focus_set() # Ou o primeiro campo editável

        dialog.wait_window()

    def open_change_password_dialog(self):
        selected_items = self.user_list_treeview.selection()
        if not selected_items:
            messagebox.showwarning("Ação Requerida", "Selecione um usuário para alterar a senha.", parent=self.window)
            return
        
        username_to_change_pass = self.user_list_treeview.item(selected_items[0])['iid']
        if username_to_change_pass not in self.users_data: # Sanity check
            messagebox.showerror("Erro Interno", "Usuário selecionado não encontrado.", parent=self.window)
            return

        dialog = tk.Toplevel(self.window)
        dialog.title(f"Alterar Senha para: {username_to_change_pass}")
        self._center_child_dialog(dialog, width=400, height=250)

        form_frame = ttk.Frame(dialog, padding=15)
        form_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Nova Senha:").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        new_password_entry = ttk.Entry(form_frame, show="*", width=35)
        new_password_entry.grid(row=0, column=1, pady=(0,5), sticky=tk.EW)

        ttk.Label(form_frame, text="Confirmar Nova Senha:").grid(row=1, column=0, sticky=tk.W, pady=5)
        confirm_new_password_entry = ttk.Entry(form_frame, show="*", width=35)
        confirm_new_password_entry.grid(row=1, column=1, pady=5, sticky=tk.EW)
        
        form_frame.columnconfigure(1, weight=1)

        action_button_frame = ttk.Frame(form_frame)
        action_button_frame.grid(row=2, column=0, columnspan=2, pady=(15,0), sticky=tk.EW)

        def on_save_password():
            new_password = new_password_entry.get()
            confirm_new_password = confirm_new_password_entry.get()

            if not new_password:
                messagebox.showerror("Validação", "A nova senha não pode estar vazia.", parent=dialog)
                return
            if new_password != confirm_new_password:
                messagebox.showerror("Validação", "As senhas digitadas não coincidem.", parent=dialog)
                return
            
            self.users_data[username_to_change_pass]['password_hash'] = UserService.hash_password(new_password)
            try:
                UserService.save_users(self.users_data)
                logger.info(f"Senha do usuário '{username_to_change_pass}' alterada. (Operador: {self.parent_main_window.username})")
                messagebox.showinfo("Sucesso", "Senha alterada com sucesso!", parent=dialog)
                dialog.destroy()
            except Exception as e_save:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível alterar a senha: {e_save}", parent=dialog)
                logger.error(f"Erro ao alterar senha do usuário {username_to_change_pass}: {e_save}", exc_info=True)

        ttk.Button(action_button_frame, text="Salvar Nova Senha", command=on_save_password).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)
        
        new_password_entry.focus_set()
        dialog.wait_window()

    def confirm_delete_user(self):
        selected_items = self.user_list_treeview.selection()
        if not selected_items:
            messagebox.showwarning("Ação Requerida", "Selecione um usuário para remover.", parent=self.window)
            return
        
        username_to_delete = self.user_list_treeview.item(selected_items[0])['iid']

        if username_to_delete == 'admin': # Restrição fundamental
            messagebox.showerror("Operação Não Permitida", "O usuário 'admin' principal não pode ser removido.", parent=self.window)
            return
        if username_to_delete == self.parent_main_window.username: # Autopreservação
            messagebox.showerror("Operação Não Permitida", "Você não pode remover seu próprio usuário enquanto estiver logado.", parent=self.window)
            return
        
        if messagebox.askyesno("Confirmar Remoção", 
                                f"Tem certeza que deseja remover permanentemente o usuário '{username_to_delete}'?\nEsta ação não pode ser desfeita.", 
                                icon='warning', parent=self.window):
            try:
                del self.users_data[username_to_delete] # Remove do dicionário em memória
                UserService.save_users(self.users_data) # Salva as alterações no arquivo
                self.refresh_user_list_display() # Atualiza a Treeview
                logger.info(f"Usuário '{username_to_delete}' removido. (Operador: {self.parent_main_window.username})")
            except KeyError:
                 messagebox.showerror("Erro Interno", f"Usuário '{username_to_delete}' não encontrado para remoção (pode já ter sido removido).", parent=self.window)
                 logger.warning(f"Tentativa de remover usuário '{username_to_delete}' que não está no dicionário users_data.")
                 self.refresh_user_list_display() # Garante que a lista esteja consistente
            except Exception as e_delete:
                 messagebox.showerror("Erro ao Remover", f"Não foi possível remover o usuário: {e_delete}", parent=self.window)
                 logger.error(f"Erro ao remover o usuário {username_to_delete}: {e_delete}", exc_info=True)
                 self.users_data = UserService.load_users() # Recarrega em caso de falha para manter consistência
                 self.refresh_user_list_display()