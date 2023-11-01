from django.shortcuts import render, redirect

import os
import json
import requests
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


def upload_m(request):
    response_content = None
    if request.method == "POST":
        xml_file = request.FILES.get('xmlFile')  # Obtener el archivo XML cargado
        if xml_file:
            content = xml_file.read().decode('utf-8')  # Leer y decodificar el contenido del archivo
            print(content)
            # Hacer petición a la API
            api_url = url + "/grabarMensajes"
            headers = {
                'Content-Type': 'application/xml'  # Suponiendo que la API espera XML
            }
            response = requests.post(api_url, data=content, headers=headers)
            
            # Aquí puedes manejar la respuesta como lo necesites
            if response.status_code == 200:
                response_content = response.text
            else:
                # Puedes manejar errores de manera más específica aquí si lo necesitas
                return JsonResponse({"error": "Error al enviar datos a la API."}, status=400)
    return render(request, 'upload_m.html', {'response_content': response_content})  # Enviar el contenido de la respuesta al template

def upload_c(request):
    response_content = None
    error_message = None 

    if request.method == "POST":

        # Obtener el archivo XML cargado
        xml_file = request.FILES.get('xmlFile')  
        if xml_file:
            content = xml_file.read().decode('utf-8') 
            print(content)

            #Se hace la peticion a la API
            api_url = url + "/grabarConfiguracion"
            headers = {
                'Content-Type': 'application/xml'
            }
            response = requests.post(api_url, data=content, headers=headers)
            
            # Respuesta de la API
            if response.status_code == 200:
                response_content = response.text
            else:
                #Mensaje de Error si no se puede enviar la solicitud a la API
                error_message = response.text
    
    return render(request, 'upload_c.html', {'response_content': response_content, 'error_message': error_message})
        

def limpiar_datos(request):
    if request.method == 'POST':
        try:
            # URL de la API de Flask para borrar archivos
            api_url = url + "/limpiarDatos"  # Reemplaza con la URL de tu API para borrar archivos
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



def get_hashtags(request):
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')

    contexto = {
        'hashtags': [],
        'startDate': start_date_str,
        'endDate': end_date_str
    }

    try:
        # Dar Formato a las fechas en el formato correcto "DD/MM/YYYY"
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            start_date = None

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            end_date = None

        # URL de la API de Flask para obtener los hashtags
        api_url = "http://localhost:5000/devolverHashtags"
        params = {}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date

        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            try:
                # Cargar los hashtags de la respuesta JSON
                all_hashtags = response.json()
                contexto['hashtags'] = all_hashtags
            except json.JSONDecodeError as e:
                print("Error al cargar JSON:", str(e))
        else:
            print("Error al obtener los datos de la API")

    except ValueError as e:
        print("Error al formatear las fechas:", str(e))

    return render(request, "get_hashtags.html", contexto)


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

def info_estudiante(request):
    return render(request, "info_estudiante.html")

def stats_hashtags(request):
    contexto = {
        'response': [],
        'hashtags_data': []  # Agrega esta variable para los hashtags utilizados
    }
    response = requests.get(url + "/stats_hashtags")
    
    if response.status_code == 200:
        data = response.json()
        contexto['response'] = data
        hashtags_data = []

        # Itera a través de los datos para obtener los hashtags y su conteo
        for item in data:
            fecha = item['FECHA']
            hashtags = item['HASHTAGS']
            hashtags_data.append({'fecha': fecha, 'hashtags': hashtags})

        contexto['hashtags_data'] = hashtags_data
        
    return render(request, "stats_hashtags.html", contexto)

def stats_menciones(request):
    contexto = {
        'response': [],
        'usuarios_data': []  # Agrega esta variable para los usuarios mencionados
    }
    response = requests.get(url + "/stats_menciones")
    
    if response.status_code == 200:
        data = response.json()
        contexto['response'] = data
        usuarios_data = []

        # Itera a través de los datos para obtener los usuarios mencionados y su conteo
        for item in data:
            fecha = item['Fecha']
            usuarios = item['usuarios']
            usuarios_data.append({'fecha': fecha, 'usuarios': usuarios})

        contexto['usuarios_data'] = usuarios_data
        
    return render(request, "stats_menciones.html", contexto)