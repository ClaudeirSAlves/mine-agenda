# gui/main_window.py
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime # Já deve estar aqui, mas confirme
import os
import sys
import webbrowser 
import threading 
import subprocess 
import shutil 
from pathlib import Path 
import uuid 

from config import Config, logger, HAS_PIL, ASSETS_DIR # ASSETS_DIR está importado
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

        self.setup_ui()
        self.load_tasks_from_service()
        self.update_task_lists_display()
        
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

    def setup_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        refresh_icon = self._load_icon(Config.ICON_REFRESH)
        exit_icon = self._load_icon(Config.ICON_EXIT)
        
        file_menu.add_command(label="Atualizar Tarefas", command=self.refresh_tasks_ui, image=refresh_icon, compound=tk.LEFT, accelerator="F5")
        self.root.bind("<F5>", lambda event: self.refresh_tasks_ui()) 
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
        self.root.bind_all("<F2>", lambda event: self.edit_selected_task()) 
        task_menu.add_separator()
        task_menu.add_command(label="Gerar Relatório de Tarefas...", command=self.generate_report_ui, image=report_icon_menu, compound=tk.LEFT)
        menubar.add_cascade(label="Tarefas", menu=task_menu)

        if self.user_level == 'admin':
            tools_menu = tk.Menu(menubar, tearoff=0)
            user_icon = self._load_icon(Config.ICON_USER)
            restore_icon_path = ASSETS_DIR / "restore.ico" 
            restore_icon = self._load_icon(restore_icon_path) 

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

    def setup_ui(self):
        self.setup_menu() 
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.pending_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.pending_frame, text=" Tarefas Pendentes ") 
        self.pending_list = ttk.Treeview(
            self.pending_frame,
            columns=('id', 'description', 'priority', 'category', 'created_by', 'created_at'), 
            show='headings' 
        )
        self.pending_list.heading('id', text='ID')
        self.pending_list.heading('description', text='Descrição')
        self.pending_list.heading('priority', text='Prioridade')
        self.pending_list.heading('category', text='Categoria')
        self.pending_list.heading('created_by', text='Criado por') 
        self.pending_list.heading('created_at', text='Criada em')
        self.pending_list.column('id', width=80, anchor=tk.W, stretch=tk.NO) 
        self.pending_list.column('description', width=330, stretch=tk.YES) 
        self.pending_list.column('priority', width=100, anchor=tk.CENTER, stretch=tk.NO)
        self.pending_list.column('category', width=120, anchor=tk.W, stretch=tk.NO)
        self.pending_list.column('created_by', width=100, anchor=tk.W, stretch=tk.NO) 
        self.pending_list.column('created_at', width=140, anchor=tk.CENTER, stretch=tk.NO)
        self.pending_list.tag_configure('priority_1', background='#e6ffe6')  
        self.pending_list.tag_configure('priority_2', background='#fff2cc')  
        self.pending_list.tag_configure('priority_3', background='#ffcccc')  
        self.pending_list.bind("<Double-1>", lambda event: self.edit_selected_task()) 
        pending_scrollbar_y = ttk.Scrollbar(self.pending_frame, orient="vertical", command=self.pending_list.yview)
        pending_scrollbar_x = ttk.Scrollbar(self.pending_frame, orient="horizontal", command=self.pending_list.xview)
        self.pending_list.configure(yscrollcommand=pending_scrollbar_y.set, xscrollcommand=pending_scrollbar_x.set)
        pending_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        pending_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X) 
        self.pending_list.pack(fill=tk.BOTH, expand=True)
        pending_button_frame = ttk.Frame(self.pending_frame)
        pending_button_frame.pack(fill=tk.X, pady=(10,0)) 
        icon_btn_new = self._load_icon(Config.ICON_NEW)
        icon_btn_edit = self._load_icon(Config.ICON_EDIT)
        icon_btn_complete = self._load_icon(Config.ICON_COMPLETE)
        icon_btn_delete = self._load_icon(Config.ICON_DELETE)
        btn_nova_tarefa = ttk.Button(pending_button_frame, text="Nova", image=icon_btn_new, compound=tk.LEFT, command=self.open_new_task_dialog)
        btn_nova_tarefa.pack(side=tk.LEFT, padx=5)
        Tooltip(btn_nova_tarefa, "Criar uma nova tarefa (Ctrl+N)")
        btn_edit = ttk.Button(pending_button_frame, text="Editar", image=icon_btn_edit, compound=tk.LEFT, command=self.edit_selected_task)
        btn_edit.pack(side=tk.LEFT, padx=5)
        Tooltip(btn_edit, "Editar tarefa selecionada (F2)")
        btn_complete = ttk.Button(pending_button_frame, text="Concluir", image=icon_btn_complete, compound=tk.LEFT, command=self.complete_selected_task)
        btn_complete.pack(side=tk.LEFT, padx=5)
        Tooltip(btn_complete, "Marcar tarefa selecionada como concluída (Ctrl+Enter)")
        self.root.bind_all("<Control-Return>", lambda event: self.complete_selected_task()) 
        btn_delete = ttk.Button(pending_button_frame, text="Remover", image=icon_btn_delete, compound=tk.LEFT, command=self.delete_selected_task)
        btn_delete.pack(side=tk.LEFT, padx=5)
        Tooltip(btn_delete, "Remover tarefa selecionada (Delete)")
        
        self.completed_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.completed_frame, text=" Tarefas Concluídas ")
        self.completed_list = ttk.Treeview(
            self.completed_frame,
            columns=('id', 'description', 'category', 'created_by', 'completed_by_user', 'completed_at'), 
            show='headings'
        )
        self.completed_list.heading('id', text='ID')
        self.completed_list.heading('description', text='Descrição')
        self.completed_list.heading('category', text='Categoria')
        self.completed_list.heading('created_by', text='Criado por')         
        self.completed_list.heading('completed_by_user', text='Concluído por') 
        self.completed_list.heading('completed_at', text='Concluído em')
        self.completed_list.column('id', width=80, anchor=tk.W, stretch=tk.NO) 
        self.completed_list.column('description', width=280, stretch=tk.YES) 
        self.completed_list.column('category', width=120, anchor=tk.W, stretch=tk.NO)
        self.completed_list.column('created_by', width=100, anchor=tk.W, stretch=tk.NO) 
        self.completed_list.column('completed_by_user', width=100, anchor=tk.W, stretch=tk.NO) 
        self.completed_list.column('completed_at', width=140, anchor=tk.CENTER, stretch=tk.NO)
        completed_scrollbar_y = ttk.Scrollbar(self.completed_frame, orient="vertical", command=self.completed_list.yview)
        completed_scrollbar_x = ttk.Scrollbar(self.completed_frame, orient="horizontal", command=self.completed_list.xview)
        self.completed_list.configure(yscrollcommand=completed_scrollbar_y.set, xscrollcommand=completed_scrollbar_x.set)
        completed_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        completed_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.completed_list.pack(fill=tk.BOTH, expand=True)
        completed_button_frame = ttk.Frame(self.completed_frame)
        completed_button_frame.pack(fill=tk.X, pady=(10,0))
        icon_btn_reopen = self._load_icon(Config.ICON_REOPEN)
        icon_btn_report_tab = self._load_icon(Config.ICON_REPORT) 
        btn_reopen = ttk.Button(
            completed_button_frame, text="Reabrir", image=icon_btn_reopen, compound=tk.LEFT,
            command=self.reopen_selected_task, state=tk.DISABLED if self.user_level != 'admin' else tk.NORMAL 
        )
        btn_reopen.pack(side=tk.LEFT, padx=5)
        Tooltip(btn_reopen, "Reabrir tarefa concluída (Apenas Administradores)")
        btn_report_completed = ttk.Button(completed_button_frame, text="Gerar Relatório", image=icon_btn_report_tab, compound=tk.LEFT, command=self.generate_report_ui)
        btn_report_completed.pack(side=tk.LEFT, padx=5)
        Tooltip(btn_report_completed, "Gerar relatório em PDF das tarefas concluídas")
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar("Pronto.") 

    def load_tasks_from_service(self):
        try:
            tasks_data = TaskService.load_tasks() 
            self.tasks = [Task.from_dict(task_dict) for task_dict in tasks_data]
            logger.info(f"Total de {len(self.tasks)} tarefas carregadas do serviço.")
        except Exception as e:
            logger.error(f"Erro crítico ao carregar tarefas do serviço: {e}", exc_info=True)
            messagebox.showerror("Erro Crítico", "Não foi possível carregar as tarefas. Verifique os logs.", parent=self.root)
            self.tasks = [] 

    def save_tasks_to_service(self):
        try:
            tasks_data = [task.to_dict() for task in self.tasks]
            TaskService.save_tasks(tasks_data)
            logger.info("Tarefas salvas com sucesso no serviço.")
        except Exception as e:
            logger.error(f"Erro crítico ao salvar tarefas no serviço: {e}", exc_info=True)
            messagebox.showerror("Erro Crítico", "Não foi possível salvar as tarefas. Verifique os logs.", parent=self.root)
    
    def get_priority_label(self, priority_value: int) -> str:
        return {1: "Baixa", 2: "Média", 3: "Alta"}.get(priority_value, "N/A")

    def format_display_datetime(self, iso_datetime_str: str | None) -> str:
        if not iso_datetime_str: return "N/A"
        try:
            return datetime.fromisoformat(iso_datetime_str).strftime('%d/%m/%Y %H:%M')
        except ValueError:
            logger.warning(f"Data/hora em formato ISO inválido para exibição: {iso_datetime_str}")
            return iso_datetime_str[:16] 

    def update_task_lists_display(self):
        for item in self.pending_list.get_children(): self.pending_list.delete(item)
        for item in self.completed_list.get_children(): self.completed_list.delete(item)

        pending_display_tasks = []
        completed_display_tasks = []
        
        for task in self.tasks: 
            if not task.is_completed:
                pending_display_tasks.append(task)
            else:
                completed_display_tasks.append(task)
        
        pending_display_tasks.sort(key=lambda t: (-t.priority, datetime.fromisoformat(t.created_at)))

        for task_obj in pending_display_tasks:
            display_id = task_obj.task_id
            self.pending_list.insert(
                '', 'end',
                iid=task_obj.task_id, 
                values=(
                    display_id, 
                    task_obj.description,
                    self.get_priority_label(task_obj.priority),
                    task_obj.category,
                    task_obj.user, 
                    self.format_display_datetime(task_obj.created_at)
                ),
                tags=(f'priority_{task_obj.priority}',) 
            )
        
        completed_display_tasks.sort(key=lambda t: datetime.fromisoformat(t.completed_at) if t.completed_at else datetime.min, reverse=True)

        for task_obj in completed_display_tasks:
            display_id = task_obj.task_id
            self.completed_list.insert('', 'end', 
                iid=task_obj.task_id,
                values=(
                    display_id,
                    task_obj.description,
                    task_obj.category,
                    task_obj.user, 
                    task_obj.completed_by or "N/A", 
                    self.format_display_datetime(task_obj.completed_at)
                )
            )
        
        self.update_status_bar(f"Pendentes: {len(pending_display_tasks)} | Concluídas: {len(completed_display_tasks)} | Total: {len(self.tasks)}")

    def update_status_bar(self, message: str):
        full_message = f"{message} | Usuário: {self.username} ({self.user_level.capitalize()})"
        self.status_var.set(full_message)

    def refresh_tasks_ui(self):
        logger.info("Atualizando interface de tarefas a partir do comando do usuário...")
        self.load_tasks_from_service()
        self.update_task_lists_display()
        messagebox.showinfo("Atualizado", "Lista de tarefas foi atualizada com sucesso.", parent=self.root)

    def _center_dialog_on_main(self, dialog_window: tk.Toplevel, width: int, height: int):
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        dialog_x = main_x + (main_width - width) // 2
        dialog_y = main_y + (main_height - height) // 2
        dialog_window.geometry(f'{width}x{height}+{dialog_x}+{dialog_y}')
        dialog_window.resizable(False, False) 
        dialog_window.transient(self.root) 
        dialog_window.grab_set() 

    def open_new_task_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Nova Tarefa")
        self._center_dialog_on_main(dialog, width=500, height=380)
        main_dialog_frame = ttk.Frame(dialog, padding=15)
        main_dialog_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_dialog_frame, text="Descrição (máx 500 caracteres):").pack(anchor=tk.W, pady=(0,2))
        desc_text_frame = ttk.Frame(main_dialog_frame)
        desc_text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        description_text_widget = tk.Text(desc_text_frame, height=8, width=50, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
        desc_scrollbar = ttk.Scrollbar(desc_text_frame, orient=tk.VERTICAL, command=description_text_widget.yview)
        description_text_widget['yscrollcommand'] = desc_scrollbar.set
        description_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        options_frame = ttk.Frame(main_dialog_frame)
        options_frame.pack(fill=tk.X, pady=5)
        ttk.Label(options_frame, text="Prioridade:").grid(row=0, column=0, sticky=tk.W, padx=(0,5), pady=(0,5))
        priority_var = tk.IntVar(value=1) 
        priority_radio_frame = ttk.Frame(options_frame)
        ttk.Radiobutton(priority_radio_frame, text="Baixa", variable=priority_var, value=1).pack(side=tk.LEFT)
        ttk.Radiobutton(priority_radio_frame, text="Média", variable=priority_var, value=2).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(priority_radio_frame, text="Alta", variable=priority_var, value=3).pack(side=tk.LEFT)
        priority_radio_frame.grid(row=0, column=1, sticky=tk.W, pady=(0,5))
        ttk.Label(options_frame, text="Categoria:").grid(row=1, column=0, sticky=tk.W, padx=(0,5))
        category_entry_widget = ttk.Entry(options_frame, width=30)
        category_entry_widget.grid(row=1, column=1, sticky=tk.EW, pady=(0,5))
        options_frame.columnconfigure(1, weight=1) 
        action_button_frame = ttk.Frame(main_dialog_frame)
        action_button_frame.pack(fill=tk.X, pady=(15,0))
        def save_action():
            description = description_text_widget.get("1.0", tk.END).strip()
            category = category_entry_widget.get().strip()
            priority = priority_var.get()
            if not description:
                messagebox.showerror("Erro", "A descrição da tarefa é obrigatória.", parent=dialog)
                return
            if len(description) > 500:
                messagebox.showerror("Erro", "A descrição não pode exceder 500 caracteres.", parent=dialog)
                return
            if len(category) > 50:
                 messagebox.showerror("Erro", "A categoria não pode exceder 50 caracteres.", parent=dialog)
                 return
            new_task_id_str = TaskService.get_next_task_id()
            new_task_obj = Task(task_id=new_task_id_str, description=description, 
                                user=self.username, priority=priority, category=category)
            self.tasks.append(new_task_obj)
            self.save_tasks_to_service()
            self.update_task_lists_display()
            logger.info(f"Nova tarefa '{new_task_obj.task_id}' criada por {self.username}.")
            dialog.destroy()
        ttk.Button(action_button_frame, text="Salvar Tarefa", command=save_action).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)
        description_text_widget.focus_set() 
        dialog.wait_window() 
    
    def _get_selected_task_from_treeview(self, treeview: ttk.Treeview) -> Task | None:
        selected_items = treeview.selection() 
        if not selected_items:
            return None
        task_id_from_selection = selected_items[0] 
        selected_task_obj = next((task for task in self.tasks if task.task_id == task_id_from_selection), None)
        if not selected_task_obj: 
            logger.warning(f"Task com ID '{task_id_from_selection}' selecionado na Treeview, mas não encontrado na lista self.tasks.")
        return selected_task_obj

    def edit_selected_task(self):
        current_tab_index = self.notebook.index(self.notebook.select())
        task_to_edit: Task | None = None
        if current_tab_index == 0: 
            task_to_edit = self._get_selected_task_from_treeview(self.pending_list) 
            if not task_to_edit:
                messagebox.showwarning("Aviso", "Selecione uma tarefa pendente para editar.", parent=self.root)
                return
        else: 
            messagebox.showinfo("Informação", "Tarefas concluídas não podem ser editadas diretamente. Se necessário, reabra a tarefa.", parent=self.root)
            return
        if task_to_edit.user != self.username and self.user_level != 'admin':
            messagebox.showwarning("Permissão Negada", "Você só pode editar tarefas que você criou, a menos que seja um administrador.", parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar Tarefa: {task_to_edit.task_id}") 
        self._center_dialog_on_main(dialog, width=500, height=380)
        main_dialog_frame = ttk.Frame(dialog, padding=15)
        main_dialog_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_dialog_frame, text="Descrição (máx 500 caracteres):").pack(anchor=tk.W, pady=(0,2))
        desc_text_frame = ttk.Frame(main_dialog_frame)
        desc_text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        description_text_widget = tk.Text(desc_text_frame, height=8, width=50, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
        description_text_widget.insert(tk.END, task_to_edit.description) 
        desc_scrollbar = ttk.Scrollbar(desc_text_frame, orient=tk.VERTICAL, command=description_text_widget.yview)
        description_text_widget['yscrollcommand'] = desc_scrollbar.set
        description_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        options_frame = ttk.Frame(main_dialog_frame)
        options_frame.pack(fill=tk.X, pady=5)
        ttk.Label(options_frame, text="Prioridade:").grid(row=0, column=0, sticky=tk.W, padx=(0,5), pady=(0,5))
        priority_var = tk.IntVar(value=task_to_edit.priority) 
        priority_radio_frame = ttk.Frame(options_frame)
        ttk.Radiobutton(priority_radio_frame, text="Baixa", variable=priority_var, value=1).pack(side=tk.LEFT)
        ttk.Radiobutton(priority_radio_frame, text="Média", variable=priority_var, value=2).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(priority_radio_frame, text="Alta", variable=priority_var, value=3).pack(side=tk.LEFT)
        priority_radio_frame.grid(row=0, column=1, sticky=tk.W, pady=(0,5))
        ttk.Label(options_frame, text="Categoria:").grid(row=1, column=0, sticky=tk.W, padx=(0,5))
        category_entry_widget = ttk.Entry(options_frame, width=30)
        category_entry_widget.insert(0, task_to_edit.category) 
        category_entry_widget.grid(row=1, column=1, sticky=tk.EW, pady=(0,5))
        options_frame.columnconfigure(1, weight=1)
        action_button_frame = ttk.Frame(main_dialog_frame)
        action_button_frame.pack(fill=tk.X, pady=(15,0))
        def save_changes_action():
            new_description = description_text_widget.get("1.0", tk.END).strip()
            new_category = category_entry_widget.get().strip()
            new_priority = priority_var.get()
            if not new_description:
                messagebox.showerror("Erro", "A descrição não pode estar vazia.", parent=dialog)
                return
            if len(new_description) > 500:
                messagebox.showerror("Erro", "A descrição não pode ultrapassar 500 caracteres.", parent=dialog)
                return
            if len(new_category) > 50:
                 messagebox.showerror("Erro", "A categoria não pode ultrapassar 50 caracteres.", parent=dialog)
                 return
            task_to_edit.description = new_description
            task_to_edit.priority = new_priority
            task_to_edit.category = new_category
            self.save_tasks_to_service()
            self.update_task_lists_display()
            logger.info(f"Tarefa '{task_to_edit.task_id}' editada por {self.username}.")
            dialog.destroy()
        ttk.Button(action_button_frame, text="Salvar Alterações", command=save_changes_action).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)
        description_text_widget.focus_set()
        dialog.wait_window()

    def complete_selected_task(self):
        task_to_complete = self._get_selected_task_from_treeview(self.pending_list) 
        if not task_to_complete:
            messagebox.showwarning("Aviso", "Selecione uma tarefa pendente para concluir.", parent=self.root)
            return
        task_to_complete.is_completed = True
        task_to_complete.completed_at = datetime.now().isoformat()
        task_to_complete.completed_by = self.username 
        self.save_tasks_to_service()
        self.update_task_lists_display()
        logger.info(f"Tarefa '{task_to_complete.task_id}' marcada como concluída por {self.username}.")

    def delete_selected_task(self):
        current_tab_index = self.notebook.index(self.notebook.select())
        treeview_to_use = self.pending_list if current_tab_index == 0 else self.completed_list
        task_to_delete = self._get_selected_task_from_treeview(treeview_to_use) 
        if not task_to_delete:
            messagebox.showwarning("Aviso", "Selecione uma tarefa para remover.", parent=self.root)
            return
        if task_to_delete.user != self.username and self.user_level != 'admin':
            messagebox.showwarning("Permissão Negada", "Você só pode remover tarefas que você criou, a menos que seja um administrador.", parent=self.root)
            return
        confirm_msg = f"Tem certeza que deseja remover permanentemente a tarefa:\n\n'{task_to_delete.description[:80]}...'?"
        if messagebox.askyesno("Confirmar Remoção", confirm_msg, icon='warning', parent=self.root):
            self.tasks.remove(task_to_delete) 
            self.save_tasks_to_service()
            self.update_task_lists_display()
            logger.info(f"Tarefa '{task_to_delete.task_id}' removida permanentemente por {self.username}.")

    def reopen_selected_task(self):
        if self.user_level != 'admin':
            messagebox.showerror("Permissão Negada", "Apenas administradores podem reabrir tarefas.", parent=self.root)
            return
        task_to_reopen = self._get_selected_task_from_treeview(self.completed_list) 
        if not task_to_reopen:
            messagebox.showwarning("Aviso", "Selecione uma tarefa concluída para reabrir.", parent=self.root)
            return
        confirm_msg = f"Deseja reabrir a tarefa:\n\n'{task_to_reopen.description[:80]}...'?"
        if messagebox.askyesno("Confirmar Reabertura", confirm_msg, parent=self.root):
            task_to_reopen.is_completed = False
            task_to_reopen.completed_at = None
            task_to_reopen.completed_by = None 
            self.save_tasks_to_service()
            self.update_task_lists_display()
            logger.info(f"Tarefa '{task_to_reopen.task_id}' reaberta por {self.username}.")

    def generate_report_ui(self):
        current_tab_index = self.notebook.index(self.notebook.select())
        is_completed_report = (current_tab_index == 1) 
        report_type_label = "concluídas" if is_completed_report else "pendentes"
        tasks_for_report_obj = [task for task in self.tasks if task.is_completed == is_completed_report]
        if not tasks_for_report_obj:
            messagebox.showinfo("Relatório Vazio", f"Não há tarefas {report_type_label} para incluir no relatório.", parent=self.root)
            return
        tasks_for_report_dict = [task.to_dict() for task in tasks_for_report_obj]
        def _generate_and_open_report():
            try:
                self.update_status_bar(f"Gerando relatório de tarefas {report_type_label}...")
                report_path_str = PDFGenerator.generate_task_report(tasks_for_report_dict, "completed" if is_completed_report else "pending")
                self.update_status_bar(f"Relatório salvo em {report_path_str}.")
                if messagebox.askyesno("Relatório Gerado", f"Relatório salvo em:\n{report_path_str}\n\nDeseja abri-lo agora?", parent=self.root):
                    try:
                        if sys.platform == "win32": os.startfile(report_path_str) 
                        elif sys.platform == "darwin": subprocess.call(["open", report_path_str])
                        else: subprocess.call(["xdg-open", report_path_str])
                    except Exception as e_open:
                        logger.error(f"Erro ao tentar abrir o PDF {report_path_str}: {e_open}", exc_info=True)
                        messagebox.showwarning("Erro ao Abrir", "Não foi possível abrir o PDF automaticamente. Por favor, navegue até o local.", parent=self.root)
            except RuntimeError as e_gen: 
                logger.error(f"Falha ao gerar relatório PDF: {e_gen}", exc_info=True)
                messagebox.showerror("Erro no Relatório", f"Falha ao gerar o relatório:\n{e_gen}", parent=self.root)
            except Exception as e_thread: 
                 logger.error(f"Erro inesperado na thread de geração de relatório: {e_thread}", exc_info=True)
                 messagebox.showerror("Erro Inesperado", "Ocorreu um erro ao gerar o relatório.", parent=self.root)
            finally:
                self.update_task_lists_display() 
        threading.Thread(target=_generate_and_open_report, daemon=True).start()

    def open_user_manager_ui(self):
        if self.user_level == 'admin':
            UserManagerWindow(self) 
        else:
            messagebox.showerror("Acesso Negado", "Você não tem permissão para gerenciar usuários.", parent=self.root)

    def open_restore_backup_dialog(self):
        if self.user_level == 'admin':
            from .restore_backup_window import RestoreBackupWindow 
            RestoreBackupWindow(self) 
        else:
            messagebox.showerror("Acesso Negado", "Apenas administradores podem restaurar backups.", parent=self.root)

    def request_app_restart(self, message_to_show: str):
        logger.info(f"Solicitação de reinício da aplicação: {message_to_show}")
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                try:
                    widget.destroy()
                except tk.TclError:
                    pass 
        
        if messagebox.askokcancel("Reinício Necessário", message_to_show + "\n\nA aplicação será fechada. Por favor, abra-a novamente.", parent=self.root):
            self.root.destroy()
        else: 
            self.root.destroy()


    def create_backup_ui(self):
        if self.user_level != 'admin':
            messagebox.showerror("Acesso Negado", "Apenas administradores podem criar backups.", parent=self.root)
            return
        try:
            Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True) 
            backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_success_messages = []
            if Config.USERS_FILE.exists():
                users_backup_path = Config.BACKUP_DIR / f"users_backup_{backup_timestamp}.json"
                shutil.copy2(Config.USERS_FILE, users_backup_path) 
                logger.info(f"Backup de usuários criado em: {users_backup_path}")
                backup_success_messages.append(f"Usuários: {users_backup_path.name}")
            else:
                logger.warning(f"Arquivo de usuários {Config.USERS_FILE} não encontrado para backup.")
                backup_success_messages.append("Usuários: Arquivo original não encontrado.")
            if Config.TASKS_FILE.exists():
                tasks_backup_path = Config.BACKUP_DIR / f"tasks_backup_{backup_timestamp}.json"
                shutil.copy2(Config.TASKS_FILE, tasks_backup_path)
                logger.info(f"Backup de tarefas criado em: {tasks_backup_path}")
                backup_success_messages.append(f"Tarefas: {tasks_backup_path.name}")
            else:
                logger.warning(f"Arquivo de tarefas {Config.TASKS_FILE} não encontrado para backup.")
                backup_success_messages.append("Tarefas: Arquivo original não encontrado.")
            if backup_success_messages:
                 final_message = f"Backup dos dados realizado com sucesso em:\n{Config.BACKUP_DIR}\n\nArquivos gerados:\n" + "\n".join(backup_success_messages)
                 messagebox.showinfo("Backup Concluído", final_message, parent=self.root)
            else: 
                 messagebox.showwarning("Backup", "Nenhum arquivo de dados encontrado para fazer backup.", parent=self.root)
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}", exc_info=True)
            messagebox.showerror("Erro de Backup", f"Falha ao criar backup:\n{e}", parent=self.root)

    def show_about_dialog(self):
        # Usa os atributos da classe Config para as informações do autor
        contact_line = ""
        if hasattr(Config, 'AUTHOR_EMAIL') and Config.AUTHOR_EMAIL: # Verifica se AUTHOR_EMAIL existe e não é vazio
            contact_line = f"Contato: {Config.AUTHOR_EMAIL}"

        author_name_to_display = Config.AUTHOR_NAME if hasattr(Config, 'AUTHOR_NAME') else "(Autor não definido)"
        copyright_notice_to_display = Config.COPYRIGHT_NOTICE if hasattr(Config, 'COPYRIGHT_NOTICE') else f"© {datetime.now().year}"


        about_text = f"""{Config.APP_NAME} v{Config.VERSION}

Um sistema de gerenciamento de tarefas.

Desenvolvido por: {author_name_to_display}
{contact_line}

{copyright_notice_to_display}
"""
        # Remove linhas em branco extras se contact_line for vazia
        about_text = "\n".join(line for line in about_text.splitlines() if line.strip() or line == "")


        messagebox.showinfo(f"Sobre o {Config.APP_NAME}", about_text, parent=self.root)

    def open_documentation_link(self):
        try:
            doc_url = "https://www.example.com/agendacomppro/docs" 
            webbrowser.open_new_tab(doc_url)
            logger.info(f"Tentando abrir documentação em: {doc_url}")
        except Exception as e:
            logger.error(f"Não foi possível abrir o link da documentação: {e}", exc_info=True)
            messagebox.showerror("Erro", "Não foi possível abrir o link da documentação.", parent=self.root)