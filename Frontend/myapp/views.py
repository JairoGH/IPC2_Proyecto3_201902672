from django.shortcuts import render, redirect

import os
import json
import requests
from unidecode import unidecode
import xml.etree.ElementTree as ET
from datetime import datetime
from collections import defaultdict
from django.http import HttpResponse, JsonResponse

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

url = "http://localhost:5000"


# Create your views here.
def index(request):
    return render(request, "index.html")

#Funcion para cargar los datos de mensajes de la API
def upload_m(request):
    response_content = None
    if request.method == "POST":

        #Obtener el archivo XML cargado
        xml_file = request.FILES.get('xmlFile')  
        if xml_file:
            content = xml_file.read().decode('utf-8')           
            #Convertir a UTF-8
            content = unidecode(content)

            print(content)

            # Hacer petición a la API
            api_url = url + "/grabarMensajes"
            headers = {
                'Content-Type': 'application/xml'  # Suponiendo que la API espera XML
            }
            response = requests.post(api_url, data=content, headers=headers)
            
            #Verificar la respuesta de la API
            if response.status_code == 200:
                response_content = response.text
            else:
                return JsonResponse({"error": "Error al enviar datos a la API."}, status=400)
                #Enviar el contenido de la respuesta 
    return render(request, 'upload_m.html', {'response_content': response_content})  

#Funcion para cargar los datos de Config de la API
def upload_c(request):
    response_content = None
    error_message = None 

    if request.method == "POST":

        #Obtener el archivo XML cargado
        xml_file = request.FILES.get('xmlFile')
        if xml_file:
            content = xml_file.read().decode('utf-8') 
            #Convertir a UTF-8
            content = unidecode(content)
            print(content)

            #Se hace la peticion a la API
            api_url = url + "/grabarConfiguracion"
            headers = {
                'Content-Type': 'application/xml'
            }
            response = requests.post(api_url, data=content, headers=headers)
            
            #Respuesta de la API
            if response.status_code == 200:
                response_content = response.text
            else:
                #Mensaje de Error si no se puede enviar la solicitud a la API
                error_message = response.text
    
    return render(request, 'upload_c.html', {'response_content': response_content, 'error_message': error_message})
        
#Funcion para eliminar los archivos en los que se guadan los datos
def limpiar_datos(request):
    if request.method == 'POST':
        try:
            #Realizar la peticion a la API
            api_url = url + "/limpiarDatos" 
            response = requests.post(api_url)
            
            # Verifica la respuesta de la API
            if response.status_code == 200:
                # Crear una respuesta XML
                response_xml = '<?xml version=\'1.0\' encoding=\'utf8\'?>\n<ARCHIVOS_BORRADOS>\n    <MENSAJE>Los archivos bd.xml y config.xml han sido borrados.</MENSAJE>\n</ARCHIVOS_BORRADOS>'
                return HttpResponse(response_xml, content_type='application/xml')
    
        except requests.exceptions.RequestException as e:
            response_data = {
                "error": f"Error al enviar solicitud a la API: {str(e)}"
            }
            return JsonResponse(response_data, status=500)
    else:
        return render(request, 'limpiar_datos.html')


#Funcion con la que se obtiene la informacion de los hashtags en los mensajes
def get_hashtags(request):
    #Se obtienen las fechas de inicio y fin
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')

    #Se crea el contexto, con los hashtags y fecha de inicio y fin
    contexto = {
        'hashtags': [],
        'startDate': start_date_str,
        'endDate': end_date_str
    }

    try:
        #Dar Formato a las fechas en el formato correcto "DD/MM/YYYY"
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            start_date = None

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            end_date = None

        #Se hace la peticion a la API
        api_url = url + "/devolverHashtags"
        params = {}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date

        response = requests.get(api_url, params=params)

        #Verificar la respuesta de la API
        if response.status_code == 200:
            try:
                # Cargar los hashtags de la respuesta JSON
                all_hashtags = response.json()
                contexto['hashtags'] = all_hashtags
            except json.JSONDecodeError as e:
                print("Error al cargar JSON:", str(e))
        else:
            print("Error al obtener los datos de la API")

    #Se verifica el formato de las fechas
    except ValueError as e:
        print("Error al formatear las fechas:", str(e))

    return render(request, "get_hashtags.html", contexto)

#Funcion con la que se obtiene la informacion de las menciones en los mensajes
def get_menciones(request):
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')

    contexto = {
        'menciones': [],
        'startDate': start_date_str,
        'endDate': end_date_str
    }

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            start_date = None

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            end_date = None

        api_url = "http://localhost:5000/devolverMenciones"
        params = {}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date

        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            try:
                all_menciones = response.json()
                contexto['menciones'] = all_menciones
            except json.JSONDecodeError as e:
                print("Error al cargar JSON:", str(e))
        else:
            print("Error al obtener los datos de la API")

    except ValueError as e:
        print("Error en formato de las fechas:", str(e))

    return render(request, "get_menciones.html", contexto)

#Funcion con la que muestro la pagina de informacion del estudiante
def info_estudiante(request):
    return render(request, "info_estudiante.html")


#Funcion con la que se obtienen las estadisticas de los hashtags
def stats_hashtags(request):
    contexto = {
        'response': [],
        'hashtags_data': []
    }
    response = requests.get(url + "/stats_hashtags")
    
    if response.status_code == 200:
        data = response.json()
        contexto['response'] = data
        hashtags_data = []

        #Recorro a través de los datos para obtener los hashtags y su conteo
        for item in data:
            fecha = item['FECHA']
            hashtags = item['HASHTAGS']
            hashtags_data.append({'fecha': fecha, 'hashtags': hashtags})

        contexto['hashtags_data'] = hashtags_data
        
    return render(request, "stats_hashtags.html", contexto)

#Funcion con la que se obtienen las estadisticas de las menciones
def stats_menciones(request):
    contexto = {
        'response': [],
        'usuarios_data': []
    }
    response = requests.get(url + "/stats_menciones")
    
    if response.status_code == 200:
        data = response.json()
        contexto['response'] = data
        usuarios_data = []

        #Recorre a través de los datos para obtener los usuarios mencionados y su conteo
        for item in data:
            fecha = item['Fecha']
            usuarios = item['usuarios']
            usuarios_data.append({'fecha': fecha, 'usuarios': usuarios})

        contexto['usuarios_data'] = usuarios_data
        
    return render(request, "stats_menciones.html", contexto)

#Funcion con la que se obtienen la informacion de los sentimientos en los mensajes
def get_sentimientos(request):
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')

    contexto = {
        'mensajes': [],
        'startDate': start_date_str,
        'endDate': end_date_str
    }

    try:
        api_url = "http://localhost:5000/get_messages"

        params = {}
        if start_date_str:
            start_date_api = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            params['startDate'] = start_date_api

        if end_date_str:
            end_date_api = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            params['endDate'] = end_date_api

        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            try:
                mensajes = response.json()
                contexto['mensajes'] = mensajes

            except json.JSONDecodeError as e:
                print("Error al cargar JSON:", str(e))
        else:
            print("Error al obtener los datos de la API")

    except ValueError as e:
        print("Error en el formato de las fechas:", str(e))

    return render(request, "get_sentimientos.html", contexto)

#Funcion con la que se obtienen las estadisticas de los sentimientos
def stats_sentimientos(request):
    contexto = {
        'response': []
    }
    
    response = requests.get(url + "/stats_sentimientos")
    
    if response.status_code == 200:
        data = response.json()
        contexto['response'] = data
        
    return render(request, "stats_sentimientos.html", contexto)
