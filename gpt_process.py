import os
import re
import requests
import json
from datetime import datetime

# Configuración
api_key = ""
url_api = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def log_message(message):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def limpiar_texto(texto):
    texto_limpio = re.sub(r'[^\x00-\x7F]+', ' ', texto)
    texto_limpio = re.sub(r'[^a-zA-Z0-9\s,.-]', ' ', texto_limpio)
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
    return texto_limpio

def procesar_subdirectorio(ruta_subdirectorio):
    log_message(f"Procesando subdirectorio: {ruta_subdirectorio}")
    numero, año = extraer_numero_y_ano(ruta_subdirectorio)
    
    if not numero or not año:
        log_message("No se pudo extraer el número o el año. Saltando.")
        return
    
    try:
        numero = int(numero)
        año = int(año)
    except ValueError:
        log_message("El número o el año no son válidos. Saltando.")
        return

    archivo_json = os.path.join(ruta_subdirectorio, f"resultado_{numero}_{año}.json")
    
    # Si el archivo JSON ya existe, se salta el subdirectorio
    if os.path.exists(archivo_json):
        log_message(f"El archivo {archivo_json} ya existe. Saltando.")
        return

    texto_combinado = combinar_archivos_txt(ruta_subdirectorio)
    resultado_json = procesar_con_api(texto_combinado)

    # Extraer y guardar solo el contenido relevante
    if resultado_json and "choices" in resultado_json and len(resultado_json["choices"]) > 0:
        content = resultado_json["choices"][0]["message"]["content"]
        # Quitar posibles delimitadores de código
        content = content.strip().strip('```json').strip('```')
        
        # Intentar corregir el JSON
        content = corregir_json(content)
        
        try:
            json_content = json.loads(content)
            with open(archivo_json, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, ensure_ascii=False, indent=2)
            log_message(f"Guardado resultado en {archivo_json}")
        except json.JSONDecodeError:
            log_message(f"Error al decodificar el JSON en el contenido:\n{content}")
    else:
        log_message(f"Error al procesar con la API para {ruta_subdirectorio}")

# Extrae el número y el año del nombre del subdirectorio
def extraer_numero_y_ano(ruta_subdirectorio):
    nombre_carpeta = os.path.basename(ruta_subdirectorio)
    log_message(f"Extrayendo número y año de: {nombre_carpeta}")
    match = re.search(r'Documentos Solicitud (\d+) - (\d+)', nombre_carpeta)
    if match:
        numero = match.group(1)
        año = match.group(2)
        log_message(f"Encontrado número: {numero}, año: {año}")
        return numero, año
    else:
        log_message("No se encontró un match para número y año.")
        return None, None

# Combina todos los archivos TXT en uno solo
def combinar_archivos_txt(directorio):
    texto_combinado = ""
    log_message(f"Combinando archivos en: {directorio}")
    for root, _, files in os.walk(directorio):
        for file in files:
            if file.endswith(".txt") and not ("OTROS" in file or "SOL" in file):
                log_message(f"Leyendo archivo: {file}")
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    texto_combinado += f.read() + " "
    return limpiar_texto(texto_combinado)

