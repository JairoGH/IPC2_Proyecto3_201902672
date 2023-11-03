from flask import Flask, request, jsonify
from xml.etree import ElementTree as ET
import re
import os
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

xml_file = 'bd.xml'
xml_config = 'config.xml'
mensajes_procesados = set()

dates = []
msg = []

#Se da un mensaje de inicio.
@app.route('/')
def index():
    return "PROYECTO 3 IPC2",200

@app.route('/grabarMensajes', methods=['POST'])
def grabar_msg():
    # Se obtiene el XML del request
    xml_data = request.data
    root = ET.fromstring(xml_data)

    # Se carga XML existente si existe, o se crea uno nuevo
    if os.path.exists(xml_file):
        tree = ET.parse(xml_file)
        elementos = tree.getroot()
    else:
        elementos = ET.Element('MENSAJES')

    #Se inicializa un conjunto para realizar un seguimiento de los textos de los mensajes existentes
    textos_existentes = set(elemento.find('TEXTO').text for elemento in elementos.findall('MENSAJE'))

    #Se inicializa los contadores para usuarios y hashtags
    usuario_count = 0
    hashtag_count = 0
    fechas = []

    #Defino los patrones para encontrar usuarios, hashtags y fechas (DD/MM/YYYY)
    usuario_pattern = r'@[\w_]+'
    hashtag_pattern = r'#[\w]+#'
    fecha_pattern = r'\d{2}/\d{2}/\d{4}'

    # Para llevar un registro de los mensajes grabados
    mensajes_grabados = 0  
    # Para llevar un registro de los mensajes duplicados
    mensajes_duplicados = 0  

    # Recorremos el archivo XML
    for mensaje in root.findall('MENSAJE'):
        cont_msg = mensaje.find('TEXTO').text

        # Verificar si el mensaje ya existe en el archivo
        if cont_msg in textos_existentes:
            mensajes_duplicados += 1  
            continue

        #Obtiene el nodo de fecha
        fecha_node = mensaje.find('FECHA')  

        if fecha_node is not None:
            fecha_text = fecha_node.text
            fecha_match = re.search(fecha_pattern, fecha_text)

            if fecha_match:
                fecha = fecha_match.group()
                fechas.append(fecha)

                # Actualizar el texto de la fecha al formato DD/MM/YYYY
                fecha_node.text = fecha  

        # Crear la estructura del mensaje en el XML
        elemento = ET.SubElement(elementos, 'MENSAJE')
        ET.SubElement(elemento, "FECHA").text = fecha_text
        ET.SubElement(elemento, "TEXTO").text = cont_msg

        # Agregar las fechas, usuarios y hashtags al mensaje
        for usuario in re.findall(usuario_pattern, cont_msg):
            ET.SubElement(elemento, "USUARIO_EN_MENSAJE").text = usuario
            
            #Actualizar el contador de usuarios
            usuario_count += 1  

        for hashtag in re.findall(hashtag_pattern, cont_msg):
            ET.SubElement(elemento, "HASHTAG_EN_MENSAJE").text = hashtag
            
            #Actualizar el contador de hashtags
            hashtag_count += 1  

        #Agregar el texto del nuevo mensaje al conjunto
        textos_existentes.add(cont_msg)  

        #Incrementar el contador de mensajes grabados
        mensajes_grabados += 1  

    #Guardar el archivo XML
    tree = ET.ElementTree(elementos)
    tree.write(xml_file)

    #Crear la estructura XML de respuesta
    respuesta_xml = ET.Element('MENSAJES_RECIBIDOS')
    tiempo = ET.SubElement(respuesta_xml, 'TIEMPO')

    #Comprobar si se encontraron fechas y agregarlas a la respuesta
    if fechas:
        ET.SubElement(tiempo, 'FECHAS').text = ', '.join(fechas)
    else:
        ET.SubElement(tiempo, 'FECHAS').text = "No se encontraron fechas"

    ET.SubElement(tiempo, 'MSJ_RECIBIDOS').text = str(mensajes_grabados)  # Usar el contador de mensajes grabados
    ET.SubElement(tiempo, 'USR_MENCIONADOS').text = str(usuario_count)
    ET.SubElement(tiempo, 'HASH_INCLUIDOS').text = str(hashtag_count)

    #Agregar un mensaje que indique los mensajes duplicados, si los hay
    if mensajes_duplicados > 0:
        ET.SubElement(tiempo, 'MENSAJES_DUPLICADOS').text = f"{mensajes_duplicados} mensajes ya están registrados."

    #Mostrar la estructura XML de respuesta a una cadena y retornarla
    respuesta_str = ET.tostring(respuesta_xml, encoding='unicode')
    return respuesta_str, 200, {'Content-Type': 'application/xml'}
    


