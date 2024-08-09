# Sistema de Gestión de Expedientes Electrónicos Judiciales

## Tabla de Contenidos
1. [Descripción](#descripción)
2. [Características](#características)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Instalación](#instalación)
5. [Uso](#uso)
6. [Manual Técnico](#manual-técnico)
7. [Manual de Usuario](#manual-de-usuario)
8. [Contribución](#contribución)
9. [Registro de Cambios](#registro-de-cambios)
10. [Créditos](#créditos)
11. [Licencia](#licencia)

## Descripción

El Sistema de Gestión de Expedientes Electrónicos Judiciales es una solución RDA (Robotic Desktop Automation) que automatiza la creación y diligenciamiento del formato índice electrónico con los metadatos de los archivos que conforman un expediente electrónico judicial. Este proyecto se adhiere a los estándares establecidos en el Plan Estratégico de Transformación Digital de la Rama Judicial y cumple con los parámetros técnicos y funcionales del acuerdo PCSJA20-11567 de 2020 "Protocolo para la gestión de documentos electrónicos, digitalización y conformación del expediente electrónico" Versión 2.

## Características

- Automatización de la creación del índice electrónico.
- Extracción de metadatos de archivos.
- Generación de índices en formatos Excel.
- Interfaz de usuario intuitiva basada en PyQt5 para la versión de escritorio.
- Interfaz web utilizando Streamlit.
- Cumplimiento con los estándares judiciales colombianos.

## Estructura del Proyecto
```
sistema_gestion_expedientes/
│
├── app.py
├── main.py
├── index_generator.py
├── file_utils.py
├── metadata_extractor.py
├── excel_handler.py
│
├── assets/
│   └── 000IndiceElectronicoC0.xlsm
│
├── tests/
│   └── test_expediente_processor.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Instalación

1. Clonar el repositorio:
git clone https://github.com/bladealex9848/GestionExpedienteElectronico.git

2. Navegar al directorio del proyecto:
cd GestionExpedienteElectronico

3. Crear un entorno virtual:
- En Windows:
  ```
  python -m venv venv
  .\venv\Scripts\activate
  ```
- En macOS y Linux:
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```

4. Instalar las dependencias:
```
pip install --upgrade pip
pip install watchdog
pip install -r requirements.txt
```

## Uso

Para ejecutar la versión de escritorio:
```
python app.py
```
Para ejecutar la versión web:
```
streamlit run main.py
```
Siga las instrucciones en la interfaz de usuario para cargar y procesar los expedientes.

## Manual Técnico

[Incluir aquí detalles técnicos del proyecto]

## Manual de Usuario

[Incluir aquí instrucciones detalladas para el usuario final]

## Contribución

Las contribuciones son bienvenidas. Por favor, siga estos pasos:

1. Haga fork del repositorio.
2. Cree una nueva rama (`git checkout -b feature/AmazingFeature`).
3. Haga commit de sus cambios (`git commit -m 'Add some AmazingFeature'`).
4. Haga Push a la rama (`git push origin feature/AmazingFeature`).
5. Abra un Pull Request.

## Registro de Cambios

- 2024-08-09: Actualización mayor (v.1.1.0)
  - Implementación de la versión de escritorio utilizando PyQt5.
  - Adición de la funcionalidad para generar índices tanto desde cero como utilizando una plantilla.
  - Mejora en la extracción de metadatos para soportar múltiples tipos de archivos.
  - Implementación de un manejador de Excel para crear y modificar archivos de índice.
  - Actualización de la estructura del proyecto para soportar tanto la versión web como la de escritorio.
  - Adición de pruebas unitarias para las nuevas funcionalidades.
  - Actualización de la documentación para reflejar los nuevos cambios y características.

- 2024-08-08: Primera versión. (v.1.0.0)
  - Lanzamiento inicial del Sistema de Gestión de Expedientes Electrónicos Judiciales.
  - Implementación de la versión web utilizando Streamlit.

## Créditos

Este proyecto es una evolución del trabajo inicial realizado por [HammerDev99 Daniel](https://github.com/HammerDev99/GestionExpedienteElectronico_Version1), a quien se le reconoce y agradece por sentar las bases de esta herramienta.

Desarrollado y mantenido por Alexander Oviedo Fadul, Profesional Universitario Grado 11 en el Consejo Seccional de la Judicatura de Sucre.

[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!)

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [MIT License](https://opensource.org/licenses/MIT) para más detalles.