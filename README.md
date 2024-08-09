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
- Generación de índices en formatos Excel y PDF.
- Interfaz de usuario intuitiva basada en Streamlit.
- Cumplimiento con los estándares judiciales colombianos.

## Estructura del Proyecto

```
sistema_gestion_expedientes/
│
├── app/
│   ├── main.py
│   ├── expediente_processor.py
│   ├── file_utils.py
│   ├── metadata_extractor.py
│   ├── index_generator.py
│   └── gui.py
│
├── tests/
│   └── test_expediente_processor.py
│
├── assets/
│   └── 000IndiceElectronicoC0.xlsm
│
├── requirements.txt
└── README.md
```

### Descripción de los archivos:

- `main.py`: Punto de entrada principal de la aplicación.
- `expediente_processor.py`: Contiene la lógica principal para procesar expedientes.
- `file_utils.py`: Utilidades para el manejo de archivos y carpetas.
- `metadata_extractor.py`: Funciones para extraer metadatos de diferentes tipos de archivos.
- `index_generator.py`: Genera los índices en formatos Excel y PDF.
- `gui.py`: Implementa la interfaz gráfica de usuario con Streamlit.
- `test_expediente_processor.py`: Pruebas unitarias para el procesador de expedientes.
- `000IndiceElectronicoC0.xlsm`: Plantilla Excel para el índice electrónico.

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/bladealex9848/GestionExpedienteElectronico.git
   ```

2. Navegar al directorio del proyecto:
   ```
   cd GestionExpedienteElectronico
   ```

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
   pip install -r requirements.txt
   ```

## Uso

Para ejecutar la aplicación:

```
streamlit run app/main.py
```

Siga las instrucciones en la interfaz de usuario para cargar y procesar los expedientes.

## Manual Técnico

### Flujo de Trabajo del Sistema

1. **Carga de Archivos**: 
   - Los archivos del expediente se cargan desde una carpeta especificada.
   - `file_utils.py` maneja la lectura y renombrado de archivos.

2. **Extracción de Metadatos**: 
   - `metadata_extractor.py` extrae información relevante de cada archivo.
   - Se manejan diferentes tipos de archivos (PDF, Word, Excel, imágenes).

3. **Procesamiento del Expediente**: 
   - `expediente_processor.py` coordina el proceso general.
   - Organiza los metadatos y prepara la información para el índice.

4. **Generación del Índice**: 
   - `index_generator.py` crea los índices en Excel y PDF.
   - Utiliza plantillas predefinidas para mantener la consistencia.

5. **Interfaz de Usuario**: 
   - `gui.py` implementa la interfaz con Streamlit.
   - Maneja la interacción del usuario y la presentación de resultados.

### Componentes Clave

- **ExpedienteProcessor**: Clase principal que orquesta el procesamiento.
- **Extractores de Metadatos**: Funciones especializadas para cada tipo de archivo.
- **Generadores de Índice**: Módulos para crear documentos Excel y PDF.
- **Utilidades de Archivo**: Funciones para manejar operaciones de sistema de archivos.

### Pruebas

Las pruebas unitarias en `test_expediente_processor.py` cubren:
- Renombrado de archivos
- Extracción de metadatos
- Generación de DataFrames
- Validación de metadatos del expediente

## Manual de Usuario

1. **Inicio de la Aplicación**:
   - Ejecute la aplicación como se indica en la sección de Uso.
   - Se abrirá una interfaz web en su navegador predeterminado.

2. **Selección de Carpeta**:
   - Use el campo de entrada para especificar la ruta de la carpeta del expediente.

3. **Ingreso de Metadatos**:
   - Complete los campos requeridos con la información del expediente.

4. **Procesamiento**:
   - Haga clic en "Generar Índice Electrónico" para iniciar el proceso.

5. **Descarga de Resultados**:
   - Una vez completado, use los botones para descargar los índices en Excel y PDF.

6. **Revisión**:
   - Verifique los archivos generados para asegurar la exactitud de la información.

## Contribución

Las contribuciones son bienvenidas. Por favor, siga estos pasos:

1. Haga fork del repositorio.
2. Cree una nueva rama (`git checkout -b feature/AmazingFeature`).
3. Haga commit de sus cambios (`git commit -m 'Add some AmazingFeature'`).
4. Haga Push a la rama (`git push origin feature/AmazingFeature`).
5. Abra un Pull Request.

## Registro de Cambios

- 2024-08-08: Primera versión. (v.1.0.0)

## Créditos

Este proyecto es una evolución del trabajo inicial realizado por [HammerDev99 Daniel](https://github.com/HammerDev99/GestionExpedienteElectronico_Version1), a quien se le reconoce y agradece por sentar las bases de esta herramienta.

Desarrollado y mantenido por Alexander Oviedo Fadul, Profesional Universitario Grado 11 en el Consejo Seccional de la Judicatura de Sucre.

[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!)

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [MIT License](https://opensource.org/licenses/MIT) para más detalles.