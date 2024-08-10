import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, 
                             QVBoxLayout, QWidget, QLabel, QProgressBar, QHBoxLayout, 
                             QRadioButton, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from index_generator import generate_index_from_scratch, generate_index_from_template
from file_utils import rename_files
from excel_handler import save_excel_file
import shutil

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Usar esta función para todas las rutas de archivos
logo_path = resource_path("assets/logo.png")
template_path = resource_path("assets/000IndiceElectronicoC0.xlsm")

class IndexGeneratorThread(QThread):
    progress_update = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, folder_path, use_template):
        QThread.__init__(self)
        self.folder_path = folder_path
        self.use_template = use_template

    def run(self):
        try:
            self.progress_update.emit(25)
            rename_files(self.folder_path)
            
            self.progress_update.emit(50)
            if self.use_template:
                template_path = os.path.join('assets', '000IndiceElectronicoC0.xlsm')
                df = generate_index_from_template(self.folder_path, template_path)
            else:
                df = generate_index_from_scratch(self.folder_path)
            
            self.progress_update.emit(75)
            index_file_path = os.path.join(self.folder_path, "000IndiceElectronicoC0.xlsx")
            save_excel_file(df, index_file_path, self.use_template)
            
            self.progress_update.emit(100)
            self.finished.emit(True, "Índice electrónico generado con éxito.")
        except Exception as e:
            self.finished.emit(False, str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.folder_path = ""
        self.setWindowTitle("Sistema de Gestión de Expedientes Electrónicos Judiciales")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {background-color: black;}
            QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            font-family: Montserrat;
            }
            QPushButton:hover {background-color: #45a049;}
            QRadioButton {
            font-size: 14px;
            font-family: Montserrat;
            }
            QLabel {
            color: white;
            font-family: Montserrat;
            }
        """)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Logo
        logo_label = QLabel()
        pixmap = QPixmap("assets/logo_CSJ_Sucre.jpg")        
        # Aplicar el fondo blanco a la imagen        
        logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # Ícono de la ventana
        main_layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        main_layout.addSpacing(20)

        # Título
        title_label = QLabel("Sistema de Gestión de Expedientes Electrónicos Judiciales")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        main_layout.addSpacing(40)

        # Botones
        buttons_layout = QHBoxLayout()
        self.select_folder_btn = QPushButton("Seleccionar Carpeta")
        self.generate_index_btn = QPushButton("Generar Índice")
        self.download_template_btn = QPushButton("Descargar Plantilla")
        self.download_guide_btn = QPushButton("Descargar Guía")
        
        buttons_layout.addWidget(self.select_folder_btn)
        buttons_layout.addWidget(self.generate_index_btn)
        buttons_layout.addWidget(self.download_template_btn)
        buttons_layout.addWidget(self.download_guide_btn)
        
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.generate_index_btn.clicked.connect(self.generate_index)
        self.download_template_btn.clicked.connect(self.download_template)
        self.download_guide_btn.clicked.connect(self.download_guide)
        
        main_layout.addLayout(buttons_layout)
        main_layout.addSpacing(20)

        # Opciones de generación
        options_layout = QHBoxLayout()
        self.from_scratch_radio = QRadioButton("Generar desde cero")
        self.use_template_radio = QRadioButton("Usar plantilla")
        self.from_scratch_radio.setChecked(True)
        options_layout.addWidget(self.from_scratch_radio)
        options_layout.addWidget(self.use_template_radio)
        main_layout.addLayout(options_layout)
        main_layout.addSpacing(20)
        
        # Color de la letra en negro
        self.from_scratch_radio.setStyleSheet("color: white;")
        self.use_template_radio.setStyleSheet("color: white;")
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        main_layout.addSpacing(20)

        # Área de información
        self.info_label = QLabel("Seleccione una carpeta para comenzar.")
        self.info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_label)

        # Créditos
        credits_label = QLabel("Desarrollado por Alexander Oviedo Fadul\nProfesional Universitario Grado 11\nConsejo Seccional de la Judicatura de Sucre")
        credits_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(credits_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def select_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta del Expediente")
        if self.folder_path:
            self.info_label.setText(f"Carpeta seleccionada: {self.folder_path}")
        else:
            self.info_label.setText("No se seleccionó ninguna carpeta.")

    def generate_index(self):
        if not self.folder_path:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una carpeta para procesar.")
            return

        use_template = self.use_template_radio.isChecked()
        self.thread = IndexGeneratorThread(self.folder_path, use_template)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.finished.connect(self.process_finished)
        self.thread.start()

        self.select_folder_btn.setEnabled(False)
        self.generate_index_btn.setEnabled(False)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def process_finished(self, success, message):
        self.select_folder_btn.setEnabled(True)
        self.generate_index_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {message}")
        self.progress_bar.setValue(0)

    def download_template(self):
        destination, _ = QFileDialog.getSaveFileName(self, "Guardar Plantilla", "000IndiceElectronicoC0.xlsm", "Excel Files (*.xlsm)")
        if destination:
            shutil.copy("assets/000IndiceElectronicoC0.xlsm", destination)
            QMessageBox.information(self, "Éxito", "Plantilla descargada con éxito.")

    def download_guide(self):
        destination, _ = QFileDialog.getSaveFileName(self, "Guardar Guía", "guia_uso.pdf", "PDF Files (*.pdf)")
        if destination:
            shutil.copy("assets/guia_uso.pdf", destination)
            QMessageBox.information(self, "Éxito", "Guía descargada con éxito.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())