#Metodo POST para grabar la configuracion!
@app.route('/grabarConfiguracion', methods=['POST']) 
def grabar_config():
    # Obtener el XML de la solicitud
    xml_data_config = request.data
    root = ET.fromstring(xml_data_config)

    #Cargar el XML existente si existe
    if os.path.exists(xml_config):
        tree = ET.parse(xml_config)
        elementos = tree.getroot()
    else:
        elementos = ET.Element('diccionario')

    # Encontrar o crear elementos para sentimientos positivos y negativos
    sentimientos_positivos = elementos.find('sentimientos_positivos')
    sentimientos_negativos = elementos.find('sentimientos_negativos')

    if sentimientos_positivos is None:
        sentimientos_positivos = ET.SubElement(elementos, 'sentimientos_positivos')

    if sentimientos_negativos is None:
        sentimientos_negativos = ET.SubElement(elementos, 'sentimientos_negativos')

    #Lista para almacenar sentimientos duplicados
    sentimientos_duplicados_positivos = []
    sentimientos_duplicados_negativos = []

    #Procesar sentimientos positivos
    for config in root.find('sentimientos_positivos'):
        palabra_pos = config.text.strip()  # Eliminar espacios en blanco alrededor de la palabra
        if palabra_pos not in [palabra.text.strip() for palabra in sentimientos_positivos.findall('palabra')]:
            ET.SubElement(sentimientos_positivos, "palabra").text = palabra_pos
        else:
            sentimientos_duplicados_positivos.append(palabra_pos)
    
    #Procesar sentimientos negativos
    for confi in root.find('sentimientos_negativos'):
        palabra_neg = confi.text.strip()  # Eliminar espacios en blanco alrededor de la palabra
        if palabra_neg not in [palabra.text.strip() for palabra in sentimientos_negativos.findall('palabra')]:
            ET.SubElement(sentimientos_negativos, "palabra").text = palabra_neg
        else:
            sentimientos_duplicados_negativos.append(palabra_neg)
            # Si la palabra ya existe en la lista de sentimientos negativos, devuelve un error
            return "La configuración ya se encuentra en la base de datos", 400  # 400 es el código de error "Bad Request"
    
    # Guardar el archivo XML
    tree = ET.ElementTree(elementos)
    tree.write(xml_config)

    #Crear la estructura XML de respuesta
    respuesta = ET.Element("CONFIG_RECIBIDA")
    ET.SubElement(respuesta, "PALABRAS_POSITIVAS").text = str(len(sentimientos_positivos.findall('palabra')))
    ET.SubElement(respuesta, "PALABRAS_POSITIVAS_RECHAZADA").text = str(len(sentimientos_duplicados_positivos))
    ET.SubElement(respuesta, "PALABRAS_NEGATIVAS").text = str(len(sentimientos_negativos.findall('palabra')))
    ET.SubElement(respuesta, "PALABRAS_NEGATIVAS_RECHAZADA").text = str(len(sentimientos_duplicados_negativos))

    #Convierte la respuesta XML en una cadena
    response_xml = ET.tostring(respuesta, encoding='utf8', method='xml')
    
    #Retorna la respuesta con el tipo de contenido adecuado
    return response_xml, 200, {'Content-Type': 'application/xml'}



