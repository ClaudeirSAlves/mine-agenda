import tkinter as tk
from tkinter import ttk
from fpdf import FPDF # Dependência: pip install fpdf
from datetime import datetime
from pathlib import Path 
from typing import List, Dict, Optional # Importações de tipos

from config import Config, logger, HAS_PIL 

class Tooltip:
    """Cria um tooltip (dica de ferramenta) para um widget."""
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") 
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20 

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True) 
        self.tooltip_window.wm_geometry(f"+{x}+{y}") 

        label = ttk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0", 
            relief=tk.SOLID,
            borderwidth=1,
            padding=(5, 3) 
        )
        label.pack(ipadx=1) 

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class PDFGenerator:
    """Classe responsável por gerar relatórios de tarefas em formato PDF."""
    STYLES = {
        'title': {'font': 'Arial', 'style': 'B', 'size': 18, 'color': (0, 0, 128)},
        'header': {'font': 'Arial', 'style': 'B', 'size': 14, 'color': (0, 64, 128)},
        'subheader': {'font': 'Arial', 'style': '', 'size': 10, 'color': (50, 50, 50)},
        'table_header': {'font': 'Arial', 'style': 'B', 'size': 9, 'color': (255, 255, 255)}, 
        'table_row': {'font': 'Arial', 'style': '', 'size': 9, 'color': (0, 0, 0)},
        'footer': {'font': 'Arial', 'style': 'I', 'size': 8, 'color': (128, 128, 128)}
    }
    COLORS = {
        'table_header_fill': (70, 130, 180), 
        'row_even': (240, 248, 255),    
        'row_odd': (255, 255, 255),     
    }
    CELL_HEIGHT = 8 # Altura padrão da célula da tabela em mm

    @staticmethod
    def _format_datetime_pdf(iso_datetime_str: Optional[str]) -> str: 
        if not iso_datetime_str: return "N/A"
        try:
            return datetime.fromisoformat(iso_datetime_str).strftime('%d/%m/%Y %H:%M')
        except ValueError: return iso_datetime_str[:16] 

    @staticmethod
    def _apply_style(pdf: FPDF, style_name: str):
        style = PDFGenerator.STYLES[style_name]
        pdf.set_font(style['font'], style['style'], style['size'])
        pdf.set_text_color(*style['color'])

    @staticmethod
    def _add_document_header(pdf: FPDF, report_title: str):
        if Config.LOGO_PATH.exists() and HAS_PIL:
            try:
                pdf.image(str(Config.LOGO_PATH), x=10, y=8, w=30) 
                pdf.ln(15) 
            except Exception as e:
                logger.warning(f"Não foi possível adicionar logo ao PDF ({Config.LOGO_PATH}): {e}")
                pdf.ln(10)
        else:
            pdf.ln(10)

        PDFGenerator._apply_style(pdf, 'title')
        pdf.cell(0, 10, f"{Config.APP_NAME} - Relatório", ln=True, align='C')
        PDFGenerator._apply_style(pdf, 'header')
        pdf.cell(0, 10, report_title, ln=True, align='C')
        PDFGenerator._apply_style(pdf, 'subheader')
        pdf.cell(0, 7, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='C')
        pdf.ln(7) 

    @staticmethod
    def _get_priority_label_pdf(priority_value: int) -> str:
        return {1: "Baixa", 2: "Média", 3: "Alta"}.get(priority_value, "N/D")

    @staticmethod
    def generate_task_report(tasks_data: List[Dict], report_type: str) -> str:
        try:
            Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            
            class CustomFPDF(FPDF): 
                def footer(self):
                    self.set_y(-15)
                    PDFGenerator._apply_style(self, 'footer') 
                    self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", border=0, align='C')

            pdf = CustomFPDF(orientation='P', unit='mm', format='A4') 
            pdf.alias_nb_pages() 
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15) 
            pdf.set_left_margin(10)
            pdf.set_right_margin(10)

            report_title = f"Listagem de Tarefas {report_type.capitalize()}"
            PDFGenerator._add_document_header(pdf, report_title)
            
            col_widths = {'id': 15, 'desc': 70, 'prio': 20, 'cat': 30, 'criada': 25, 'status': 30}
            headers = ['ID', 'Descrição', 'Prior.', 'Categoria', 'Criada em', 'Status']

            if report_type.lower() == "completed" or report_type.lower() == "concluídas":
                col_widths['concluida'] = 25 
                headers.append('Concluída em')
                col_widths['desc'] = 50 
                col_widths['cat'] = 25
                col_widths['status'] = 20 # Reduzido para caber 'concluida'
                # Total: 15+50+20+25+25+20+25 = 180. OK.

            PDFGenerator._apply_style(pdf, 'table_header')
            pdf.set_fill_color(*PDFGenerator.COLORS['table_header_fill'])
            for i, header_text in enumerate(headers):
                col_name = list(col_widths.keys())[i]
                pdf.cell(col_widths[col_name], PDFGenerator.CELL_HEIGHT, header_text, border=1, ln=0, align='C', fill=True)
            pdf.ln()

            PDFGenerator._apply_style(pdf, 'table_row')
            fill = False 
            for task_dict in tasks_data:
                pdf.set_fill_color(*(PDFGenerator.COLORS['row_even'] if fill else PDFGenerator.COLORS['row_odd']))
                
                row_values = [
                    task_dict.get('task_id', '')[:8], 
                    task_dict.get('description', ''),
                    PDFGenerator._get_priority_label_pdf(task_dict.get('priority', 1)),
                    task_dict.get('category', 'N/D')[:25], # Limita caracteres da categoria
                    PDFGenerator._format_datetime_pdf(task_dict.get('created_at')),
                    "Concluída" if task_dict.get('is_completed') else "Pendente"
                ]
                if report_type.lower() == "completed" or report_type.lower() == "concluídas":
                    row_values.append(PDFGenerator._format_datetime_pdf(task_dict.get('completed_at')))

                # Guarda a posição Y inicial da linha
                y_start_of_row = pdf.get_y()
                x_pos = pdf.get_x() # Margem esquerda (ex: 10)

                for i, col_name_key in enumerate(list(col_widths.keys())[:len(row_values)]):
                    width = col_widths[col_name_key]
                    text = str(row_values[i])
                    
                    # Define a posição X,Y para cada célula da linha
                    pdf.set_xy(x_pos, y_start_of_row)
                    
                    if col_name_key == 'desc': 
                        pdf.multi_cell(width, PDFGenerator.CELL_HEIGHT, text, border=1, align='L', fill=fill)
                        # multi_cell com ln (padrão 0) avança X para x_start + width e Y para y_start + H
                        # No entanto, o FPDF padrão pode se comportar de forma que o Y é atualizado para a próxima linha.
                        # Por segurança, após um multi_cell, é bom resetar X e Y para a próxima célula *na mesma linha lógica*.
                    else:
                        pdf.cell(width, PDFGenerator.CELL_HEIGHT, text, border=1, ln=0, align='C' if col_name_key != 'cat' else 'L', fill=fill)
                    
                    x_pos += width # Avança a posição X para a próxima célula na linha

                # Após todas as células da linha, avança para a próxima linha da tabela
                pdf.ln(PDFGenerator.CELL_HEIGHT) 
                fill = not fill 

            report_filename = f"relatorio_tarefas_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            report_file_path = Config.REPORTS_DIR / report_filename
            
            pdf.output(str(report_file_path), 'F') 

            logger.info(f"Relatório PDF gerado com sucesso: {report_file_path}")
            return str(report_file_path)

        except Exception as e:
            logger.error(f"Erro ao gerar relatório PDF: {str(e)}", exc_info=True)
            raise RuntimeError(f"Falha ao gerar o relatório PDF: {str(e)}")