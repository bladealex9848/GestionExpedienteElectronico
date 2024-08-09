import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QLabel, QMessageBox, QProgressDialog, QRadioButton, QButtonGroup
from PyQt5.QtCore import Qt
from index_generator import generate_index_from_scratch, generate_index_from_template
from file_utils import rename_files
from excel_handler import save_excel_file

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Expedientes Electrónicos Judiciales")
        self.setGeometry(100, 100, 600, 300)
        self.folder_path = ""
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.folder_button = QPushButton("Seleccionar Carpeta del Expediente", self)
        self.folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_button)

        self.folder_path_label = QLabel("Ruta de la carpeta seleccionada:", self)
        layout.addWidget(self.folder_path_label)

        self.radio_group = QButtonGroup(self)
        self.radio_from_scratch = QRadioButton("Generar índice desde cero", self)
        self.radio_from_template = QRadioButton("Usar plantilla para generar índice", self)
        self.radio_from_scratch.setChecked(True)
        self.radio_group.addButton(self.radio_from_scratch)
        self.radio_group.addButton(self.radio_from_template)
        layout.addWidget(self.radio_from_scratch)
        layout.addWidget(self.radio_from_template)

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

        progress = QProgressDialog("Generando índice electrónico...", "Cancelar", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        try:
            # Renombrar archivos
            rename_files(self.folder_path)
            progress.setValue(25)

            # Generar índice
            if self.radio_from_scratch.isChecked():
                df = generate_index_from_scratch(self.folder_path)
            else:
                template_path = os.path.join(os.path.dirname(__file__), 'assets', '000IndiceElectronicoC0.xlsm')
                df = generate_index_from_template(self.folder_path, template_path)
            
            progress.setValue(75)

            # Guardar el archivo Excel
            index_file_path = os.path.join(self.folder_path, "000IndiceElectronicoC0.xlsx")
            save_excel_file(df, index_file_path, self.radio_from_template.isChecked())

            progress.setValue(100)
            QMessageBox.information(self, "Éxito", "Índice electrónico generado con éxito.")

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Salir', '¿Está seguro que desea salir?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())