#Metodo GET para mostrar los mensajes grabados!
@app.route('/getdata', methods=['GET']) 
def mostrar_msg_json():
    
    #Comprobamos si el archivo xml existe
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}),404

    #Carga XML existente
    tree = ET.parse(xml_file)
    elementos = tree.getroot()
    result_msg = []

    for elemento in elementos.findall('MENSAJE'):
        date = elemento.find('FECHA').text
        cont_msg = elemento.find('TEXTO').text
        obj = {
            'Fecha': date,
            'Mensajes': cont_msg,
        }
        result_msg.append(obj)

    return jsonify(result_msg),200

#Metodo GET para mostrar la config grabada!
@app.route('/getconfig', methods=['GET']) 
def mostrar_config_json():
    
    #Comprobamos si el archivo xml existe
    if not os.path.exists(xml_config):
        return jsonify({"message": "No existe el archivo XML"}),404

    #Carga XML existente
    tree = ET.parse(xml_config)
    dic_config = tree.getroot()
    result_msg = []

    # Buscar sentimientos positivos
    sentimientos_positivos = dic_config.find('sentimientos_positivos')
    if sentimientos_positivos is not None:
        for palabra_pos in sentimientos_positivos.findall('palabra'):
            obj = {
                'Palabra Positiva': palabra_pos.text
            }
            result_msg.append(obj)

    # Buscar sentimientos negativos
    sentimientos_negativos = dic_config.find('sentimientos_negativos')
    if sentimientos_negativos is not None:
        for palabra_neg in sentimientos_negativos.findall('palabra'):
            obj = {
                'Palabra Negativa': palabra_neg.text
            }
            result_msg.append(obj)

    return jsonify(result_msg), 200


#Metodo POST para limpiar las bases de datos
@app.route('/limpiarDatos', methods=['POST'])
def borrar_archivos():
    try:
        #Comprobar si el archivo XML de mensajes existe y borrarlo si es así
        if os.path.exists(xml_file):
            os.remove(xml_file)

        #Comprobar si el archivo XML de configuraciones existe y borrarlo si es así
        if os.path.exists(xml_config):
            os.remove(xml_config)

        #Crear la estructura XML de respuesta
        respuesta = ET.Element("ARCHIVOS_BORRADOS")
        ET.SubElement(respuesta, "MENSAJE").text = "Los archivos bd.xml y config.xml han sido borrados."

        #Convierte la respuesta XML en una cadena
        response_xml = ET.tostring(respuesta, encoding='utf8', method='xml')

        #Retorna la respuesta con el tipo de contenido adecuado
        return response_xml, 200, {'Content-Type': 'application/xml'}

    except Exception as e:
        return jsonify({"error": f"Error al borrar archivos: {str(e)}"}, 500)

#Metodo GET que devolvera los Hashtags grabados con su fecha y en cuantos mensajes se menciono
@app.route('/devolverHashtags', methods=['GET'])
def get_hashtags():
    #Comprobar si el archivo XML existe
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}), 404

    #Comprobar si el archivo XML está vacío
    if os.path.getsize(xml_file) == 0:
        return jsonify({"message": "El archivo XML está vacío"}), 404

    #Cargar XML existente
    tree = ET.parse(xml_file)
    elementos = tree.getroot()
    result_msg = []

    #Inicializar un diccionario para realizar un seguimiento de los hashtags existentes y su frecuencia
    hashtags_existentes = defaultdict(int)

    #Recorrer los mensajes
    for elemento in elementos.findall('MENSAJE'):
        fecha_text = elemento.find('FECHA').text

        #Extraer la fecha en formato "DD/MM/YYYY"
        fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text).group()  

        cont_msg = elemento.find('TEXTO').text

        #Buscar hashtags en el mensaje
        hashtags = [hashtag.lower() for hashtag in re.findall(r'#\w+#', cont_msg)]

        for hashtag in hashtags:
            hashtags_existentes[hashtag] += 1  # Incrementar la frecuencia del hashtag

        msg_data = {
            "FECHA": fecha,
            "HASHTAGS": []
        }

        #Agregar hashtags y conteo al mensaje
        for hashtag in hashtags:
            msg_data["HASHTAGS"].append(hashtag)
            msg_data["HASHTAGS"].append(f"{hashtags_existentes[hashtag]}")

        result_msg.append(msg_data)

    #Filtrar los resultados por fecha en formato "DD/MM/YYYY"
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    if start_date_str and end_date_str:
        filtered_results = []
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
        end_date = datetime.strptime(end_date_str, "%d/%m/%Y")

        for msg in result_msg:
            msg_date = datetime.strptime(msg['FECHA'], "%d/%m/%Y")
            if start_date <= msg_date <= end_date:
                filtered_results.append(msg)

        #Crear una lista de hashtags y sus conteos para los mensajes filtrados
        hashtags_list = [{"hashtag": hashtag, "count": count} for msg in filtered_results for hashtag, count in zip(msg['HASHTAGS'][::2], msg['HASHTAGS'][1::2])]

        return jsonify(filtered_results), 200
    else:
        #Si no se proporcionaron fechas de inicio y fin, devolver todos los resultados
        return jsonify(result_msg), 200


