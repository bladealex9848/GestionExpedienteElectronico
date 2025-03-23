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
├── pages/
│   └── 1_📊_Hoja_de_Ruta.py
|   └── 2_🤖_Experto_en_Expediente_Electronico.py
|   └── 3_📊_Informe_Consolidado_SIUGJ.py
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
streamlit run 🏠_Inicio.py.py
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
├── 🏠_Inicio.py              # Aplicación web (Streamlit)
├── index_generator.py        # Lógica de generación del índice
├── file_utils.py             # Utilidades para manejo de archivos
├── metadata_extractor.py     # Extracción de metadatos
├── excel_handler.py          # Manejo de archivos Excel
│
├── assets/                   # Recursos estáticos
├── pages/                    # Páginas de la aplicación web
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

#### 3.2 🏠_Inicio.py (Aplicación Web)
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

### 3. Instalación (Versión de Escritorio Lite y AgilEx)

1. Descargue el ejecutable portable desde [enlace de descarga](https://gestionexpedienteelectronico.streamlit.app).
2. Ejecute el archivo descargado y siga las instrucciones en pantalla.
3. No se requiere instalación adicional.

### 4. Acceso (Versión Web de entrenamiento)

1. Abra su navegador web.
2. Visite la URL: [URL de la aplicación web](https://gestionexpedienteelectronico.streamlit.app).
3. No se requiere instalación ni registro.

### 5. Interfaz de Usuario

#### 5.1 Versión de Escritorio Lite

- **Ventana Principal**: Contiene todos los controles necesarios para la gestión de expedientes.
- **Botón "Seleccionar Carpeta"**: Permite elegir la carpeta que contiene los archivos del expediente.
- **Botón "Generar Índice"**: Inicia el proceso de creación del índice electrónico.
- **Opciones de Generación**: Permite elegir entre generar desde cero o usar una plantilla.
- **Barra de Progreso**: Muestra el avance del proceso de generación.
- **Área de Información**: Muestra mensajes y resultados del proceso.

#### 5.2 Versión AgilEx v1.4.4

### **Interfaz Principal Mejorada**

* **Panel de Control Modular**:
   - Nueva interfaz con tres modos de procesamiento integrados
   - Validaciones TRD en tiempo real
   - Sistema de ayuda contextual inteligente

* **Selector de Procesamiento Flexible**:
   - Procesamiento individual de subcarpetas
   - Gestión completa de expedientes
   - Manejo de series documentales
   - Soporte estructura 4-5 niveles
   - Validación jerárquica reforzada

### **Herramientas de Procesamiento Optimizadas**

* **Configuración Avanzada**:
  - Reglas TRD personalizables por nivel
  - Sistema preventivo de validaciones multinivel
  - Parámetros adaptables de migración
  - Sistema de logging mejorado
  - Patrones de diseño optimizados

### **Monitoreo y Control Inteligente**

* **Visualizador de Estructura Mejorado**:
  - Árbol jerárquico adaptativo
  - Validación instantánea por nivel
  - Sistema predictivo de errores
  - Vista previa de documentos integrada

* **Sistema de Progreso Avanzado**:
  - Monitoreo global del proceso
  - Seguimiento individual por elemento
  - Métricas detalladas de rendimiento
  - Indicadores de calidad en tiempo real

### **Gestión de Datos Avanzada**

* **Panel de Metadatos Renovado**:
  - Editor contextual inteligente
  - Validación TRD multinivel
  - Extracción automática optimizada
  - Control de calidad integrado

* **Generación de Informes Mejorada**:
  - Reportes personalizados por nivel
  - Estadísticas completas de proceso
  - Sistema de logs estructurado
  - Trazabilidad completa de operaciones

### **Exportación e Integración Ampliada**

* **Formatos Soportados Extendidos**:
  - XLSX con validaciones mejoradas
  - XLSM con macros optimizadas
  - PDF con metadata enriquecida
  - Compatibilidad retrospectiva

* **Conexión SGDEA Reforzada**:
  - Integración Alfresco optimizada
  - Sistema de migración inteligente
  - Validación multinivel de compatibilidad
  - Sincronización en tiempo real

#### 5.3 Versión Web de entrenamiento

- **Panel Principal**: Área central donde se cargan los archivos y se inicia el proceso.
- **Barra Lateral**: Contiene enlaces a recursos adicionales, marco normativo, hoja de ruta, y chat bot experto en expedientes electrónicos.
- **Área de Carga de Archivos**: Permite subir los documentos del expediente.
- **Botón "Generar Índice Electrónico"**: Inicia el proceso de creación del índice.

### 6. Uso Básico

#### 6.1 Generar un Índice Electrónico (Versión de Escritorio Lite)

1. Abra la aplicación.
2. Haga clic en "Seleccionar Carpeta" y elija la carpeta que contiene los archivos del expediente.
3. Seleccione la opción de generación (desde cero o usar plantilla).
4. Haga clic en "Generar Índice".
5. Espere a que el proceso termine. El índice se guardará en la misma carpeta del expediente.

#### 6.2 Generar un Índice Electrónico (Versión AgilEx v1.4.4)

La versión AgilEx 1.4.4 introduce un sistema de procesamiento flexible que permite manejar desde subcarpetas individuales hasta series documentales completas, incorporando validaciones avanzadas compatibles con el sistema migrador y la Tabla de Retención Documental (TRD).

**Proceso de generación por niveles:**

1. **Preparación inicial**
   - Inicie la aplicación AgilEx v1.4.4
   - Ejecute las verificaciones preliminares del sistema
   - Asegure que no hay archivos Excel abiertos
   - Identifique el nivel de procesamiento requerido (subcarpeta/expediente/serie)

2. **Selección del modo de procesamiento**
   - Elija entre las tres opciones disponibles:
     - Procesamiento de subcarpeta individual
     - Gestión de expediente completo
     - Manejo de serie documental
   - Configure el alcance del procesamiento según la opción seleccionada
   - Verifique la estructura de carpetas correspondiente al modo elegido

3. **Configuración avanzada**
   - Ajuste los parámetros según el nivel seleccionado:
     - Validaciones específicas por nivel (4-5 niveles)
     - Reglas TRD aplicables al contexto
     - Configuración de logging detallado
     - Gestión de metadatos contextual
     - Parámetros de validación estructural

4. **Ejecución del procesamiento**
   - Active el proceso mediante "Iniciar Procesamiento"
   - Supervise el avance en tiempo real:
     - Progreso general del proceso
     - Estado individual de elementos
     - Validaciones en curso
     - Mensajes del sistema

5. **Verificación multinivel**
   - Examine los resultados según el modo seleccionado:
     - Validación de índices generados
     - Confirmación de estructura jerárquica
     - Verificación de metadatos extraídos
     - Revisión de logs operativos
     - Control de calidad por nivel

6. **Exportación adaptativa**
   - Seleccione el formato más apropiado:
     - XLSX con validaciones mejoradas
     - XLSM con macros optimizadas
     - PDF con metadata enriquecida
   - Verifique la integridad de los archivos exportados

7. **Integración con sistemas externos** (opcional)
   - Configure la conexión con Alfresco
   - Valide los parámetros de migración
   - Ejecute la sincronización de datos
   - Verifique la integridad de la transferencia

**Consideraciones importantes:**
- Mantenga copias de seguridad de los documentos originales
- Monitoree el consumo de recursos del sistema
- Consulte los logs detallados ante cualquier anomalía
- Utilice el modo asíncrono para procesamiento de grandes volúmenes
- Verifique la compatibilidad de estructura según el nivel seleccionado
- Asegure la consistencia de metadatos en cada nivel de procesamiento

Esta nueva versión optimiza el flujo de trabajo mediante un enfoque modular y adaptativo, permitiendo un control más preciso y eficiente del proceso de gestión documental.

#### 6.3 Generar un Índice Electrónico (Versión Web de entrenamiento)

1. Acceda a la aplicación web.
2. Arrastre y suelte los archivos del expediente en el área de carga o use el botón para seleccionarlos.
3. Una vez cargados todos los archivos, haga clic en "Generar Índice Electrónico".
4. Espere a que el proceso termine. Se le proporcionará un enlace para descargar el índice generado.

### 7. Funciones Avanzadas

- **Uso de Plantillas**: Para usar una plantilla personalizada, seleccione la opción correspondiente antes de generar el índice (solo versión de escritorio).
- **Descarga de Recursos**: Utilice los enlaces en la barra lateral (versión web) o los botones correspondientes (versión de escritorio) para descargar la plantilla Excel y la guía de uso.

### 8. Solución de Problemas

- **El índice no se genera**: Asegúrese de que todos los archivos en la carpeta sean válidos y accesibles.
- **Errores en la carga de archivos (versión web de entrenamiento)**: Verifique que el tamaño total de los archivos no exceda el límite permitido.
- **La aplicación se cierra inesperadamente**: Asegúrese de tener la última versión instalada y que su sistema cumpla con los requisitos mínimos.

### 9. Mejores Prácticas

- Organice los archivos del expediente en una sola carpeta antes de generar el índice.
- Utilice nombres de archivo descriptivos y cortos.
- Actualice regularmente el índice si añade o modifica documentos en el expediente.

### 10. Soporte y Contacto

**Canales de ayuda:**
- [GitHub Issues](https://github.com/bladealex9848/GestionExpedienteElectronico/issues): Reportar bugs y sugerir mejoras
- [Soporte técnico Lite](mailto:aoviedof@cendoj.ramajudicial.gov.co): Alexander Oviedo Fadul
- [Soporte técnico AgilEx](mailto:darbelaeza@cendoj.ramajudicial.gov.co): Daniel Arbeláez Álvarez
- [Documentación](https://gestionexpedienteelectronico.streamlit.app/): Guías y tutoriales
- [Base de Conocimiento](https://gestionexpedienteelectronico.streamlit.app/): Soluciones comunes

**Desarrolladores:**
- Versión Lite: [Alexander Oviedo Fadul](https://github.com/bladealex9848)
- Versión AgilEx: [Daniel Arbeláez Álvarez](https://github.com/HammerDev99)

**Horarios de atención:**
- Soporte técnico: Lunes a viernes 8:00 AM - 5:00 PM (COT)
- GitHub Issues: Respuesta en 24-48 horas hábiles

**Prioridades de atención:**
1. Problemas críticos de producción
2. Errores que impiden operación
3. Mejoras y sugerencias
4. Consultas generales

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

### 2025-05-09: Optimización del procesamiento y mejora en la experiencia de usuario (v1.4.4)

La versión AgilEx 1.4.4 constituye una importante actualización que refina y potencia las funcionalidades introducidas en la versión anterior, con un enfoque especial en la experiencia de usuario y la eficiencia operativa. Esta actualización incorpora mejoras sustanciales basadas en la retroalimentación de usuarios y las especificaciones técnicas proporcionadas por la Unidad de Transformación Digital:

* **Interfaz de usuario rediseñada:** Implementación de una interfaz completamente renovada con funcionalidad mejorada para la gestión de carpetas, facilitando la interacción con el sistema y reduciendo la curva de aprendizaje para usuarios nuevos.

* **Sistema de comunicación optimizado:** Desarrollo de un nuevo sistema de mensajes más claros y precisos que guían al usuario a través de cada etapa del proceso, minimizando errores y mejorando la comprensión de las operaciones en curso.

* **Parámetros de indexación ajustados:** Refinamiento de los algoritmos de indexación siguiendo las especificaciones proporcionadas por la Unidad de Transformación Digital, resultando en índices más precisos y compatibles con los estándares actualizados.

* **Eliminación de limitaciones técnicas:** Resolución de restricciones que impedían el procesamiento correcto en versiones anteriores, especialmente en escenarios de alto volumen documental o estructuras complejas.

* **Mejora en la validación contextual:** Perfeccionamiento del sistema de validación multinivel que ahora proporciona retroalimentación más específica y soluciones proactivas ante posibles inconsistencias.

* **Rendimiento optimizado:** Implementación de mejoras en el uso de recursos del sistema, resultando en tiempos de procesamiento reducidos, especialmente notable en operaciones con grandes volúmenes de documentos.

* **Compatibilidad ampliada:** Actualización de los protocolos de integración con sistemas externos, incluyendo soporte mejorado para las últimas versiones de Alfresco y otros sistemas SGDEA.

* **Tutoriales actualizados:** Incorporación de nuevos materiales didácticos adaptados a la interfaz renovada, incluyendo videos paso a paso para cada modo de procesamiento.

* **Soporte para estructuras complejas:** Mejora en la capacidad del sistema para manejar estructuras de directorios anidadas, con soporte reforzado para casos de uso avanzados.

* **Sistema predictivo de errores:** Implementación de mecanismos que anticipan posibles problemas durante el procesamiento, ofreciendo soluciones preventivas.

La verificación de integridad del software puede realizarse utilizando el siguiente hash:
SHA256: `76d5fd5337e9894ac45a99afac55ef8310c87f4931434be3ce0d40b1f5ee1c1b`

Esta actualización mantiene el pleno cumplimiento con el Protocolo para la gestión de documentos electrónicos, digitalización y conformación del expediente electrónico (PCSJA20-11567 de 2020, Versión 2), a la vez que introduce mejoras significativas en la usabilidad y eficiencia del sistema, consolidando a AgilEx como la herramienta de referencia para la gestión de expedientes electrónicos en entornos judiciales.

### 2025-02-15: Actualización mayor con enfoque en procesamiento flexible y arquitectura modular (v1.4.3)

La nueva versión 1.4.3 representa una evolución significativa en la arquitectura del sistema, introduciendo un enfoque modular que permite un procesamiento más flexible y adaptable a diferentes necesidades. Las principales mejoras incluyen:

* **Sistema de procesamiento multinivel:** Implementación de tres modos distintos de procesamiento que permiten manejar desde subcarpetas individuales hasta series documentales completas, ofreciendo una flexibilidad sin precedentes en la gestión documental.
* **Refactorización de la interfaz de usuario:** Rediseño completo de la interfaz gráfica para incorporar el nuevo sistema de procesamiento flexible, manteniendo la intuitividad y facilidad de uso que caracterizan al software.
* **Arquitectura optimizada:** Implementación de patrones de diseño avanzados que mejoran la ortogonalidad del proyecto, resultando en un código más mantenible y eficiente.
* **Sistema de validación contextual:** Mejoras en el sistema de validación que ahora se adapta al nivel de procesamiento seleccionado, asegurando la integridad de los datos en cada contexto específico.
* **Gestión inteligente de recursos:** Optimización en el manejo de memoria y procesamiento, especialmente importante cuando se trabaja con grandes volúmenes de documentos.
* **Mejoras en la compatibilidad:** Refinamiento de la integración con sistemas externos y actualización de los protocolos de comunicación para asegurar una mejor interoperabilidad.
* **Documentación actualizada:** Renovación completa de la documentación técnica y guías de usuario para reflejar las nuevas funcionalidades y modos de operación.
* **Sistema de ayuda contextual:** Implementación de un sistema de ayuda que se adapta al modo de procesamiento seleccionado, ofreciendo asistencia relevante en cada contexto.
* **Actualización de validaciones TRD:** Mejoras en la implementación de las reglas de la Tabla de Retención Documental, con soporte para validaciones específicas por nivel.
* **Recursos actualizados:** Incorporación de nuevos videos tutoriales y guías específicas para cada modo de procesamiento.
La verificación de integridad del software puede realizarse utilizando el siguiente hash:
SHA256: 022afb2b53968567f36579296043094e31fef5af635f0d5817a653fd3c214ac8

Esta actualización mantiene el cumplimiento con el Protocolo para la gestión de documentos electrónicos, digitalización y conformación del expediente electrónico (PCSJA20-11567 de 2020, Versión 2), mientras introduce mejoras significativas en la flexibilidad y eficiencia del sistema.


### 2024-12-31: Actualización con mejoras de usabilidad y gestión de índices (v1.4.2)

*   **Gestión segura de índices existentes:** Implementación de medidas para proteger y preservar índices generados previamente.
*   **Interfaz más intuitiva:** Renovación de la interfaz gráfica con un diseño más amigable y un menú de ayuda integrado para facilitar la navegación.
*   **Mejor manejo de errores y validaciones:** Refinamiento del sistema de detección y manejo de errores, con validaciones más robustas.
*   **Optimización en el procesamiento de carpetas:** Mejoras en el algoritmo para un procesamiento más eficiente de las carpetas de expedientes.
*   **Sistema de mensajes mejorado para el usuario:** Implementación de un sistema de notificaciones y mensajes más claro y comprensible.
*   **Nueva Vista Previa:** Se ha añadido la función de vista previa.
*   **Actualización de la Guía Rápida de Uso:** Se ha actualizado la guía para incluir las últimas mejoras y características, como la preparación, estructura válida de carpetas y requisitos básicos, como el radicado de 23 dígitos, nombres de archivos ordenados y datos SGDE exactos.
*   **Características Principales Reafirmadas:** Se mantienen las características principales, como la compatibilidad con el sistema migrador de expedientes, soporte para estructuras de 4 y 5 niveles, validación automática de estructuras y gestión documental estandarizada (TRD).
*   **Actualización de la Nota de Verificación:** Se ha actualizado el SHA256 para reflejar la nueva versión del software.
*   **Recursos Actualizados:** Se ha añadido un enlace a un nuevo Video Tutorial v1.4.2.
*   **Conformidad con el Protocolo:** Se reafirma que el software cumple con el Protocolo para la gestión de documentos electrónicos, digitalización y conformación del expediente electrónico (PCSJA20-11567 de 2020, Versión 2).
*   SHA256: 6d54ccabc0048fefe40648bdadb5b26a215d031448eb2f67235b1189beb70521

### 2024-11-15: Actualización mayor con mejoras en validación y compatibilidad (v1.4.1)

* Implementación de validaciones compatibles con el sistema migrador de expedientes electrónicos
* Integración de la Tabla de Retención Documental (TRD) para gestión documental estandarizada
* Soporte para estructuras de directorios de 4 y 5 niveles con validación jerárquica
* Mejora en sistema de logging para trazabilidad completa de operaciones
* Implementación de manejo asíncrono de operaciones de E/S
* Nuevas validaciones preventivas en estructura de expedientes
* Optimización del rendimiento en procesamiento masivo
* Refactorización de la interfaz para mejor experiencia de usuario
* Compatibilidad ampliada con SGDEA y preparación para Alfresco
* Actualización de documentación técnica y guías de usuario
* Corrección de errores en manejo de metadatos y conteo de páginas
* SHA256: fb172a837bd7f91f3e1d6528cddebee164f9d89fd8807a83c8560521852a5b4e

### 2024-10-16: Mejora en la experiencia de usuario y expansión de funcionalidades (v.1.3.5)

* Implementación de una nueva pestaña "Visión General" en la página principal, proporcionando una introducción completa al sistema y sus características.
* Reorganización de la estructura de pestañas para incluir "Visión General", "Versiones de Escritorio", "Versión Web" e "Instrucciones de Uso".
* Actualización de las descripciones y características de las versiones Lite, Ultimate y Web para una mejor comprensión por parte del usuario.
* Integración de video tutoriales embebidos para las versiones Lite y Ultimate, mejorando la accesibilidad a la información de uso.
* Adición de enlaces de respaldo para ver los videos tutoriales en alta calidad.
* Mejora en la presentación de recursos adicionales y marco normativo en la barra lateral.
* Inclusión de una sección que destaca los beneficios clave del sistema en la página de visión general.
* Integración de información sobre funcionalidades adicionales como Hoja de Ruta, Experto en Expediente Electrónico e Informe Consolidado SIUGJ.
* Optimización del código para mejorar el rendimiento y la eficiencia de la aplicación web.
* Actualización de la documentación, incluyendo instrucciones de uso específicas para cada versión del sistema.
* Implementación de URLs personalizadas para facilitar el acceso a los recursos y videos tutoriales.
* Preparación para una mejor integración con sistemas existentes como SIUGJ, Justicia XXICS y Tyba.
* Actualización del README y documentación técnica para reflejar los nuevos cambios y características.

### 2024-10-09: Actualización de funcionalidades de renombrado y generación de índice (v.1.3.4)
* Mejora en la función de renombrado de archivos para manejar casos especiales de numeración preexistente.
* Actualización del algoritmo para eliminar cualquier secuencia de números al inicio de los nombres de archivos.
* Refinamiento del proceso de ordenamiento cronológico en la función de renombrado.
* Ajuste en la generación del índice para reflejar correctamente los nuevos nombres de archivos sin numeración inicial.
* Optimización del manejo de archivos de índice (IndiceElectronico) con extensiones .xlsx y .xlsm.
* Corrección de la lógica para evitar la duplicación de números en nombres de archivos ya numerados.
* Mejora en la consistencia entre el sistema de archivos y el índice generado en la plantilla de Excel.
* Actualización de la documentación para reflejar los nuevos cambios en el proceso de renombrado y generación de índice.

### 2024-10-08: Actualización mayor y revisión externa (v.1.3.3)

- Implementación de una nueva pestaña "Visión General" en la página principal, proporcionando una introducción completa al sistema y sus características.
- Reorganización de la estructura de pestañas para incluir "Visión General", "Versiones de Escritorio", "Versión Web" e "Instrucciones de Uso".
- Actualización de las descripciones y características de las versiones Lite, Ultimate y Web.
- Mejora en la presentación de recursos adicionales y marco normativo.
- Adición de una sección que destaca los beneficios clave del sistema.
- Integración de información sobre funcionalidades adicionales como Hoja de Ruta, Experto en Expediente Electrónico e Informe Consolidado SIUGJ.
- Actualización de la interfaz de usuario para mejorar la navegación y experiencia del usuario.
- Revisión y actualización de la documentación, incluyendo instrucciones de uso específicas para cada versión.
- Optimización del código para mejorar el rendimiento y la eficiencia.
- Preparación para una mejor integración con sistemas existentes como SIUGJ, Justicia XXICS y Tyba.

### 2024-08-18: Actualización mayor y revisión externa (v.1.3.2)

#### Documentación
- Actualización del ABC "Protocolo para la Gestión de Documentos Electrónicos en la Rama Judicial" a la versión 1.2.0.
- Revisión y actualización de la guía de usuario con mejoras en claridad y consistencia.
- Modificación de la recomendación sobre el prefijo numérico en la nomenclatura de archivos, permitiendo mayor flexibilidad.
- Inclusión de referencias a documentación adicional sobre el proceso de transformación digital de la Rama Judicial:
  * Plan de Digitalización de Expedientes 2020-2022
  * CIRCULAR PCSJC20-32
  * Plan Estratégico de Transformación Digital
  * Programa de Expediente Electrónico
  * Sistema Integrado Único de Gestión Judicial - Core
  * Proyectos de Transición
- Actualización de las referencias bibliográficas al formato APA séptima edición.
- Mejora en la estructura del documento con la adición de saltos de página para mejor legibilidad.

#### Software
- Corrección de errores en la generación del índice en formato Excel.
- Resolución del problema de ventanas sin mensajes durante la ejecución del programa.
- Implementación de mejoras en el manejo de archivos y la generación del índice electrónico, contribuidas por [HammerDev99](https://github.com/HammerDev99):
  * Optimización del algoritmo de renombrado de archivos.
  * Función más robusta para la extracción de metadatos de diferentes tipos de archivos.
  * Mejora en la lógica de generación del índice electrónico.
- Inicio del proceso para resolver el problema de seguridad que marca el ejecutable como sospechoso.

#### Nuevas Características
- Mantenimiento de las nuevas páginas implementadas en la versión anterior:
  * Hoja de Ruta (1_📊_Hoja_de_Ruta.py): Visualización interactiva del progreso del proyecto.
  * Experto en Expediente Electrónico (2_🤖_Experto_en_Expediente_Electronico.py): Chatbot especializado en gestión documental judicial.

#### Revisión Externa
- Revisión completa realizada por Daniel Arbeláez Álvarez, Técnico CSP de Bello, Antioquia.
- Incorporación de sugerencias y correcciones basadas en la revisión externa.

#### Próximos Pasos
- Continuar la optimización del software basándose en el feedback recibido.
- Implementar soluciones para los problemas de seguridad identificados.
- Actualizar la documentación para reflejar las últimas normativas y planes de transformación digital de la Rama Judicial.

### 2024-08-15: Actuaización menor y corrección de errores (v.1.3.1)
- Corrección de errores menores en la interfaz de usuario y el proceso de generación de índices.
- Supreción de las carpetas marco_normativo y temp_expediente en la versión web y escritorio para optimizar el espacio de almacenamiento y carga de archivos.
- Mejoras en la gestión de errores y mensajes de usuario para una experiencia más fluida y menos propensa a errores.
- En la versión de escritorio se elimino el guardar el índice electrónico (xlsx) en la carpeta del expediente y se dejo solamente el guardado del índice electrónico (xlsm) en la carpeta del expediente para optimizar el espacio de almacenamiento y carga de archivos.

### 2024-08-10: Actualización mayor y mejoras en la versión web (v.1.3.0)
- Rediseño completo de la interfaz web, con un panel lateral mejorado.
- Implementación de descarga de recursos adicionales y marco normativo desde el panel lateral.
- Adición de badges de GitHub y contador de visitantes en la página principal.
- Mejora en la configuración de Streamlit para una mejor experiencia de usuario.
- Optimización del manejo de archivos temporales para mejorar la seguridad y el rendimiento.
- Implementación de manejo de errores robusto, especialmente para la carga de imágenes y recursos.
- Preparación del proyecto para generación de ejecutable para Windows.
- Actualización de la documentación y guías de usuario.

### 2024-08-10: Actualización de la versión web (v.1.2.0)
- Rediseño de la interfaz web, moviendo recursos adicionales y créditos al panel lateral.
- Simplificación del proceso de generación de índices, eliminando la opción de usar plantilla.
- Implementación de manejo de archivos temporales para mejorar la seguridad y el rendimiento en entornos multi-usuario.
- Adición de funcionalidad para comprimir y descargar el expediente completo con el índice generado.
- Mejora en la gestión de recursos del servidor al procesar múltiples solicitudes simultáneas.

### 2024-08-09: Actualización y correcciones (v.1.1.1)
- Mejora en el manejo de la plantilla Excel con macros (.xlsm).
- Corrección del problema de generación de archivos .xlsx adicionales.
- Optimización del proceso de renombrado de archivos para respetar la numeración existente.
- Ajuste en la lógica de generación del índice para excluir correctamente archivos no deseados.
- Mejora en la compatibilidad con diferentes sistemas operativos.
- Actualización de la documentación y guías de usuario.

### 2024-08-09: Actualización mayor (v.1.1.0)
- Implementación de la versión de escritorio utilizando PyQt5.
- Adición de la funcionalidad para generar índices tanto desde cero como utilizando una plantilla.
- Mejora en la extracción de metadatos para soportar múltiples tipos de archivos.
- Implementación de un manejador de Excel para crear y modificar archivos de índice.
- Actualización de la estructura del proyecto para soportar tanto la versión web como la de escritorio.
- Adición de pruebas unitarias para las nuevas funcionalidades.
- Actualización de la documentación para reflejar los nuevos cambios y características.

### 2024-08-08: Primera versión (v.1.0.0)
- Lanzamiento inicial del Sistema de Gestión de Expedientes Electrónicos Judiciales.
- Implementación de la versión web utilizando Streamlit.

## Créditos

Este proyecto es una evolución del trabajo inicial realizado por [HammerDev99 Daniel](https://github.com/HammerDev99/GestionExpedienteElectronico_Version1), a quien se le reconoce y agradece por sentar las bases de esta herramienta.

Desarrollado y mantenido por Alexander Oviedo Fadul, Profesional Universitario Grado 11 en el Consejo Seccional de la Judicatura de Sucre.

[GitHub](https://github.com/bladealex9848) | [Website](https://alexanderoviedofadul.dev/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/)

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [MIT License](https://opensource.org/licenses/MIT) para más detalles.