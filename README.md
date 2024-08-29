# Procesamiento de Documentos Legales - Sistema de Extracción de Información

Este proyecto está diseñado para procesar subdirectorios de documentos legales, combinando archivos TXT y utilizando la API de OpenAI para extraer información específica en un formato JSON.

## Requisitos

- Python 3.7+
- Paquetes necesarios:
  - `requests`
  - `re`
  - `os`
  - `json`
  - `datetime`

## Instalación

1. Clona este repositorio en tu máquina local.
2. Asegúrate de tener Python 3.7 o superior instalado.
3. Instala las dependencias necesarias:

    ```bash
    pip install -r requirements.txt
    ```

4. Configura tu clave API de OpenAI en el script `gpt_process.py`:

    ```python
    api_key = "tu_clave_api_aqui"
    ```

5. Ejecuta el script principal:

    ```bash
    python gpt_process.py
    ```

## Uso

El script está diseñado para procesar un subdirectorio de documentos legales que sigue el formato `Documentos Solicitud {número} - {año}`. Extrae el número y año del nombre del subdirectorio, combina los archivos TXT, y utiliza la API de OpenAI para generar un archivo JSON con la información relevante.

## Estructura del Proyecto

- `gpt_process.py`: Script principal para procesar los documentos.
- `requirements.txt`: Archivo con las dependencias del proyecto.

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.