#Metodo GET que devolvera los Usuarios grabados con su fecha y en cuantos mensajes se menciono  
@app.route('/devolverMenciones', methods=['GET'])
def get_menciones():
    #Comprobar si el archivo XML existe
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}), 404

    #Cargar XML existente
    tree = ET.parse(xml_file)
    elementos = tree.getroot()
    menciones_por_fecha = defaultdict(list)

    #Recorrer los mensajes
    for elemento in elementos.findall('MENSAJE'):
        mensaje_text = elemento.find('TEXTO').text
        fecha_text = elemento.find('FECHA').text
        fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text).group()

        #Encuentra menciones en el mensaje (suponiendo que las menciones tienen el formato '@usuario')
        menciones = re.findall(r'@(\w+)', mensaje_text)

        for mencion in menciones:
            menciones_por_fecha[fecha].append(mencion)

    #Filtrar los resultados por fecha en formato "DD/MM/YYYY"
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')
    
    if start_date_str and end_date_str:
        filtered_menciones_por_fecha = {}
        start_date_obj = datetime.strptime(start_date_str, "%d/%m/%Y")
        end_date_obj = datetime.strptime(end_date_str, "%d/%m/%Y")
        
        for fecha, menciones in menciones_por_fecha.items():
            fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
            if start_date_obj <= fecha_obj <= end_date_obj:
                filtered_menciones_por_fecha[fecha] = menciones
    else:
        filtered_menciones_por_fecha = menciones_por_fecha

    #Convierte el diccionario de menciones por fecha a un formato de respuesta
    result_msg = []
    for fecha, menciones in filtered_menciones_por_fecha.items():
        menciones_usuario = defaultdict(int)
        for mencion in menciones:
            menciones_usuario[mencion] += 1
        
        result_msg.append({"Fecha": fecha, "usuarios": menciones_usuario})

    return jsonify(result_msg), 200


#Método GET para devolver las estadísticas de hashtags
@app.route('/stats_hashtags', methods=['GET'])
def stats_hashtags():
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}), 404

    if os.path.getsize(xml_file) == 0:
        return jsonify({"message": "El archivo XML está vacío"}), 404

    tree = ET.parse(xml_file)
    elementos = tree.getroot()
    
    hashtag_data = defaultdict(list)

    for elemento in elementos.findall('MENSAJE'):
        fecha_text = elemento.find('FECHA').text
        fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text).group()

        cont_msg = elemento.find('TEXTO').text

        hashtags = [hashtag.lower() for hashtag in re.findall(r'#\w+#', cont_msg)]

        for hashtag in hashtags:
            hashtag_data[fecha].append(hashtag)

    #Convertir el diccionario a un formato de respuesta
    response_data = []
    for fecha, hashtags in hashtag_data.items():
        hashtags_count = {hashtag: hashtags.count(hashtag) for hashtag in set(hashtags)}
        msg_data = {
            "FECHA": fecha,
            "HASHTAGS": [{"hashtag": hashtag, "count": count} for hashtag, count in hashtags_count.items()]
        }
        response_data.append(msg_data)

    return jsonify(response_data), 200

