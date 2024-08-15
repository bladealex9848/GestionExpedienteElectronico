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

### 1. Arquitectura del Sistema

El Sistema de Gestión de Expedientes Electrónicos Judiciales está construido utilizando las siguientes tecnologías:

- Lenguaje de programación: Python 3.x
- Frameworks:
  - Interfaz de escritorio: PyQt5
  - Interfaz web: Streamlit
- Principales librerías:
  - pandas: Para manipulación y análisis de datos
  - openpyxl: Para manejo de archivos Excel
  - PyPDF2: Para extracción de metadatos de archivos PDF
  - xlwings: Para interacción avanzada con Excel (macros)

### 2. Estructura del Proyecto

```
GestionExpedienteElectronico/
│
├── app.py                    # Aplicación de escritorio (PyQt5)
├── main.py                   # Aplicación web (Streamlit)
├── index_generator.py        # Lógica de generación del índice
├── file_utils.py             # Utilidades para manejo de archivos
├── metadata_extractor.py     # Extracción de metadatos
├── excel_handler.py          # Manejo de archivos Excel
│
├── assets/                   # Recursos estáticos
├── tests/                    # Pruebas unitarias
│
├── requirements.txt          # Dependencias del proyecto
├── .gitignore
└── README.md
```

### 3. Componentes Principales

#### 3.1 app.py (Aplicación de Escritorio)
- Clase `MainWindow`: Interfaz gráfica principal
- Clase `IndexGeneratorThread`: Hilo para procesamiento asíncrono

#### 3.2 main.py (Aplicación Web)
- Función `main()`: Punto de entrada de la aplicación Streamlit
- Funciones auxiliares para manejo de archivos y UI

#### 3.3 index_generator.py
- `generate_index_from_scratch()`: Genera el índice sin plantilla
- `generate_index_from_template()`: Genera el índice usando plantilla Excel

#### 3.4 file_utils.py
- `rename_files()`: Renombra archivos según el protocolo
- `get_file_metadata()`: Obtiene metadatos básicos de archivos

#### 3.5 metadata_extractor.py
- Funciones específicas para extraer metadatos de diferentes tipos de archivos (PDF, Word, Excel, imágenes)

#### 3.6 excel_handler.py
- `save_excel_file()`: Guarda el índice en formato Excel
- `create_new_excel()`: Crea un nuevo archivo Excel con formato
- `fill_template_xlwings()`: Llena la plantilla Excel usando xlwings

### 4. Flujo de Datos

1. El usuario selecciona la carpeta del expediente o carga archivos (versión web).
2. Se renombran los archivos según el protocolo.
3. Se extraen los metadatos de cada archivo.
4. Se genera el índice electrónico (DataFrame).
5. Se crea o actualiza el archivo Excel del índice.
6. Se presenta el resultado al usuario.

### 5. Seguridad y Manejo de Errores

- Validación de entradas de usuario en la interfaz.
- Manejo de excepciones en procesos críticos como la lectura de archivos y generación del índice.
- Uso de directorios temporales para el manejo seguro de archivos en la versión web.

### 6. Requisitos del Sistema

- Python 3.7+
- Dependencias listadas en `requirements.txt`
- Para la versión de escritorio: Sistema operativo compatible con PyQt5
- Para la versión web: Navegador web moderno

### 7. Instalación y Configuración

1. Clonar el repositorio:
   ```
   git clone https://github.com/bladealex9848/GestionExpedienteElectronico.git
   ```
2. Crear y activar un entorno virtual.
3. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

### 8. Despliegue

- Versión de Escritorio: Generar ejecutable usando PyInstaller
- Versión Web: Desplegar en plataforma compatible con Streamlit (ej. Streamlit Share, Heroku)

### 9. Mantenimiento y Actualización

- Actualizar dependencias periódicamente.
- Realizar pruebas unitarias antes de cada actualización mayor.
- Mantener compatibilidad con versiones anteriores de los formatos de archivo.

### 10. Consideraciones de Rendimiento

- La aplicación está diseñada para manejar expedientes de tamaño moderado.
- Para expedientes muy grandes, considerar procesamiento por lotes.

### 11. Integración y APIs

- Actualmente, el sistema funciona de manera independiente.
- Potencial para futura integración con sistemas de gestión judicial mediante APIs.

### 12. Logging y Monitoreo

- Implementar un sistema de logging para rastrear errores y uso.
- Considerar la integración de herramientas de monitoreo para la versión web.

Este manual técnico proporciona una visión general completa de la arquitectura y funcionamiento del Sistema de Gestión de Expedientes Electrónicos Judiciales. Para más detalles sobre componentes específicos, consulte los comentarios en el código fuente de cada archivo.

## Manual de Usuario

### 1. Introducción

El Sistema de Gestión de Expedientes Electrónicos Judiciales es una herramienta diseñada para facilitar la creación y gestión de índices electrónicos para expedientes judiciales. Este manual le guiará a través de las funcionalidades principales del sistema, tanto en su versión de escritorio como en su versión web.

### 2. Requisitos del Sistema

- Para la versión de escritorio:
  - Sistema operativo: Windows 10/11, macOS 10.14+, o Linux (distribución reciente)
  - 4 GB de RAM mínimo
  - 200 MB de espacio en disco duro
- Para la versión web:
  - Navegador web actualizado (Chrome, Firefox, Safari, Edge)
  - Conexión a internet estable