# Envía el texto a la API de OpenAI y obtiene el JSON
def procesar_con_api(texto):
    log_message(f"Procesando texto con la API. Longitud del texto: {len(texto)} caracteres.")
    
    prompt = f"""
            Este es un nuevo texto que debe ser procesado de manera independiente a cualquier texto anterior:

            "{texto}"

            Extrae y organiza la siguiente información en un formato JSON. No uses información de ningún texto anterior y no mezcles datos entre diferentes textos. Si no encuentras algún dato específico, omítelo completamente en el resultado JSON (excepto para los campos indicados más abajo que pueden devolver un valor vacío).

            1. **Información del derecho de agua:** (informacion_derecho_agua)
            - naturaleza_agua: Selecciona entre ['--','SUPERFICIAL', 'SUBTERRANEA', 'S. Y DETENIDA', 'SUP. Y CORRIENTE', 'SUP. CORRIENTES/DETENIDAS'].
            - tipo_derecho: Selecciona entre ['--','CONSUNTIVO', 'NO CONSUNTIVO'].
            - nombre_comunidad: Texto simple.
            - proyecto_parcelacion: Texto simple.
            - sitio: Texto simple. Por lo general, suelen ser numeros o numeros y letras Ej: A1, B2, 22, nunca incluir la comuna.
            - parcela: Texto simple.
            - ejercicio_derecho: Selecciona entre ['--','PERMANENTE Y CONTINUO', 'EVENTUAL Y CONTINUO', 'PERM. Y CONT. Y PROVICIONALES', 'SIN EJERCICIO', 'PERM. Y DISC. Y PROVICIONALES', 'PERM Y ALTER. Y PROVICIONALES', 'EVENTUAL Y DISCONTINUO', 'EVENTUAL Y ALTERNADO', 'PERMANENTE Y DISCONTINUO', 'PERMANENTE Y ALTERNADO'].
            - metodo_extraccion: Selecciona entre ['--','MECANICA', 'GRAVITACIONAL', 'MECANICA Y/O GRAVITACIONAL'].
            - cantidad: Texto simple (solo números. Ejemplo: 84). Puede devolver vacío si no se encuentra explícitamente.
            - unidad: Selecciona entre ['--','LT/S', 'M3/S', 'MM3/AÑO', 'M3/AÑO', 'LT/MIN', 'M3/H', 'LT/H', 'M3/MES', 'ACCIONES', 'M3/DIA', 'M3/MIN', 'LT/DIA', 'REGADORES', 'CUADRAS', 'TEJAS', 'HORAS TURNO', '%', 'PARTES', 'LT/MES', 'MMM3/MES', 'M3/HA/MES', 'ETC']. Puede devolver '--' si no se encuentra explícitamente.
            - utm_norte: Texto simple (solo números, formato coordenadas. Ejemplo: 6.017.265). Puede devolver vacío si no se encuentra explícitamente.
            - utm_este: Texto simple (solo números, formato coordenadas. Ejemplo: 321.575). Puede devolver vacío si no se encuentra explícitamente.
            - unidad_utm: Selecciona entre ['--','KM', 'MTS']. Puede devolver '--' si no se encuentra explícitamente.
            - huso: Selecciona entre ['--','18', '19']. Puede devolver '--' si no se encuentra explícitamente.
            - datum: Selecciona entre ['--','56', '69', '84']. Puede devolver '--' si no se encuentra explícitamente.
            - pto_conocidos_captacion: Texto libre, posiblemente multilineal.

            2. **Información del inscriptor del derecho:** (informacion_inscriptor_derecho)
            - Puede haber uno o múltiples inscriptores. Ordenar desde quien tiene el derecho actualmente sin incluir los del pasado.
            - Para cada inscriptor:
                - `rut`: Número de RUT del inscriptor (sin DV. Ejemplo: 11123123). solo numeros, sin Digito verificador.
                - `nac`: Nacionalidad del inscriptor.
                - `tipo`: Tipo de persona (natural o jurídica).
                - `genero`: Género del inscriptor (masculino o femenino) si es persona natural. jurídica devolver '--'
                - `nombre`: 
                    - Si es persona natural, extrae solo el primer nombre y el segundo nombre (si tiene).
                    - Si es persona jurídica, utiliza el nombre completo tal como está.
                - `paterno`: Apellido paterno si es persona natural.
                - `materno`: Apellido materno si es persona natural.

            3. **Información de las inscripciones:** (informacion_inscripciones)
            - Puede haber una o múltiples inscripciones. Ordenar del más nuevo al más antiguo.
            - Para cada inscripción:
                - `f_inscripcion`: Fecha de la inscripción en formato día/mes/año. Nota: La fecha de inscripción debe ser extraída del texto que menciona explícitamente el lugar y la fecha, por ejemplo, "Ovalle, 1 de Diciembre del 2009 Drs". La fecha extraída debe convertirse al formato numérico correspondiente (ej.: "1 de Diciembre del 2009" se convierte en "01/12/2009") y debe coincidir con el año mencionado en el texto. Omitir cualquier fecha que aparezca después de la palabra "CERTIFICO:", ya que estas no corresponden a la fecha de inscripción.
                - `comuna`: Comuna donde se realizó la inscripción.
                - `cbr`: Nombre del Conservador de Bienes Raíces (CBR), omitiendo la frase "Conservador de Bienes Raíces de".
                - `foja`: Número de la foja donde está registrada la inscripción (solo números, ej.: 403).
                - `numero`: Número de la inscripción (solo números, ej.: 501).
                - `anio`: Año de la inscripción, que debe coincidir con el año especificado en la documentación proporcionada. Ejemplo: Si en el documento se menciona que la inscripción es del año 2009, el campo anio debe reflejar "2009" y no otro año.
                - `vta`: Indica si se menciona la "vuelta" o "VTA". Si está presente, marcar como `true`, en caso contrario, `false`.

            Entrega los resultados en formato JSON. Si no se encuentra alguno de los datos solicitados en el texto, simplemente no lo incluyas en el resultado. En los casos donde se permite devolver un valor vacío, hazlo sin inventar datos.

        Ejemplo de JSON esperado: 
        {{
            "informacion_derecho_agua": {{
                "naturaleza_agua": "SUPERFICIAL",
                "tipo_derecho": "CONSUNTIVO",
                "nombre_comunidad": "FJS",
                "proyecto_parcelacion": "AGUAS",
                "sitio": "Mulchen",
                "parcela": "84",
                "ejercicio_derecho": "PERMANENTE Y CONTINUO",
                "metodo_extraccion": "MECANICA",
                "cantidad": "84",
                "unidad": "M3/AÑO",
                "utm_norte": "6.017.265",
                "utm_este": "321.575",
                "unidad_utm": "MTS",
                "huso": "19",
                "datum": "84",
                "pto_conocidos_captacion": "Mulchen, 04 de Diciembre de 2023"
            }},
            "informacion_inscriptor_derecho": [
                {{
                "rut": "5925399-9",
                "nac": "Chilena",
                "tipo": "natural",
                "genero": "masculino",
                "nombre": "Pedro Francisco",
                "paterno": "Fuentes",
                "materno": "López"
                }}
            ],
            "informacion_inscripciones": [
                {{
                "f_inscripcion": "dd/mm/yyyy",
                "comuna": "Mulchen",
                "cbr": "Mulchen",
                "foja": "84",
                "numero": "103",
                "anio": "2023",
                "vta": true
                }}
            ]
        }}
    """


    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 3000,
        "temperature": 0.5
    }

    response = requests.post(url_api, headers=headers, json=payload)
    if response.status_code == 200:
        log_message("Procesamiento exitoso con la API.")
        return response.json()
    else:
        log_message(f"Error en la API: {response.status_code}, {response.text}")
        return None

# Función para intentar corregir el JSON
def corregir_json(content):
    content = re.sub(r',\s*}', '}', content) 
    content = re.sub(r',\s*\]', ']', content)

    content = re.sub(r'"\s+"', '"', content)
    content = re.sub(r'":\s*"([\w\s]+)"', r'": "\1"', content)

    return content


if __name__ == "__main__":
    directorio = "PRUEBA2\Documentos Solicitud 045 - 045"
    procesar_subdirectorio(directorio)