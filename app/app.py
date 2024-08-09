import sys
import os
import pandas as pd
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Border, Side
import io
from file_utils import rename_files, get_file_metadata
from metadata_extractor import get_pdf_pages
from index_generator import generate_index, generate_excel
from gui import create_info_table, show_instructions
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QLabel, QLineEdit, QTextEdit, QMessageBox, QProgressDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sistema de Gestión de Expedientes Electrónicos Judiciales")
        self.setGeometry(100, 100, 800, 600)

        self.folder_path = ""

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.folder_button = QPushButton("Seleccionar Carpeta del Expediente", self)
        self.folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_button)

        self.folder_path_label = QLabel("Ruta de la carpeta seleccionada:", self)
        layout.addWidget(self.folder_path_label)

        self.ciudad_input = QLineEdit(self)
        self.ciudad_input.setPlaceholderText("Ciudad")
        layout.addWidget(self.ciudad_input)

        self.despacho_judicial_input = QLineEdit(self)
        self.despacho_judicial_input.setPlaceholderText("Despacho Judicial")
        layout.addWidget(self.despacho_judicial_input)

        self.serie_subserie_input = QLineEdit(self)
        self.serie_subserie_input.setPlaceholderText("Serie/Subserie documental")
        layout.addWidget(self.serie_subserie_input)

        self.num_radicacion_input = QLineEdit(self)
        self.num_radicacion_input.setPlaceholderText("Número de radicación del proceso")
        layout.addWidget(self.num_radicacion_input)

        self.partes_procesales_input = QTextEdit(self)
        self.partes_procesales_input.setPlaceholderText("Partes procesales")
        layout.addWidget(self.partes_procesales_input)

        self.generate_button = QPushButton("Generar Índice Electrónico", self)
        self.generate_button.clicked.connect(self.generate_index_electronico)
        layout.addWidget(self.generate_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta del Expediente")
        if folder_path:
            self.folder_path = folder_path
            self.folder_path_label.setText(f"Ruta de la carpeta seleccionada: {folder_path}")
        else:
            QMessageBox.warning(self, "Advertencia", "No se seleccionó ninguna carpeta.")

    def generate_index_electronico(self):
        if not self.folder_path:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una carpeta para procesar.")
            return

        progress = QProgressDialog("Generando índice electrónico...", "Cancelar", 0, 0, self)
        progress.setWindowModality(2)
        progress.show()

        try:
            # Renombrar archivos
            rename_files(self.folder_path)

            # Generar índice
            metadata = {
                'Ciudad': self.ciudad_input.text(),
                'Despacho Judicial': self.despacho_judicial_input.text(),
                'Serie/Subserie documental': self.serie_subserie_input.text(),
                'Número de radicación del proceso': self.num_radicacion_input.text(),
                'Partes procesales': self.partes_procesales_input.toPlainText()
            }
            df = generate_index(self.folder_path, metadata)

            # Generar Excel
            excel_file = generate_excel(df)
            index_file_path = os.path.join(self.folder_path, "000IndiceElectronicoC0.xlsx")

            # Reemplazar el archivo índice si ya existe
            with open(index_file_path, "wb") as f:
                f.write(excel_file.getvalue())  # Obtener los bytes del objeto BytesIO

            progress.close()
            QMessageBox.information(self, "Éxito", "Índice electrónico generado con éxito.")

            # Limpiar el formulario
            self.clear_form()
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {e}")

    def clear_form(self):
        self.folder_path = ""
        self.folder_path_label.setText("Ruta de la carpeta seleccionada:")
        self.ciudad_input.clear()
        self.despacho_judicial_input.clear()
        self.serie_subserie_input.clear()
        self.num_radicacion_input.clear()
        self.partes_procesales_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())