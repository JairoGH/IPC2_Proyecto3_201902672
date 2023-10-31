from flask import Flask, request, jsonify
from xml.etree import ElementTree as ET
import re
import os
from collections import defaultdict

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

    # Inicializar un conjunto para realizar un seguimiento de los textos de los mensajes existentes
    textos_existentes = set(elemento.find('TEXTO').text for elemento in elementos.findall('MENSAJE'))

    # Inicializar contadores para usuarios y hashtags
    usuario_count = 0
    hashtag_count = 0
    fechas = []

    # Definir expresiones regulares
    usuario_pattern = r'@[\w_]+'
    hashtag_pattern = r'#[\w]+#'
    fecha_pattern = r'\d{2}/\d{2}/\d{4}'  # Formato DD/MM/YYYY

    mensajes_grabados = 0  # Para llevar un registro de los mensajes grabados
    mensajes_duplicados = 0  # Para llevar un registro de los mensajes duplicados

    # Recorremos el archivo XML
    for mensaje in root.findall('MENSAJE'):
        cont_msg = mensaje.find('TEXTO').text

        # Verificar si el mensaje ya existe en el archivo
        if cont_msg in textos_existentes:
            mensajes_duplicados += 1  # Incrementar el contador de mensajes duplicados
            continue  # Mensaje duplicado, omitir

        fecha_node = mensaje.find('FECHA')  # Obtener el nodo de fecha

        if fecha_node is not None:
            fecha_text = fecha_node.text
            fecha_match = re.search(fecha_pattern, fecha_text)

            if fecha_match:
                fecha = fecha_match.group()
                fechas.append(fecha)
                fecha_node.text = fecha  # Actualizar el texto de la fecha al formato DD/MM/YYYY

        # Crear la estructura del mensaje en el XML
        elemento = ET.SubElement(elementos, 'MENSAJE')
        ET.SubElement(elemento, "FECHA").text = fecha_text  # Agregar la fecha original
        ET.SubElement(elemento, "TEXTO").text = cont_msg

        # Agregar las fechas, usuarios y hashtags al mensaje
        for usuario in re.findall(usuario_pattern, cont_msg):
            ET.SubElement(elemento, "USUARIO_EN_MENSAJE").text = usuario
            usuario_count += 1  # Actualizar el contador de usuarios
        for hashtag in re.findall(hashtag_pattern, cont_msg):
            ET.SubElement(elemento, "HASHTAG_EN_MENSAJE").text = hashtag
            hashtag_count += 1  # Actualizar el contador de hashtags

        textos_existentes.add(cont_msg)  # Agregar el texto del nuevo mensaje al conjunto

        mensajes_grabados += 1  # Incrementar el contador de mensajes grabados

    # Guardar el archivo XML
    tree = ET.ElementTree(elementos)
    tree.write(xml_file)

    # Crear la estructura XML de respuesta
    respuesta_xml = ET.Element('MENSAJES_RECIBIDOS')
    tiempo = ET.SubElement(respuesta_xml, 'TIEMPO')

    # Comprobar si se encontraron fechas y agregarlas a la respuesta
    if fechas:
        ET.SubElement(tiempo, 'FECHAS').text = ', '.join(fechas)
    else:
        ET.SubElement(tiempo, 'FECHAS').text = "No se encontraron fechas"

    ET.SubElement(tiempo, 'MSJ_RECIBIDOS').text = str(mensajes_grabados)  # Usar el contador de mensajes grabados
    ET.SubElement(tiempo, 'USR_MENCIONADOS').text = str(usuario_count)
    ET.SubElement(tiempo, 'HASH_INCLUIDOS').text = str(hashtag_count)

    # Agregar un mensaje que indique los mensajes duplicados, si los hay
    if mensajes_duplicados > 0:
        ET.SubElement(tiempo, 'MENSAJES_DUPLICADOS').text = f"{mensajes_duplicados} mensajes ya están registrados."

    # Serializar la estructura XML de respuesta a una cadena y retornarla
    respuesta_str = ET.tostring(respuesta_xml, encoding='unicode')
    return respuesta_str, 200, {'Content-Type': 'application/xml'}
    
def is_date(dates):
    pattern = r'^\d{2}\/\d{2}\/\d{4}$'    
    return re.match(pattern, dates) is not None

def is_user(cont_msg):
    pattern_user = r'(@\w+)'
    return re.match(pattern_user, cont_msg) is not None

