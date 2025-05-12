# gui/main_window.py
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, date # Adicionado date para comparação de datas
import os
import sys
import webbrowser
import threading
import subprocess
import shutil
from pathlib import Path

from config import Config, logger, HAS_PIL, ASSETS_DIR
from models import Task
from services import TaskService, UserService
from utils import Tooltip, PDFGenerator
from .user_manager_window import UserManagerWindow
# A importação de RestoreBackupWindow será feita dentro do método para evitar ciclos


class MainWindow:
    def __init__(self, username: str, user_level: str):
        self.username = username
        self.user_level = user_level.lower()
        self.tasks: list[Task] = []
        self.icon_cache: dict[str, tk.PhotoImage] = {}

        self.root = tk.Tk()

        if Config.ICON_PATH.exists():
            try:
                self.root.iconbitmap(str(Config.ICON_PATH))
            except Exception as e:
                logger.warning(f"Não foi possível carregar o ícone da aplicação ({Config.ICON_PATH}): {e}")

        self.root.title(f"{Config.APP_NAME} - Usuário: {username} ({user_level.capitalize()})")

        self.center_main_window(width=1000, height=700)
        self.root.minsize(800, 600)

        # Ordem de inicialização da UI:
        self._setup_ui_elements()  # Cria todos os widgets primeiro
        self.setup_menu()         # Depois configura o menu, que pode referenciar widgets

        self.load_tasks_from_service() # Carrega as tarefas na inicialização
        self.update_task_lists_display() # Exibe as tarefas carregadas

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()

    def _on_closing(self):
        logger.info(f"Aplicação encerrada pelo usuário {self.username} através do fechamento da janela principal.")
        self.root.destroy()

    def _load_icon(self, icon_path: Path | None) -> tk.PhotoImage | None:
        if not icon_path or not isinstance(icon_path, Path) or not icon_path.exists():
            if icon_path:
                logger.warning(f"Arquivo de ícone não encontrado ou caminho inválido: {icon_path}")
            return None

        path_str = str(icon_path)
        if path_str not in self.icon_cache:
            try:
                self.icon_cache[path_str] = tk.PhotoImage(file=path_str, master=self.root)
            except tk.TclError as e:
                logger.error(f"Erro ao carregar PhotoImage para {icon_path}: {e}")
                return None
            except Exception as e_pil:
                logger.error(f"Erro PIL/ImageTk ao carregar {icon_path}: {e_pil}")
                return None
        return self.icon_cache[path_str]

    def center_main_window(self, width: int = 1000, height: int = 700):
        self.root.update_idletasks()
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        width_to_use = current_width if current_width > 1 else width
        height_to_use = current_height if current_height > 1 else height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_coordinate = (screen_width // 2) - (width_to_use // 2)
        y_coordinate = (screen_height // 2) - (height_to_use // 2)
        self.root.geometry(f'{width_to_use}x{height_to_use}+{x_coordinate}+{y_coordinate}')

    def setup_menu(self): # Agora chamado depois de _setup_ui_elements
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        refresh_icon = self._load_icon(Config.ICON_REFRESH)
        exit_icon = self._load_icon(Config.ICON_EXIT)
        file_menu.add_command(label="Atualizar Tarefas", command=self.refresh_tasks_ui, image=refresh_icon, compound=tk.LEFT, accelerator="F5")
        self.root.bind("<F5>", lambda event: self.refresh_tasks_ui())
        file_menu.add_separator()
        file_menu.add_command(label="Alterar Minha Senha...",command=self.abrir_tela_alterar_senha)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self._on_closing, image=exit_icon, compound=tk.LEFT)
        menubar.add_cascade(label="Arquivo", menu=file_menu)

        task_menu = tk.Menu(menubar, tearoff=0)
        new_task_icon = self._load_icon(Config.ICON_NEW)
        edit_task_icon = self._load_icon(Config.ICON_EDIT)
        report_icon_menu = self._load_icon(Config.ICON_REPORT)
        task_menu.add_command(label="Nova Tarefa...", command=self.open_new_task_dialog, image=new_task_icon, compound=tk.LEFT, accelerator="Ctrl+N")
        self.root.bind_all("<Control-n>", lambda event: self.open_new_task_dialog())
        task_menu.add_command(label="Editar Tarefa Selecionada", command=self.edit_selected_task, image=edit_task_icon, compound=tk.LEFT, accelerator="F2")
        task_menu.add_separator()
        task_menu.add_command(label="Gerar Relatório de Tarefas...", command=self.generate_report_ui, image=report_icon_menu, compound=tk.LEFT)
        menubar.add_cascade(label="Tarefas", menu=task_menu)

        if self.user_level == 'admin':
            tools_menu = tk.Menu(menubar, tearoff=0)
            user_icon = self._load_icon(Config.ICON_USER)
            restore_icon = self._load_icon(Config.ICON_RESTORE)
            tools_menu.add_command(label="Gerenciar Usuários...", command=self.open_user_manager_ui, image=user_icon, compound=tk.LEFT)
            tools_menu.add_command(label="Backup de Dados...", command=self.create_backup_ui)
            tools_menu.add_command(label="Restaurar Backup...", command=self.open_restore_backup_dialog, image=restore_icon, compound=tk.LEFT)
            menubar.add_cascade(label="Ferramentas", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        about_icon = self._load_icon(Config.ICON_ABOUT)
        help_doc_icon = self._load_icon(Config.ICON_HELP)
        help_menu.add_command(label=f"Sobre o {Config.APP_NAME}", command=self.show_about_dialog, image=about_icon, compound=tk.LEFT)
        help_menu.add_command(label="Documentação Online", command=self.open_documentation_link, image=help_doc_icon, compound=tk.LEFT)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        self.root.config(menu=menubar)

    def _setup_ui_elements(self): # Anteriormente setup_ui
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Aba de Tarefas Pendentes ---
        self.pending_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.pending_frame, text=" Tarefas Pendentes ")
        self.pending_list = ttk.Treeview(
            self.pending_frame,
            columns=('id', 'description', 'priority', 'category', 'created_by', 'created_at'),
            show='headings'
        )
        cols_pending = {'id': ('ID', 80, tk.W), 'description': ('Descrição', 330, tk.W), 'priority': ('Prioridade', 100, tk.CENTER),
                        'category': ('Categoria', 120, tk.W), 'created_by': ('Criado por', 100, tk.W), 'created_at': ('Criada em', 140, tk.CENTER)}
        for col, (head, wd, anc) in cols_pending.items():
            self.pending_list.heading(col, text=head)
            self.pending_list.column(col, width=wd, anchor=anc, stretch=(col == 'description'))
        for i in range(1, 4): self.pending_list.tag_configure(f'priority_{i}', background={1:'#e6ffe6', 2:'#fff2cc', 3:'#ffcccc'}[i])
        self.pending_list.bind("<Double-1>", lambda event: self.edit_selected_task())
        self.pending_list.bind("<F2>", lambda event: self.edit_selected_task()) # Bind F2 aqui é seguro
        self.pending_list.bind("<Delete>", lambda event: self.delete_selected_task())
        ys_p = ttk.Scrollbar(self.pending_frame, orient="vertical", command=self.pending_list.yview)
        xs_p = ttk.Scrollbar(self.pending_frame, orient="horizontal", command=self.pending_list.xview)
        self.pending_list.configure(yscrollcommand=ys_p.set, xscrollcommand=xs_p.set)
        ys_p.pack(side=tk.RIGHT, fill=tk.Y); xs_p.pack(side=tk.BOTTOM, fill=tk.X); self.pending_list.pack(fill=tk.BOTH, expand=True)
        
        p_btn_frame = ttk.Frame(self.pending_frame); p_btn_frame.pack(fill=tk.X, pady=(10,0))
        btns_pending_spec = [
            ("Nova", Config.ICON_NEW, self.open_new_task_dialog, "Criar nova tarefa (Ctrl+N)"),
            ("Editar", Config.ICON_EDIT, self.edit_selected_task, "Editar tarefa selecionada (F2)"),
            ("Concluir", Config.ICON_COMPLETE, self.complete_selected_task, "Marcar como concluída (Ctrl+Enter)"),
            ("Remover", Config.ICON_DELETE, self.delete_selected_task, "Remover tarefa (Delete)")
        ]
        for txt, icon_path, cmd, tip in btns_pending_spec:
            icon = self._load_icon(icon_path)
            btn = ttk.Button(p_btn_frame, text=txt, image=icon, compound=tk.LEFT, command=cmd)
            btn.pack(side=tk.LEFT, padx=5); Tooltip(btn, tip)
        self.root.bind_all("<Control-Return>", lambda event: self.complete_selected_task())

        # --- Aba de Tarefas Concluídas ---
        self.completed_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.completed_frame, text=" Tarefas Concluídas ")
        self.completed_list = ttk.Treeview(
            self.completed_frame,
            columns=('id', 'description', 'category', 'created_by', 'completed_by_user', 'completed_at'),
            show='headings'
        )
        cols_completed = {'id': ('ID', 80, tk.W), 'description': ('Descrição', 280, tk.W), 'category': ('Categoria', 120, tk.W),
                          'created_by': ('Criado por', 100, tk.W), 'completed_by_user': ('Concluído por', 100, tk.W), 'completed_at': ('Concluído em', 140, tk.CENTER)}
        for col, (head, wd, anc) in cols_completed.items():
            self.completed_list.heading(col, text=head)
            self.completed_list.column(col, width=wd, anchor=anc, stretch=(col == 'description'))
        self.completed_list.bind("<Delete>", lambda event: self.delete_selected_task())
        ys_c = ttk.Scrollbar(self.completed_frame, orient="vertical", command=self.completed_list.yview)
        xs_c = ttk.Scrollbar(self.completed_frame, orient="horizontal", command=self.completed_list.xview)
        self.completed_list.configure(yscrollcommand=ys_c.set, xscrollcommand=xs_c.set)
        ys_c.pack(side=tk.RIGHT, fill=tk.Y); xs_c.pack(side=tk.BOTTOM, fill=tk.X); self.completed_list.pack(fill=tk.BOTH, expand=True)

        c_btn_frame = ttk.Frame(self.completed_frame); c_btn_frame.pack(fill=tk.X, pady=(10,0))
        # O estado dos botões é NORMAL por padrão, a lógica de permissão está nas funções de comando.
        btns_completed_spec = [
            ("Reabrir", Config.ICON_REOPEN, self.reopen_selected_task, "Reabrir tarefa selecionada"),
            ("Gerar Relatório", Config.ICON_REPORT, self.generate_report_ui, "Gerar relatório PDF"),
            ("Remover", Config.ICON_DELETE, self.delete_selected_task, "Remover tarefa (Delete)")
        ]
        for spec in btns_completed_spec: # Removido o 'state' da spec, já que é tk.NORMAL
            txt, icon_path, cmd, tip = spec[0], spec[1], spec[2], spec[3]
            icon = self._load_icon(icon_path)
            btn = ttk.Button(c_btn_frame, text=txt, image=icon, compound=tk.LEFT, command=cmd) # state=tk.NORMAL é o padrão
            btn.pack(side=tk.LEFT, padx=5); Tooltip(btn, tip)
            
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar("Pronto.")

    def load_tasks_from_service(self):
        try:
            tasks_data = TaskService.load_tasks()
            self.tasks = [Task.from_dict(task_dict) for task_dict in tasks_data]
            logger.info(f"Total de {len(self.tasks)} tarefas carregadas.")
        except Exception as e:
            logger.error(f"Erro crítico ao carregar tarefas: {e}", exc_info=True)
            messagebox.showerror("Erro Crítico", f"Não foi possível carregar as tarefas: {e}", parent=self.root)
            self.tasks = []

    def get_priority_label(self, priority_value: int) -> str:
        return {1: "Baixa", 2: "Média", 3: "Alta"}.get(priority_value, "N/A")

    def format_display_datetime(self, iso_datetime_str: str | None) -> str:
        if not iso_datetime_str: return "N/A"
        try: return datetime.fromisoformat(iso_datetime_str).strftime('%d/%m/%Y %H:%M')
        except ValueError: return iso_datetime_str[:16]

    def update_task_lists_display(self):
        for item in self.pending_list.get_children(): self.pending_list.delete(item)
        for item in self.completed_list.get_children(): self.completed_list.delete(item)
        pending_tasks, completed_tasks = [], []
        for task in self.tasks: (completed_tasks if task.is_completed else pending_tasks).append(task)
        
        pending_tasks.sort(key=lambda t: (-t.priority, datetime.fromisoformat(t.created_at)))
        for task in pending_tasks:
            self.pending_list.insert('', 'end', iid=task.task_id, values=(
                task.task_id, task.description, self.get_priority_label(task.priority), task.category,
                task.user, self.format_display_datetime(task.created_at)), tags=(f'priority_{task.priority}',))
        
        completed_tasks.sort(key=lambda t: datetime.fromisoformat(t.completed_at) if t.completed_at else datetime.min, reverse=True)
        for task in completed_tasks:
            self.completed_list.insert('', 'end', iid=task.task_id, values=(
                task.task_id, task.description, task.category, task.user,
                task.completed_by or "N/A", self.format_display_datetime(task.completed_at)))
        self.update_status_bar(f"Pendentes: {len(pending_tasks)} | Concluídas: {len(completed_tasks)} | Total: {len(self.tasks)}")

    def update_status_bar(self, message: str):
        self.status_var.set(f"{message} | Usuário: {self.username} ({self.user_level.capitalize()})")

    def refresh_tasks_ui(self):
        logger.info("Atualizando UI de tarefas...")
        try:
            self.load_tasks_from_service()
            self.update_task_lists_display()
            messagebox.showinfo("Atualizado", "Lista de tarefas atualizada.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar tarefas: {e}", parent=self.root)

    def _center_dialog_on_main(self, dialog: tk.Toplevel, width: int, height: int):
        self.root.update_idletasks()
        px, py = self.root.winfo_x(), self.root.winfo_y()
        pw, ph = self.root.winfo_width(), self.root.winfo_height()
        dx, dy = px + (pw - width) // 2, py + (ph - height) // 2
        dialog.geometry(f'{width}x{height}+{dx}+{dy}')
        dialog.resizable(False, False); dialog.transient(self.root); dialog.grab_set()

    def _task_form_dialog_ui(self, dialog: tk.Toplevel, task: Task | None = None):
        """Helper para criar a UI do formulário de tarefa (nova/edição)."""
        is_editing = task is not None
        dialog.title("Editar Tarefa" if is_editing else "Nova Tarefa")
        self._center_dialog_on_main(dialog, 500, 380)

        frame = ttk.Frame(dialog, padding=15); frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Descrição (máx 500 caracteres):").pack(anchor=tk.W)
        desc_txt_frame = ttk.Frame(frame); desc_txt_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        desc_widget = tk.Text(desc_txt_frame, height=8, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
        desc_scroll = ttk.Scrollbar(desc_txt_frame, orient=tk.VERTICAL, command=desc_widget.yview)
        desc_widget['yscrollcommand'] = desc_scroll.set
        desc_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        if is_editing: desc_widget.insert(tk.END, task.description)

        opts_frame = ttk.Frame(frame); opts_frame.pack(fill=tk.X, pady=5)
        ttk.Label(opts_frame, text="Prioridade:").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        priority_var = tk.IntVar(value=task.priority if is_editing else 1)
        pri_radio_frame = ttk.Frame(opts_frame)
        for val, txt in [(1,"Baixa"),(2,"Média"),(3,"Alta")]:
            ttk.Radiobutton(pri_radio_frame, text=txt, variable=priority_var, value=val).pack(side=tk.LEFT, padx=(0 if val==1 else 5, 0))
        pri_radio_frame.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(opts_frame, text="Categoria:").grid(row=1, column=0, sticky=tk.W, padx=(0,5), pady=(5,0))
        cat_entry = ttk.Entry(opts_frame, width=30)
        if is_editing: cat_entry.insert(0, task.category)
        cat_entry.grid(row=1, column=1, sticky=tk.EW, pady=(5,0))
        opts_frame.columnconfigure(1, weight=1)
        
        return desc_widget, priority_var, cat_entry

    def open_new_task_dialog(self):
        dialog = tk.Toplevel(self.root)
        desc_widget, priority_var, cat_entry = self._task_form_dialog_ui(dialog)

        def save_action():
            desc = desc_widget.get("1.0", tk.END).strip()
            cat = cat_entry.get().strip()
            pri = priority_var.get()
            if not desc: messagebox.showerror("Erro", "Descrição é obrigatória.", parent=dialog); return
            if len(desc) > 500: messagebox.showerror("Erro", "Descrição > 500 caracteres.", parent=dialog); return
            if len(cat) > 50: messagebox.showerror("Erro", "Categoria > 50 caracteres.", parent=dialog); return

            task_id = TaskService.get_next_task_id()
            new_task = Task(task_id=task_id, description=desc, user=self.username, priority=pri, category=cat)
            try:
                TaskService.add_task(new_task.to_dict())
                self.load_tasks_from_service()
                self.update_task_lists_display()
                logger.info(f"Nova tarefa '{task_id}' criada por {self.username}.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Falha: {e}", parent=dialog)
                logger.error(f"Erro ao adicionar tarefa {task_id}: {e}", exc_info=True)
        
        # Acessa o frame principal do diálogo para adicionar os botões
        # Assume que main_dialog_frame é o primeiro filho de 'dialog'
        main_dialog_frame = dialog.winfo_children()[0] 
        btn_frame = ttk.Frame(main_dialog_frame); btn_frame.pack(fill=tk.X, pady=(15,0))
        ttk.Button(btn_frame, text="Salvar Tarefa", command=save_action).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)
        desc_widget.focus_set(); dialog.wait_window()

    def _get_selected_task_from_active_treeview(self) -> Task | None:
        current_tab_idx = self.notebook.index(self.notebook.select())
        tree = self.pending_list if current_tab_idx == 0 else self.completed_list
        selected_items = tree.selection()
        if not selected_items: return None
        task_id = selected_items[0]
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def edit_selected_task(self):
        task_to_edit = self._get_selected_task_from_active_treeview()
        if not task_to_edit: # Verifica se uma tarefa foi selecionada
            current_tab_idx = self.notebook.index(self.notebook.select())
            if current_tab_idx == 0: # Apenas mostra aviso se na aba de pendentes
                 messagebox.showwarning("Aviso", "Selecione uma tarefa pendente para editar.", parent=self.root)
            return
            
        if task_to_edit.is_completed:
            messagebox.showinfo("Informação", "Tarefas concluídas não podem ser editadas. Reabra-a primeiro.", parent=self.root)
            return
        if task_to_edit.user != self.username and self.user_level != 'admin':
            messagebox.showwarning("Permissão Negada", "Só pode editar tarefas que você criou (ou se for admin).", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        desc_widget, priority_var, cat_entry = self._task_form_dialog_ui(dialog, task=task_to_edit)

        def save_changes_action():
            desc = desc_widget.get("1.0", tk.END).strip()
            cat = cat_entry.get().strip()
            pri = priority_var.get()
            if not desc: messagebox.showerror("Erro", "Descrição é obrigatória.", parent=dialog); return
            if len(desc) > 500: messagebox.showerror("Erro", "Descrição > 500 caracteres.", parent=dialog); return
            if len(cat) > 50: messagebox.showerror("Erro", "Categoria > 50 caracteres.", parent=dialog); return

            task_to_edit.description = desc; task_to_edit.priority = pri; task_to_edit.category = cat
            try:
                if TaskService.update_task(task_to_edit.to_dict()):
                    self.load_tasks_from_service()
                    self.update_task_lists_display()
                    logger.info(f"Tarefa '{task_to_edit.task_id}' editada por {self.username}.")
                    dialog.destroy()
                else:
                    messagebox.showerror("Erro ao Salvar", f"Tarefa '{task_to_edit.task_id}' não encontrada para atualizar.", parent=dialog)
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Falha: {e}", parent=dialog)
                logger.error(f"Erro ao editar tarefa {task_to_edit.task_id}: {e}", exc_info=True)

        main_dialog_frame = dialog.winfo_children()[0]
        btn_frame = ttk.Frame(main_dialog_frame); btn_frame.pack(fill=tk.X, pady=(15,0))
        ttk.Button(btn_frame, text="Salvar Alterações", command=save_changes_action).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)
        desc_widget.focus_set(); dialog.wait_window()

    def complete_selected_task(self):
        task = self._get_selected_task_from_active_treeview()
        if not task:
            if self.notebook.index(self.notebook.select()) == 0:
                messagebox.showwarning("Aviso", "Selecione uma tarefa pendente para concluir.", parent=self.root)
            return
        if task.is_completed: return

        try:
            if TaskService.complete_task(task.task_id, self.username):
                self.load_tasks_from_service()
                self.update_task_lists_display()
                logger.info(f"Tarefa '{task.task_id}' concluída por {self.username}.")
            else:
                messagebox.showerror("Erro", f"Não foi possível concluir a tarefa '{task.task_id}'.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao concluir tarefa: {e}", parent=self.root)
            logger.error(f"Erro ao concluir tarefa {task.task_id}: {e}", exc_info=True)

    def delete_selected_task(self):
        task = self._get_selected_task_from_active_treeview()
        if not task:
            messagebox.showwarning("Aviso", "Selecione uma tarefa para remover.", parent=self.root)
            return

        can_delete = False
        permission_denied_message = "Você não tem permissão para remover esta tarefa."

        if self.user_level == 'admin':
            can_delete = True
        elif task.user == self.username: 
            if not task.is_completed: 
                can_delete = True
            else: 
                permission_denied_message = "Operadores não podem remover tarefas concluídas. Apenas administradores."
        else: 
            permission_denied_message = "Você só pode remover tarefas pendentes que você criou (ou se for admin)."
        
        if not can_delete:
            messagebox.showwarning("Permissão Negada", permission_denied_message, parent=self.root)
            return
        
        confirm_msg = f"Remover permanentemente:\nID: {task.task_id}\n'{task.description[:80]}...'?"
        if messagebox.askyesno("Confirmar Remoção", confirm_msg, icon='warning', parent=self.root):
            try:
                TaskService.remove_task(task.task_id)
                self.load_tasks_from_service()
                self.update_task_lists_display()
                logger.info(f"Tarefa '{task.task_id}' removida por {self.username}.")
            except Exception as e:
                messagebox.showerror("Erro ao Remover", f"Falha: {e}", parent=self.root)
                logger.error(f"Erro ao remover tarefa {task.task_id}: {e}", exc_info=True)

    def reopen_selected_task(self):
        task = self._get_selected_task_from_active_treeview()
        if not task:
            messagebox.showwarning("Aviso", "Selecione uma tarefa concluída para reabrir.", parent=self.root)
            return
        if not task.is_completed:
            messagebox.showinfo("Informação", "Esta tarefa já está pendente/aberta.", parent=self.root)
            return

        can_reopen = False
        permission_denied_message = "Você não tem permissão para reabrir esta tarefa."
        today_date = date.today()

        if self.user_level == 'admin':
            can_reopen = True
        elif task.user == self.username:
            if task.completed_at:
                try:
                    completed_date = datetime.fromisoformat(task.completed_at).date()
                    if completed_date == today_date:
                        can_reopen = True
                    else:
                        permission_denied_message = "Você só pode reabrir suas tarefas se elas foram concluídas hoje."
                except ValueError:
                    logger.warning(f"Formato de data de conclusão inválido para tarefa {task.task_id}: {task.completed_at}")
                    permission_denied_message = "Data de conclusão da tarefa inválida. Contate o suporte."
            else:
                 permission_denied_message = "Tarefa não possui data de conclusão registrada."
        else:
            permission_denied_message = "Você só pode reabrir tarefas que você criou (e no mesmo dia da conclusão), ou se for admin."

        if not can_reopen:
            messagebox.showwarning("Permissão Negada", permission_denied_message, parent=self.root)
            return

        confirm_msg = f"Reabrir tarefa:\nID: {task.task_id}\n'{task.description[:80]}...'?"
        if messagebox.askyesno("Confirmar Reabertura", confirm_msg, parent=self.root):
            try:
                if TaskService.reopen_task(task.task_id):
                    self.load_tasks_from_service()
                    self.update_task_lists_display()
                    logger.info(f"Tarefa '{task.task_id}' reaberta por {self.username}.")
                else:
                    messagebox.showerror("Erro", f"Não foi possível reabrir a tarefa '{task.task_id}'. Verifique os logs.", parent=self.root)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao reabrir tarefa: {e}", parent=self.root)
                logger.error(f"Erro ao reabrir tarefa {task.task_id}: {e}", exc_info=True)

    def generate_report_ui(self):
        is_completed_report = (self.notebook.index(self.notebook.select()) == 1)
        tasks_for_report = [t.to_dict() for t in self.tasks if t.is_completed == is_completed_report]
        if not tasks_for_report:
            messagebox.showinfo("Relatório Vazio", f"Não há tarefas {'concluídas' if is_completed_report else 'pendentes'} para o relatório.", parent=self.root)
            return

        def _gen_report_thread():
            try:
                self.update_status_bar(f"Gerando relatório...")
                path_str = PDFGenerator.generate_task_report(tasks_for_report, "completed" if is_completed_report else "pending")
                self.update_status_bar(f"Relatório salvo em {path_str}.")
                if messagebox.askyesno("Relatório Gerado", f"Salvo em:\n{path_str}\n\nDeseja abrir?", parent=self.root):
                    try:
                        if sys.platform == "win32": os.startfile(path_str)
                        elif sys.platform == "darwin": subprocess.call(["open", path_str])
                        else: subprocess.call(["xdg-open", path_str])
                    except Exception as e_open: messagebox.showwarning("Erro ao Abrir", f"Não foi possível abrir o PDF: {e_open}", parent=self.root)
            except Exception as e_gen:
                messagebox.showerror("Erro no Relatório", f"Falha ao gerar: {e_gen}", parent=self.root)
                logger.error(f"Falha ao gerar PDF: {e_gen}", exc_info=True)
            finally:
                pend_count = sum(1 for t in self.tasks if not t.is_completed)
                comp_count = len(self.tasks) - pend_count
                self.update_status_bar(f"Pendentes: {pend_count} | Concluídas: {comp_count} | Total: {len(self.tasks)}")
        threading.Thread(target=_gen_report_thread, daemon=True).start()

    def open_user_manager_ui(self):
        if self.user_level == 'admin': UserManagerWindow(self)
        else: messagebox.showerror("Acesso Negado", "Não tem permissão.", parent=self.root)

    def open_restore_backup_dialog(self):
        if self.user_level == 'admin':
            from .restore_backup_window import RestoreBackupWindow
            RestoreBackupWindow(self)
        else: messagebox.showerror("Acesso Negado", "Apenas admins.", parent=self.root)

    def request_app_restart(self, message: str):
        logger.info(f"Solicitação de reinício: {message}")
        for w in self.root.winfo_children():
            if isinstance(w, tk.Toplevel):
                try: w.destroy()
                except: pass
        if messagebox.askokcancel("Reinício Necessário", message + "\n\nA aplicação será fechada.", parent=self.root):
            self.root.destroy()
        else: self.root.destroy()

    def create_backup_ui(self):
        if self.user_level != 'admin':
            messagebox.showerror("Acesso Negado", "Apenas admins.", parent=self.root); return
        try:
            Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            msgs = []
            for file_path, name in [(Config.USERS_FILE, "users"), (Config.TASKS_FILE, "tasks")]:
                if file_path.exists():
                    backup_path = Config.BACKUP_DIR / f"{name}_backup_{ts}.json"
                    shutil.copy2(file_path, backup_path)
                    msgs.append(f"{name.capitalize()}: {backup_path.name}")
                else: msgs.append(f"{name.capitalize()}: Arquivo original não encontrado.")
            
            if any("não encontrado" not in m for m in msgs):
                messagebox.showinfo("Backup Concluído", f"Backup realizado em:\n{Config.BACKUP_DIR}\n\n" + "\n".join(msgs), parent=self.root)
            else: messagebox.showwarning("Backup", "Nenhum arquivo de dados encontrado.", parent=self.root)
        except Exception as e: messagebox.showerror("Erro de Backup", f"Falha: {e}", parent=self.root)

    def show_about_dialog(self):
        contact = f"Contato: {Config.AUTHOR_EMAIL}" if Config.AUTHOR_EMAIL else ""
        author = Config.AUTHOR_NAME or "(Autor não definido)"
        copy = Config.COPYRIGHT_NOTICE or f"© {datetime.now().year} {author}"
        txt = f"{Config.APP_NAME} v{Config.VERSION}\n\nGerenciador de tarefas.\n\nDesenvolvido por: {author}\n{contact}\n\n{copy}"
        messagebox.showinfo(f"Sobre o {Config.APP_NAME}", "\n".join(l for l in txt.splitlines() if l.strip() or l == ""), parent=self.root)

    def open_documentation_link(self):
        try: webbrowser.open_new_tab("https://claudeir.github.io/AgendaCompPro/")
        except Exception as e: messagebox.showerror("Erro", f"Não foi possível abrir documentação: {e}", parent=self.root)

    def abrir_tela_alterar_senha(self):
        users_data = UserService.load_users()
        user_data = users_data.get(self.username)
        if not user_data:
            messagebox.showerror("Erro", "Dados do usuário não encontrados.", parent=self.root); return

        dialog = tk.Toplevel(self.root); dialog.title("Alterar Minha Senha")
        self._center_dialog_on_main(dialog, 400, 250)
        frame = ttk.Frame(dialog, padding=15); frame.pack(fill=tk.BOTH, expand=True)

        labels = ["Senha Atual:", "Nova Senha:", "Confirmar Nova Senha:"]
        entries = {}
        for i, label_text in enumerate(labels):
            ttk.Label(frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=(0 if i==0 else 5,0), padx=(0,5))
            entry = ttk.Entry(frame, show="*", width=35)
            entry.grid(row=i, column=1, pady=(0 if i==0 else 5,0), sticky=tk.EW)
            entries[label_text.split(":")[0].lower().replace(" ", "_")] = entry
        frame.columnconfigure(1, weight=1)
        
        btn_frame = ttk.Frame(frame); btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=(15,0), sticky=tk.EW)

        def _confirm():
            curr = entries["senha_atual"].get()
            new = entries["nova_senha"].get()
            conf = entries["confirmar_nova_senha"].get()

            if not UserService.verify_password(user_data['password_hash'], curr):
                messagebox.showerror("Erro", "Senha atual incorreta.", parent=dialog); return
            if len(new) < 6:
                messagebox.showerror("Erro", "Nova senha deve ter >= 6 caracteres.", parent=dialog); return
            if new != conf:
                messagebox.showerror("Erro", "Nova senha e confirmação não coincidem.", parent=dialog); return
            
            users_data[self.username]['password_hash'] = UserService.hash_password(new)
            try:
                UserService.save_users(users_data)
                messagebox.showinfo("Sucesso", "Senha alterada com sucesso!", parent=dialog)
                logger.info(f"Senha do usuário '{self.username}' alterada.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Falha: {e}", parent=dialog)
                logger.error(f"Erro ao salvar nova senha para '{self.username}': {e}", exc_info=True)

        ttk.Button(btn_frame, text="Salvar Nova Senha", command=_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)
        entries["senha_atual"].focus_set(); dialog.wait_window()