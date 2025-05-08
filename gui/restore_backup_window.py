# gui/restore_backup_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import re 
from datetime import datetime
from pathlib import Path
import shutil 

# Importação corrigida para incluir ASSETS_DIR
from config import Config, logger, ASSETS_DIR 

class RestoreBackupWindow(tk.Toplevel):
    def __init__(self, parent_main_window):
        super().__init__(parent_main_window.root)
        self.parent_main_window = parent_main_window
        self.transient(parent_main_window.root)
        self.grab_set()

        self.title("Restaurar Backup")
        
        # Linha corrigida para usar ASSETS_DIR do módulo
        restore_icon_path = ASSETS_DIR / "restore.ico" 
        if restore_icon_path.exists():
             try: self.iconbitmap(str(restore_icon_path))
             except Exception: 
                 logger.warning(f"Falha ao carregar ícone de restauração: {restore_icon_path}, tentando ícone principal.")
                 if Config.ICON_PATH.exists(): # ICON_PATH é um atributo de Config
                     try: self.iconbitmap(str(Config.ICON_PATH))
                     except Exception: logger.warning(f"Falha ao carregar ícone principal: {Config.ICON_PATH}")
        elif Config.ICON_PATH.exists(): 
            try: self.iconbitmap(str(Config.ICON_PATH))
            except Exception: logger.warning(f"Falha ao carregar ícone principal: {Config.ICON_PATH}")
            
        self.geometry("650x450") 
        self.minsize(550, 350)
        self._center_dialog()

        self.selected_backup_timestamp = None
        self.backup_sets = {} 

        self.setup_ui()
        self.load_available_backups()

    def _center_dialog(self):
        self.update_idletasks()
        parent_x = self.parent_main_window.root.winfo_x()
        parent_y = self.parent_main_window.root.winfo_y()
        parent_width = self.parent_main_window.root.winfo_width()
        parent_height = self.parent_main_window.root.winfo_height()
        width = self.winfo_width()
        height = self.winfo_height()
        center_x = parent_x + (parent_width - width) // 2
        center_y = parent_y + (parent_height - height) // 2
        self.geometry(f'+{center_x}+{center_y}')

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(main_frame, text="Backups Disponíveis (Mais recentes primeiro)", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))

        self.backup_list_treeview = ttk.Treeview(
            list_frame,
            columns=('datetime', 'files_info', 'timestamp_raw'), 
            show='headings',
            displaycolumns=('datetime', 'files_info') 
        )
        self.backup_list_treeview.heading('datetime', text='Data e Hora do Backup')
        self.backup_list_treeview.heading('files_info', text='Arquivos no Backup')
        self.backup_list_treeview.column('datetime', width=200, anchor=tk.W)
        self.backup_list_treeview.column('files_info', width=350, anchor=tk.W, stretch=tk.YES)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.backup_list_treeview.yview)
        self.backup_list_treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.backup_list_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.backup_list_treeview.bind('<<TreeviewSelect>>', self.on_backup_selected)

        status_label_frame = ttk.Frame(main_frame)
        status_label_frame.pack(fill=tk.X, pady=(5,0))
        self.status_label = ttk.Label(status_label_frame, text="Selecione um backup da lista para restaurar.")
        self.status_label.pack(anchor=tk.W)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0))

        self.restore_button = ttk.Button(button_frame, text="Restaurar Selecionado", command=self.on_restore_clicked, state=tk.DISABLED)
        self.restore_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancelar", command=self.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)

    def load_available_backups(self):
        for item in self.backup_list_treeview.get_children():
            self.backup_list_treeview.delete(item)
        self.backup_sets.clear()

        if not Config.BACKUP_DIR.exists(): # BACKUP_DIR é um atributo de Config
            logger.warning(f"Diretório de backup não encontrado: {Config.BACKUP_DIR}")
            self.status_label.config(text="Diretório de backup não encontrado.")
            return

        backup_pattern = re.compile(r"^(users|tasks)_backup_(\d{8}_\d{6})\.json$")
        temp_backups = {} 

        for filename_obj in Config.BACKUP_DIR.iterdir(): # BACKUP_DIR é um atributo de Config
            if filename_obj.is_file():
                match = backup_pattern.match(filename_obj.name)
                if match:
                    file_type = match.group(1) 
                    timestamp_str = match.group(2) 
                    if timestamp_str not in temp_backups:
                        temp_backups[timestamp_str] = {}
                    temp_backups[timestamp_str][file_type] = filename_obj
        
        sorted_timestamps = sorted(temp_backups.keys(), reverse=True) 

        for ts_str in sorted_timestamps:
            if 'users' in temp_backups[ts_str] and 'tasks' in temp_backups[ts_str]:
                self.backup_sets[ts_str] = temp_backups[ts_str] 
                try:
                    dt_obj = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    display_datetime = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
                except ValueError:
                    display_datetime = ts_str 
                
                files_info_str = "Usuários e Tarefas"
                self.backup_list_treeview.insert('', 'end', iid=ts_str, 
                                                  values=(display_datetime, files_info_str, ts_str))
        
        if not self.backup_sets:
            self.status_label.config(text="Nenhum conjunto de backup completo encontrado.")
        else:
            self.status_label.config(text=f"{len(self.backup_sets)} conjunto(s) de backup encontrado(s). Selecione um.")

    def on_backup_selected(self, event=None):
        selected_items = self.backup_list_treeview.selection()
        if selected_items:
            self.selected_backup_timestamp = selected_items[0] 
            self.restore_button.config(state=tk.NORMAL)
            selected_item_values = self.backup_list_treeview.item(self.selected_backup_timestamp, 'values')
            if selected_item_values:
                 self.status_label.config(text=f"Backup de {selected_item_values[0]} selecionado.")
        else:
            self.selected_backup_timestamp = None
            self.restore_button.config(state=tk.DISABLED)
            self.status_label.config(text="Selecione um backup da lista para restaurar.")

    def on_restore_clicked(self):
        if not self.selected_backup_timestamp:
            messagebox.showwarning("Nenhum Backup Selecionado", "Por favor, selecione um backup da lista.", parent=self)
            return

        selected_item_values = self.backup_list_treeview.item(self.selected_backup_timestamp, 'values')
        display_dt = selected_item_values[0] if selected_item_values else f"timestamp {self.selected_backup_timestamp}"

        confirm_msg = (
            f"Você está prestes a restaurar o backup de {display_dt}.\n\n"
            "ATENÇÃO: Esta ação substituirá os seus dados atuais de usuários e tarefas. "
            "Esta operação NÃO PODE SER DESFEITA através da aplicação.\n\n"
            "Recomenda-se fazer um backup dos dados atuais antes de prosseguir, se ainda não o fez.\n\n"
            "Deseja continuar com a restauração?"
        )
        if messagebox.askyesno("Confirmar Restauração", confirm_msg, icon='warning', parent=self):
            logger.info(f"Usuário {self.parent_main_window.username} confirmou a restauração do backup: {self.selected_backup_timestamp}")
            
            success, message = self._perform_actual_restore(self.selected_backup_timestamp)
            
            if success:
                messagebox.showinfo("Sucesso", f"{message}\nA aplicação precisa ser reiniciada para que as alterações tenham efeito.", parent=self)
                self.parent_main_window.request_app_restart(
                    "Os dados foram restaurados com sucesso a partir do backup.\n"
                    "Por favor, reinicie a aplicação."
                )
                self.destroy() 
            else:
                messagebox.showerror("Erro na Restauração", message, parent=self)

    def _perform_actual_restore(self, timestamp_to_restore: str) -> tuple[bool, str]:
        if timestamp_to_restore not in self.backup_sets:
            return False, "Conjunto de backup selecionado não encontrado."

        backup_files_info = self.backup_sets[timestamp_to_restore]
        backup_users_path = backup_files_info.get('users')
        backup_tasks_path = backup_files_info.get('tasks')

        if not backup_users_path or not backup_tasks_path:
            return False, "Arquivos de backup de usuários ou tarefas ausentes para o timestamp selecionado."

        try:
            pre_restore_ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f') 
            # Config.USERS_FILE, Config.TASKS_FILE, Config.BACKUP_DIR são atributos da classe Config
            if Config.USERS_FILE.exists():
                shutil.copy2(Config.USERS_FILE, Config.BACKUP_DIR / f"users_prerestore_{pre_restore_ts}.json")
            if Config.TASKS_FILE.exists():
                shutil.copy2(Config.TASKS_FILE, Config.BACKUP_DIR / f"tasks_prerestore_{pre_restore_ts}.json")
            logger.info(f"Backup de pré-restauração criado com timestamp: {pre_restore_ts}")

            shutil.copy2(backup_users_path, Config.USERS_FILE)
            logger.info(f"Arquivo de usuários restaurado de: {backup_users_path.name}")
            
            shutil.copy2(backup_tasks_path, Config.TASKS_FILE)
            logger.info(f"Arquivo de tarefas restaurado de: {backup_tasks_path.name}")
            
            return True, "Backup restaurado com sucesso!"

        except Exception as e:
            logger.error(f"Erro durante a restauração do backup {timestamp_to_restore}: {e}", exc_info=True)
            return False, f"Ocorreu um erro ao restaurar o backup: {e}"