#Metodo POST para grabar la configuracion!
@app.route('/grabarConfiguracion', methods=['POST']) 
def grabar_config():
    # Obtener el XML de la solicitud
    xml_data_config = request.data
    root = ET.fromstring(xml_data_config)

    # Cargar el XML existente si existe
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

    # Lista para almacenar sentimientos duplicados
    sentimientos_duplicados_positivos = []
    sentimientos_duplicados_negativos = []

    # Procesar sentimientos positivos
    for config in root.find('sentimientos_positivos'):
        palabra_pos = config.text.strip()  # Eliminar espacios en blanco alrededor de la palabra
        if palabra_pos not in [palabra.text.strip() for palabra in sentimientos_positivos.findall('palabra')]:
            ET.SubElement(sentimientos_positivos, "palabra").text = palabra_pos
        else:
            sentimientos_duplicados_positivos.append(palabra_pos)

    # Procesar sentimientos negativos
    for confi in root.find('sentimientos_negativos'):
        palabra_neg = confi.text.strip()  # Eliminar espacios en blanco alrededor de la palabra
        if palabra_neg not in [palabra.text.strip() for palabra in sentimientos_negativos.findall('palabra')]:
            ET.SubElement(sentimientos_negativos, "palabra").text = palabra_neg
        else:
            sentimientos_duplicados_negativos.append(palabra_neg)

    # Guardar el archivo XML
    tree = ET.ElementTree(elementos)
    tree.write(xml_config)

    # Crear la estructura XML de respuesta
    respuesta = ET.Element("CONFIG_RECIBIDA")
    ET.SubElement(respuesta, "PALABRAS_POSITIVAS").text = str(len(root.find('sentimientos_positivos')))
    ET.SubElement(respuesta, "PALABRAS_POSITIVAS_RECHAZADA").text = "0"  # Establecer a 0
    ET.SubElement(respuesta, "PALABRAS_NEGATIVAS").text = str(len(root.find('sentimientos_negativos')))
    ET.SubElement(respuesta, "PALABRAS_NEGATIVAS_RECHAZADA").text = "0"  # Establecer a 0

    # Convierte la respuesta XML en una cadena
    response_xml = ET.tostring(respuesta, encoding='utf8', method='xml')
    
    # Retorna la respuesta con el tipo de contenido adecuado
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
def limpiar_datos():

    # Comprobar si el archivo XML de mensajes existe
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML de mensajes"}), 404

    # Cargar XML de mensajes existente
    tree_mensajes = ET.parse(xml_file)
    elementos_mensajes = tree_mensajes.getroot()

    # Eliminar todos los mensajes
    for elemento in elementos_mensajes.findall('MENSAJE'):
        elementos_mensajes.remove(elemento)

    # Guardar el archivo XML de mensajes
    tree_mensajes = ET.ElementTree(elementos_mensajes)
    tree_mensajes.write(xml_file)

    # Comprobar si el archivo XML de configuraciones existe
    if not os.path.exists(xml_config):
        return jsonify({"message": "No existe el archivo XML de configuraciones"}), 404

    # Cargar XML de configuraciones existente
    tree_configuraciones = ET.parse(xml_config)
    elementos_configuraciones = tree_configuraciones.getroot()

    # Eliminar todos los elementos de configuraciones
    elementos_configuraciones.clear()

    # Guardar el archivo XML de configuraciones
    tree_configuraciones = ET.ElementTree(elementos_configuraciones)
    tree_configuraciones.write(xml_config)

    # Crear la estructura XML de respuesta
    respuesta = ET.Element("MENSAJES_ELIMINADOS")
    ET.SubElement(respuesta, "MENSAJES").text = "Todos los mensajes y configuraciones han sido eliminados."

    # Convierte la respuesta XML en una cadena
    response_xml = ET.tostring(respuesta, encoding='utf8', method='xml')

    # Retorna la respuesta con el tipo de contenido adecuado
    return response_xml, 200, {'Content-Type': 'application/xml'}


#Metodo GET que devolvera los Hashtags grabados con su fecha y en cuantos mensajes se menciono
@app.route('/devolverHashtags', methods=['GET'])
def get_hashtags():
    # Comprobar si el archivo XML existe
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}), 404

    # Cargar XML existente
    tree = ET.parse(xml_file)
    elementos = tree.getroot()
    result_msg = []

    # Inicializar un diccionario para realizar un seguimiento de los hashtags existentes y su frecuencia
    hashtags_existentes = defaultdict(int)

    # Recorrer los mensajes
    for elemento in elementos.findall('MENSAJE'):
        fecha_text = elemento.find('FECHA').text
        fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text).group()  # Extraer la fecha en formato "DD/MM/YYYY"

        cont_msg = elemento.find('TEXTO').text

        # Buscar hashtags en el mensaje
        hashtags = [hashtag.lower() for hashtag in re.findall(r'#\w+#', cont_msg)]

        for hashtag in hashtags:
            hashtags_existentes[hashtag] += 1  # Incrementar la frecuencia del hashtag

        msg_data = {
            "FECHA": fecha,
            "HASHTAGS": []
        }

        # Agregar hashtags y conteo al mensaje
        for hashtag in hashtags:
            msg_data["HASHTAGS"].append(hashtag)
            msg_data["HASHTAGS"].append(f"{hashtags_existentes[hashtag]} mensaje(s)")

        result_msg.append(msg_data)

    return jsonify(result_msg), 200

#Metodo GET que devolvera los Usuarios grabados con su fecha y en cuantos mensajes se menciono  
@app.route('/devolverMenciones', methods=['GET'])
def get_menciones():
    # Comprobar si el archivo XML existe
    if not os.path.exists(xml_file):
        return jsonify({"message": "No existe el archivo XML"}), 404

    # Cargar XML existente
    tree = ET.parse(xml_file)
    elementos = tree.getroot()
    menciones_por_fecha = defaultdict(list)

    # Recorrer los mensajes
    for elemento in elementos.findall('MENSAJE'):
        mensaje_text = elemento.find('TEXTO').text
        fecha_text = elemento.find('FECHA').text
        fecha = re.search(r'\d{2}/\d{2}/\d{4}', fecha_text).group()
        
        # Encuentra menciones en el mensaje (suponiendo que las menciones tienen el formato '@usuario')
        menciones = re.findall(r'@(\w+)', mensaje_text)
        
        for mencion in menciones:
            menciones_por_fecha[fecha].append(mencion)

    # Convierte el diccionario de menciones por fecha a un formato de respuesta
    result_msg = []
    for fecha, menciones in menciones_por_fecha.items():
        menciones_usuario = defaultdict(int)
        for mencion in menciones:
            menciones_usuario[mencion] += 1
        
        menciones_usuario = [{"usuario": usuario, "menciones": menciones} for usuario, menciones in menciones_usuario.items()]
        
        result_msg.append({"Fecha": fecha, "usuarios": menciones_usuario})

    return jsonify(result_msg), 200


#Metodo que inicia la aplicacion
if __name__ == '__main__':
    app.run(debug = True)