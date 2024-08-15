import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, 
                             QVBoxLayout, QWidget, QLabel, QProgressBar, QHBoxLayout, 
                             QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from index_generator import generate_index_from_template
from file_utils import rename_files
from excel_handler import save_excel_file
import shutil

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class IndexGeneratorThread(QThread):
    progress_update = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, folder_path):
        QThread.__init__(self)
        self.folder_path = folder_path

    def run(self):
        try:
            self.progress_update.emit(25)
            rename_files(self.folder_path)
            
            # Generar el índice electrónico a partir de la plantilla
            self.progress_update.emit(75)
            template_path = resource_path("assets/000IndiceElectronicoC0.xlsm")
            df = generate_index_from_template(self.folder_path, template_path)
            
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
        logo_path = resource_path("assets/logo_CSJ_Sucre.jpg")
        pixmap = QPixmap(logo_path)
        if pixmap.isNull():
            print(f"No se pudo cargar la imagen: {logo_path}")
        else:
            logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        main_layout.addSpacing(20)

        # Área de información
        self.info_label = QLabel("Seleccione una carpeta para comenzar.")
        self.info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_label)

        # Créditos
        credits_label = QLabel("Desarrollado por Alexander Oviedo Fadul\nProfesional Universitario Grado 11\nConsejo Seccional de la Judicatura de Sucre\nv.1.3.1")
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

        self.thread = IndexGeneratorThread(self.folder_path)
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
        template_path = resource_path("assets/000IndiceElectronicoC0.xlsm")
        destination, _ = QFileDialog.getSaveFileName(self, "Guardar Plantilla", "000IndiceElectronicoC0.xlsm", "Excel Files (*.xlsm)")
        if destination:
            try:
                shutil.copy(template_path, destination)
                QMessageBox.information(self, "Éxito", "Plantilla descargada con éxito.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo descargar la plantilla: {str(e)}")

    def download_guide(self):
        guide_path = resource_path("assets/guia_uso.pdf")
        destination, _ = QFileDialog.getSaveFileName(self, "Guardar Guía", "guia_uso.pdf", "PDF Files (*.pdf)")
        if destination:
            try:
                shutil.copy(guide_path, destination)
                QMessageBox.information(self, "Éxito", "Guía descargada con éxito.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo descargar la guía: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