#Método GET que devolverá los usuarios mencionados con su fecha y cuántas veces fueron mencionados
@app.route('/stats_menciones', methods=['GET'])
def stats_menciones():
    # Comprobar si el archivo XML existe
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}), 404

    #Cargar el XML existente
    tree = ET.parse(xml_file)
    elementos = tree.getroot()
    menciones_por_fecha = defaultdict(list)

    #Recorrer los mensajes
    for elemento in elementos.findall('MENSAJE'):
        mensaje_text = elemento.find('TEXTO').text
        fecha_text = elemento.find('FECHA').text
        fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text).group()

        #Encuentra menciones en el mensaje (suponiendo que las menciones tienen el formato '@usuario')
        menciones = re.findall(r'@(\w+)', mensaje_text)

        for mencion in menciones:
            menciones_por_fecha[fecha].append(mencion)

    #Filtrar los resultados por fecha en formato "DD/MM/YYYY"
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    if start_date_str and end_date_str:
        filtered_menciones_por_fecha = {}
        start_date_obj = datetime.strptime(start_date_str, "%d/%m/%Y")
        end_date_obj = datetime.strptime(end_date_str, "%d/%m/%Y")

        for fecha, menciones in menciones_por_fecha.items():
            fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
            if start_date_obj <= fecha_obj <= end_date_obj:
                filtered_menciones_por_fecha[fecha] = menciones
    else:
        filtered_menciones_por_fecha = menciones_por_fecha

    #Convierte el diccionario de menciones por fecha a un formato de respuesta
    result_msg = []
    for fecha, menciones in filtered_menciones_por_fecha.items():
        menciones_usuario = defaultdict(int)
        for mencion in menciones:
            menciones_usuario[mencion] += 1

        result_msg.append({"Fecha": fecha, "usuarios": menciones_usuario})

    return jsonify(result_msg), 200



#Ruta GET para obtener mensajes clasificados por sentimiento
@app.route('/get_messages', methods=['GET'])
def get_messages():
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}), 404

    tree = ET.parse(xml_file)
    elementos = tree.getroot()

    if not os.path.exists(xml_config):
        return jsonify({"message": "No existe el archivo config.xml"}), 404

    config_tree = ET.parse(xml_config)
    config_root = config_tree.getroot()

    sentimientos_positivos = [elem.text for elem in config_root.findall('.//sentimientos_positivos/palabra')]
    sentimientos_negativos = [elem.text for elem in config_root.findall('.//sentimientos_negativos/palabra')]

    mensajes_por_fecha = defaultdict(lambda: {"positivos": 0, "negativos": 0, "neutros": 0})

    #Recorrer los mensajes
    for elemento in elementos.findall('MENSAJE'):
        mensaje_text = elemento.find('TEXTO').text
        fecha_text = elemento.find('FECHA').text
        numero_mensaje_element = elemento.find('NUMERO')  # Busca el elemento con el número de mensaje

        if numero_mensaje_element is not None:
            numero_mensaje = numero_mensaje_element.text
        else:
            numero_mensaje = "N/A"  # Establecer "N/A" como número de mensaje si no se encuentra

        fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text)

        if fecha:
            fecha = fecha.group()

            #Inicializar el diccionario anidado con valores iniciales
            mensajes_por_fecha[fecha] = {"positivos": 0, "negativos": 0, "neutros": 0, "mensajes_texto": [], "numeros_mensaje": []}

            #Analizar el mensaje en busca de palabras clave de sentimientos
            palabras = mensaje_text.split()
            sentimiento = "neutros"

            for palabra in palabras:
                if palabra in sentimientos_positivos:
                    sentimiento = "positivos"
                    break  # Si es positivo, no es necesario seguir buscando
                elif palabra in sentimientos_negativos:
                    sentimiento = "negativos"
                    break  # Si es negativo, no es necesario seguir buscando

            mensajes_por_fecha[fecha][sentimiento] += 1
            mensajes_por_fecha[fecha]["mensajes_texto"].append(mensaje_text)
            mensajes_por_fecha[fecha]["numeros_mensaje"].append(numero_mensaje)  # Agregar el texto del mensaje

    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    if start_date_str and end_date_str:
        filtered_mensajes_por_fecha = {}
        start_date_obj = datetime.strptime(start_date_str, "%d/%m/%Y")
        end_date_obj = datetime.strptime(end_date_str, "%d/%m/%Y")

        for fecha, mensajes in mensajes_por_fecha.items():
            fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
            if start_date_obj <= fecha_obj <= end_date_obj:
                numeros_mensaje = []  # Lista para almacenar los números de los mensajes
                mensaje_textos = []  # Lista para almacenar los textos de los mensajes
                for elemento in elementos.findall('MENSAJE'):
                    mensaje_text = elemento.find('TEXTO').text
                    fecha_text = elemento.find('FECHA').text
                    fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text)
                    if fecha:
                        fecha = fecha.group()
                        if fecha == fecha:
                            palabras = mensaje_text.split()
                            numeros = [palabra for palabra in palabras if palabra.isdigit()]
                            mensaje_textos.append(mensaje_text)
                            numeros_mensaje.extend(numeros)
                filtered_mensajes_por_fecha[fecha] = {
                    "positivos": mensajes["positivos"],
                    "negativos": mensajes["negativos"],
                    "neutros": mensajes["neutros"],
                    "numeros_mensaje": numeros_mensaje,
                    "mensajes_texto": mensaje_textos
                }
    else:
        filtered_mensajes_por_fecha = mensajes_por_fecha

    #Genera la respuesta JSON
    result_msg = []
    for fecha, mensajes in filtered_mensajes_por_fecha.items():
        fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
        fecha_str = fecha_obj.strftime("%d/%m/%Y")
        positivos = mensajes["positivos"]
        negativos = mensajes["negativos"]
        neutros = mensajes["neutros"]

        mensaje_textos = mensajes["mensajes_texto"]  # Acceder al texto de los mensajes
        mensaje_numeros = mensajes["numeros_mensaje"]  # Acceder a los números de mensaje

        result_msg.append({
            "FECHA": fecha_str,
            "MENSAJES_POSITIVOS": positivos,
            "MENSAJES_NEGATIVOS": negativos,
            "MENSAJES_NEUTROS": neutros,
            "MENSAJES_TEXTO": mensaje_textos,
            "MENSAJES_NUMEROS": mensaje_numeros
        })

    return jsonify(result_msg), 200


