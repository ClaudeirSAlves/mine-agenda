# AgendaCompPro

**AgendaCompPro** é um sistema de gerenciamento de tarefas com controle de usuários, níveis de acesso, relatórios em PDF e suporte a backups. A interface é amigável, construída com Tkinter, e o projeto é empacotado como um executável para Windows.

---

## 📦 Última Versão

**v1.0.0** - 09/05/2025

- Interface de login e controle de usuários
- Cadastro, edição, conclusão e reabertura de tarefas
- Geração de relatórios em PDF
- Backup e restauração de dados
- Build `.exe` com PyInstaller

---

## ✅ Requisitos

- Windows 10 ou superior
- Não é necessário ter Python instalado (o `.exe` é autossuficiente)

---

## 🚀 Instalação

1. Baixe a versão mais recente na aba [Releases](https://github.com/ClaudeirSAlves/mine-agenda/releases)
2. Execute o arquivo `AgendaCompPro-v1.0.0.exe`
3. A aplicação irá iniciar na tela de login

> O usuário padrão é `admin` com senha `admin123`.

---

## 🛠 Tecnologias Utilizadas

- Python 3.11+
- Tkinter
- PyInstaller
- Pillow
- FPDF
- Git

---

## 🗂 Estrutura do Projeto

- `AgendaCompPro.py`: ponto de entrada principal
- `config.py`: configurações da aplicação
- `gui/`: janelas (login, principal, usuários, backups)
- `services/`: lógica de usuários e tarefas
- `assets/`: ícones e logo da aplicação
- `release/`: executáveis e instaladores prontos

---

## 📄 Licença

Este projeto é distribuído sob licença pessoal/interna para fins de demonstração e uso controlado.

---

**Desenvolvido por Claudeir de Souza Alves**
