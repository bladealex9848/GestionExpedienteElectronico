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

El Sistema de Gestión de Expedientes Electrónicos Judiciales es una solución avanzada que combina automatización robótica de escritorio (RDA) con tecnologías modernas para optimizar la gestión de expedientes electrónicos en el ámbito judicial. Este sistema está diseñado para cumplir con los estrictos estándares del Plan Estratégico de Transformación Digital de la Rama Judicial, así como con los requisitos técnicos y funcionales del acuerdo PCSJA20-11567 de 2020, que establece el protocolo para la gestión de documentos electrónicos, su digitalización y la conformación del expediente electrónico, en su versión 2.

## Características Principales

- **Automatización de la Creación del Índice Electrónico**: El sistema automatiza el proceso de creación del índice electrónico, reduciendo significativamente el tiempo y los recursos necesarios para esta tarea crítica.
  
- **Extracción de Metadatos de Archivos**: Utiliza técnicas avanzadas para extraer metadatos de diversos tipos de archivos, asegurando una completa y precisa documentación de cada expediente.

- **Generación de Índices en Formatos Excel**: Facilita la generación de índices en formato Excel, compatible con las necesidades específicas de la gestión documental judicial.

- **Interfaces de Usuario Intuitivas**:
  - **Versión de Escritorio con PyQt5**: Ofrece una interfaz de usuario intuitiva y amigable, desarrollada con PyQt5, que permite una experiencia de usuario fluida y eficiente.
  - **Versión Web con Streamlit**: Además, cuenta con una interfaz web desarrollada utilizando Streamlit, que brinda flexibilidad y accesibilidad para usuarios que prefieren o necesitan interactuar a través de la web.

- **Cumplimiento con los Estándares Judiciales Colombianos**: El sistema se ajusta rigurosamente a los estándares y protocolos judiciales colombianos, garantizando su aplicabilidad y aceptación en el contexto legal y judicial del país.

Este proyecto representa un avance significativo en la gestión de expedientes electrónicos, ofreciendo una solución integral que no solo mejora la eficiencia y la precisión de los procesos judiciales, sino que también fomenta la transparencia y la accesibilidad de la información en el sistema judicial.

## Estructura del Proyecto
```
GestionExpedienteElectronico/
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
|   └── guia_uso.pdf
|   └── logo.png
|   └── logo_CSJ_Sucre.png
|   └── logo_CSJ_Sucre.jpg
│
├── marco_normativo/
│   └── ACUERDO PCSJA20-11567.pdf
│   └── ACUERDO PCSJA23-12094.pdf
|   └── CIRCULAR PCSJC24-23.pdf
|   └── Plan Sectorial de Desarrollo Rama Judicial 2023-2026.pdf
|   └── Protocolo para la gestión de documentos electronicos.pdf
|   └── UTDI_SGDE_ABC_V6.pdf
|
├── temp_expediente/
│   └── ... (archivos temporales)
|
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

Planeamos añadir más funcionalidades al Sistema de Gestión de Expedientes Electrónicos Judiciales con el tiempo. Las contribuciones son bienvenidas.

## Registro de Cambios

- 2024-08-10: Actualización mayor y mejoras en la versión web (v.1.3.0)
  - Rediseño completo de la interfaz web, con un panel lateral mejorado.
  - Implementación de descarga de recursos adicionales y marco normativo desde el panel lateral.
  - Adición de badges de GitHub y contador de visitantes en la página principal.
  - Mejora en la configuración de Streamlit para una mejor experiencia de usuario.
  - Optimización del manejo de archivos temporales para mejorar la seguridad y el rendimiento.
  - Implementación de manejo de errores robusto, especialmente para la carga de imágenes y recursos.
  - Preparación del proyecto para generación de ejecutable para Windows.
  - Actualización de la documentación y guías de usuario.

- 2024-08-10: Actualización de la versión web (v.1.2.0)
  - Rediseño de la interfaz web, moviendo recursos adicionales y créditos al panel lateral.
  - Simplificación del proceso de generación de índices, eliminando la opción de usar plantilla.
  - Implementación de manejo de archivos temporales para mejorar la seguridad y el rendimiento en entornos multi-usuario.
  - Adición de funcionalidad para comprimir y descargar el expediente completo con el índice generado.
  - Mejora en la gestión de recursos del servidor al procesar múltiples solicitudes simultáneas.

- 2024-08-09: Actualización y correcciones (v.1.1.1)
  - Mejora en el manejo de la plantilla Excel con macros (.xlsm).
  - Corrección del problema de generación de archivos .xlsx adicionales.
  - Optimización del proceso de renombrado de archivos para respetar la numeración existente.
  - Ajuste en la lógica de generación del índice para excluir correctamente archivos no deseados.
  - Mejora en la compatibilidad con diferentes sistemas operativos.
  - Actualización de la documentación y guías de usuario.

- 2024-08-09: Actualización mayor (v.1.1.0)
  - Implementación de la versión de escritorio utilizando PyQt5.
  - Adición de la funcionalidad para generar índices tanto desde cero como utilizando una plantilla.
  - Mejora en la extracción de metadatos para soportar múltiples tipos de archivos.
  - Implementación de un manejador de Excel para crear y modificar archivos de índice.
  - Actualización de la estructura del proyecto para soportar tanto la versión web como la de escritorio.
  - Adición de pruebas unitarias para las nuevas funcionalidades.
  - Actualización de la documentación para reflejar los nuevos cambios y características.

- 2024-08-08: Primera versión (v.1.0.0)
  - Lanzamiento inicial del Sistema de Gestión de Expedientes Electrónicos Judiciales.
  - Implementación de la versión web utilizando Streamlit.

## Créditos

Este proyecto es una evolución del trabajo inicial realizado por [HammerDev99 Daniel](https://github.com/HammerDev99/GestionExpedienteElectronico_Version1), a quien se le reconoce y agradece por sentar las bases de esta herramienta.

Desarrollado y mantenido por Alexander Oviedo Fadul, Profesional Universitario Grado 11 en el Consejo Seccional de la Judicatura de Sucre.

[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul-49434b9a/)

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [MIT License](https://opensource.org/licenses/MIT) para más detalles.