#Método GET para devolver estadísticas de sentimientos
@app.route('/stats_sentimientos', methods=['GET'])
def stats_sentimientos():
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}), 404

    if os.path.getsize(xml_file) == 0:
        return jsonify({"message": "El archivo XML está vacío"}), 404

    tree = ET.parse(xml_file)
    elementos = tree.getroot()

    config_tree = ET.parse(xml_config)
    config_root = config_tree.getroot()

    sentimientos_positivos = [elem.text for elem in config_root.findall('.//sentimientos_positivos/palabra')]
    sentimientos_negativos = [elem.text for elem in config_root.findall('.//sentimientos_negativos/palabra')]

    sentimiento_data = defaultdict(list)

    for elemento in elementos.findall('MENSAJE'):
        fecha_text = elemento.find('FECHA').text
        fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text).group()

        mensaje_text = elemento.find('TEXTO').text

        palabras = mensaje_text.split()
        sentimiento = "neutros"

        for palabra in palabras:
            if palabra in sentimientos_positivos:
                sentimiento = "positivos"
                break  # Si es positivo, no es necesario seguir buscando
            elif palabra in sentimientos_negativos:
                sentimiento = "negativos"
                break  # Si es negativo, no es necesario seguir buscando

        sentimiento_data[fecha].append(sentimiento)

    # Convertir el diccionario a un formato de respuesta
    response_data = []
    for fecha, sentimientos in sentimiento_data.items():
        sentimientos_count = {"positivos": sentimientos.count("positivos"), "negativos": sentimientos.count("negativos"), "neutros": sentimientos.count("neutros")}
        msg_data = {
            "FECHA": fecha,
            "SENTIMIENTOS": sentimientos_count
        }
        response_data.append(msg_data)

    return jsonify(response_data), 200



#Metodo que inicia la aplicacion
if __name__ == '__main__':
    app.run(debug = True)