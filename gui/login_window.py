import tkinter as tk
from tkinter import messagebox, ttk
import os # Necessário para os.path.exists, mas Config já usa pathlib

from config import Config, logger, HAS_PIL
if HAS_PIL:
    from PIL import Image, ImageTk

from services import UserService
from .main_window import MainWindow # Importação relativa para MainWindow

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        
        if Config.ICON_PATH.exists():
            try:
                self.root.iconbitmap(str(Config.ICON_PATH))
            except Exception as e:
                logger.warning(f"Não foi possível carregar o ícone da aplicação ({Config.ICON_PATH}): {str(e)}")
        
        self.root.title(f"{Config.APP_NAME} - Login")
        
        # Centralizar janela
        window_width = 450
        window_height = 350
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)

        self.setup_ui()
        self.root.mainloop()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        if Config.LOGO_PATH.exists() and HAS_PIL:
            try:
                image = Image.open(Config.LOGO_PATH)
                # Redimensionar mantendo a proporção, se possível, ou usar um tamanho fixo como antes
                # Exemplo: image.thumbnail((200, 60)) # thumbnail modifica a imagem in-place
                image = image.resize((200, 60), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(image, master=self.root)
                logo_label = ttk.Label(main_frame, image=self.logo_img)
                logo_label.pack(pady=(0, 10))
            except Exception as e:
                logger.warning(f"Não foi possível carregar a logo ({Config.LOGO_PATH}): {str(e)}")
        else:
            logger.info(f"Logo não encontrada em {Config.LOGO_PATH} ou PIL não disponível.")


        title_label = ttk.Label(
            main_frame,
            text=Config.APP_NAME,
            font=("Arial", 16, "bold"),
            foreground="#2c3e50" # Exemplo de cor
        )
        title_label.pack(pady=(0, 20))

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=10)

        ttk.Label(form_frame, text="Usuário:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)

        ttk.Label(form_frame, text="Senha:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        
        form_frame.columnconfigure(1, weight=1) # Faz a coluna do entry expandir

        # Bind Enter key para login
        self.username_entry.bind("<Return>", lambda event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda event: self.validate_login())


        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)

        login_button = ttk.Button(button_frame, text="Entrar", command=self.validate_login, style="Accent.TButton")
        login_button.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        exit_button = ttk.Button(button_frame, text="Sair", command=self.root.quit)
        exit_button.pack(side=tk.RIGHT, padx=10, expand=True, fill=tk.X)
        
        # Adicionar um estilo para o botão de login (opcional, requer tema como 'azure')
        # style = ttk.Style()
        # style.configure("Accent.TButton", font=("Arial", 10, "bold"))


        self.username_entry.focus_set()

    def validate_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Erro de Login", "Por favor, preencha todos os campos.", parent=self.root)
            return

        users = UserService.load_users()

        if username not in users:
            logger.warning(f"Tentativa de login com usuário inexistente: {username}")
            messagebox.showerror("Erro de Login", "Credenciais inválidas.", parent=self.root)
            return

        if not UserService.verify_password(users[username]['password_hash'], password):
            logger.warning(f"Tentativa de login com senha incorreta para usuário: {username}")
            messagebox.showerror("Erro de Login", "Credenciais inválidas.", parent=self.root)
            return

        logger.info(f"Usuário {username} logado com sucesso.")
        self.root.destroy() # Fecha a janela de login
        MainWindow(username, users[username]['level']) # Abre a janela principal