### 3. Instalación (Versión de Escritorio)

1. Descargue el ejecutable portable desde [enlace de descarga](https://gestionexpedienteelectronico.streamlit.app).
2. Ejecute el archivo descargado y siga las instrucciones en pantalla.
3. No se requiere instalación adicional.

### 4. Acceso (Versión Web)

1. Abra su navegador web.
2. Visite la URL: [URL de la aplicación web](https://gestionexpedienteelectronico.streamlit.app).
3. No se requiere instalación ni registro.

### 5. Interfaz de Usuario

#### 5.1 Versión de Escritorio

- **Ventana Principal**: Contiene todos los controles necesarios para la gestión de expedientes.
- **Botón "Seleccionar Carpeta"**: Permite elegir la carpeta que contiene los archivos del expediente.
- **Botón "Generar Índice"**: Inicia el proceso de creación del índice electrónico.
- **Opciones de Generación**: Permite elegir entre generar desde cero o usar una plantilla.
- **Barra de Progreso**: Muestra el avance del proceso de generación.
- **Área de Información**: Muestra mensajes y resultados del proceso.

#### 5.2 Versión Web

- **Panel Principal**: Área central donde se cargan los archivos y se inicia el proceso.
- **Barra Lateral**: Contiene enlaces a recursos adicionales y marco normativo.
- **Área de Carga de Archivos**: Permite subir los documentos del expediente.
- **Botón "Generar Índice Electrónico"**: Inicia el proceso de creación del índice.

### 6. Uso Básico

#### 6.1 Generar un Índice Electrónico (Versión de Escritorio)

1. Abra la aplicación.
2. Haga clic en "Seleccionar Carpeta" y elija la carpeta que contiene los archivos del expediente.
3. Seleccione la opción de generación (desde cero o usar plantilla).
4. Haga clic en "Generar Índice".
5. Espere a que el proceso termine. El índice se guardará en la misma carpeta del expediente.

#### 6.2 Generar un Índice Electrónico (Versión Web)

1. Acceda a la aplicación web.
2. Arrastre y suelte los archivos del expediente en el área de carga o use el botón para seleccionarlos.
3. Una vez cargados todos los archivos, haga clic en "Generar Índice Electrónico".
4. Espere a que el proceso termine. Se le proporcionará un enlace para descargar el índice generado.

### 7. Funciones Avanzadas

- **Uso de Plantillas**: Para usar una plantilla personalizada, seleccione la opción correspondiente antes de generar el índice (solo versión de escritorio).
- **Descarga de Recursos**: Utilice los enlaces en la barra lateral (versión web) o los botones correspondientes (versión de escritorio) para descargar la plantilla Excel y la guía de uso.

### 8. Solución de Problemas

- **El índice no se genera**: Asegúrese de que todos los archivos en la carpeta sean válidos y accesibles.
- **Errores en la carga de archivos (versión web)**: Verifique que el tamaño total de los archivos no exceda el límite permitido.
- **La aplicación se cierra inesperadamente**: Asegúrese de tener la última versión instalada y que su sistema cumpla con los requisitos mínimos.

### 9. Mejores Prácticas

- Organice los archivos del expediente en una sola carpeta antes de generar el índice.
- Utilice nombres de archivo descriptivos y cortos.
- Actualice regularmente el índice si añade o modifica documentos en el expediente.

### 10. Soporte y Contacto

Para obtener ayuda adicional o reportar problemas:

- Visite nuestra [página de GitHub](https://github.com/bladealex9848/GestionExpedienteElectronico/issues) para reportar problemas.
- Contacte al soporte técnico en [correo electrónico de soporte](aoviedof@cendoj.ramajudicial.gov.co) para preguntas más específicas o problemas técnicos.

### 11. Glosario

- **Índice Electrónico**: Documento que lista y describe todos los archivos que componen un expediente judicial electrónico.
- **Metadatos**: Información sobre los archivos, como fecha de creación, tamaño, tipo, etc.
- **Plantilla**: Archivo Excel preformateado para la creación de índices electrónicos.

### 12. Actualizaciones

- Visite regularmente [URL del repositorio o sitio web](https://gestionexpedienteelectronico.streamlit.app/) para obtener las últimas actualizaciones y mejoras del sistema.

Este manual de usuario proporciona una guía completa para utilizar el Sistema de Gestión de Expedientes Electrónicos Judiciales. Para información más detallada sobre aspectos técnicos o legales, consulte el Manual Técnico o la documentación legal proporcionada.

## Contribución

Planeamos añadir más funcionalidades al Sistema de Gestión de Expedientes Electrónicos Judiciales con el tiempo. Las contribuciones son bienvenidas.

## Registro de Cambios

- 2024-08-15: Actuaización menor y corrección de errores (v.1.3.1)
  - Corrección de errores menores en la interfaz de usuario y el proceso de generación de índices.
  - Supreción de las carpetas marco_normativo y temp_expediente en la versión web y escritorio para optimizar el espacio de almacenamiento y carga de archivos.
  - Mejoras en la gestión de errores y mensajes de usuario para una experiencia más fluida y menos propensa a errores.
  - En la versión de escritorio se elimino el guardar el índice electrónico (xlsx) en la carpeta del expediente y se dejo solamente el guardado del índice electrónico (xlsm) en la carpeta del expediente para optimizar el espacio de almacenamiento y carga de archivos.

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