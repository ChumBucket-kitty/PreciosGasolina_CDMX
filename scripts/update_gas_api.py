import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime

def run_update():
    # Enlaces de Azure (Más estables)
    URL_PLACES = "https://publicacionexterna.azurewebsites.net/publicaciones/places"
    URL_PRICES = "https://publicacionexterna.azurewebsites.net/publicaciones/prices"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. Obtener metadatos de actualización del servidor
    res_prices = requests.get(URL_PRICES, headers=headers)
    last_mod = res_prices.headers.get('Last-Modified', 'Sin fecha')

    # 2. Procesar Estaciones (Filtrar CDMX)
    res_places = requests.get(URL_PLACES, headers=headers)
    root_places = ET.fromstring(res_places.content)
    
    cdmx_data = {}
    for place in root_places.findall('place'):
        loc = place.find('location')
        if loc is not None:
            try:
                lat = float(loc.find('y').text)
                lon = float(loc.find('x').text)
                # Cuadro geográfico CDMX
                if 19.0 <= lat <= 19.6 and -99.4 <= lon <= -98.8:
                    pid = place.get('place_id')
                    cdmx_data[pid] = {
                        "id": pid,
                        "nombre": place.find('name').text,
                        "cre_id": place.find('cre_id').text if place.find('cre_id') is not None else "",
                        "direccion": place.find('.//address').text,
                        "coords": {"lat": lat, "lon": lon},
                        "precios": {}
                    }
            except: continue

    # 3. Inyectar Precios
    root_prices = ET.fromstring(res_prices.content)
    for place in root_prices.findall('place'):
        pid = place.get('place_id')
        if pid in cdmx_data:
            for p in place.findall('gas_price'):
                cdmx_data[pid]["precios"][p.get('type')] = float(p.text)

    # 4. Generar Respuesta tipo API
    api_output = {
        "status": "success",
        "updated_at_server": last_mod,
        "sync_time": datetime.now().isoformat(),
        "count": len(cdmx_data),
        "results": list(cdmx_data.values())
    }

    # Guardamos en la raíz para acceso fácil
    with open('gas_api_cdmx.json', 'w', encoding='utf-8') as f:
        json.dump(api_output, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    run_update()
