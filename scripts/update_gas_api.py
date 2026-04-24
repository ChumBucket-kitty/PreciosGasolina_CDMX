import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime

def run_update():
    # Enlaces de Azure (Espejos oficiales más estables)
    URL_PLACES = "https://publicacionexterna.azurewebsites.net/publicaciones/places"
    URL_PRICES = "https://publicacionexterna.azurewebsites.net/publicaciones/prices"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 1. Obtener metadatos
        res_prices = requests.get(URL_PRICES, headers=headers, timeout=30)
        last_mod = res_prices.headers.get('Last-Modified', 'Sin fecha')

        # 2. Procesar Estaciones
        res_places = requests.get(URL_PLACES, headers=headers, timeout=30)
        root_places = ET.fromstring(res_places.content)
        
        cdmx_data = {}
        
        for place in root_places.findall('place'):
            # Extraemos la dirección y la convertimos a mayúsculas para comparar
            address_node = place.find('.//address')
            address_text = address_node.text.upper() if address_node is not None else ""
            
            # Filtro: ¿La dirección dice CDMX o está en el rango de coordenadas?
            es_cdmx = False
            if "CIUDAD DE MEXICO" in address_text or "DISTRITO FEDERAL" in address_text or "CDMX" in address_text:
                es_cdmx = True
            
            # Refuerzo por coordenadas si el texto falla
            loc = place.find('location')
            if loc is not None and not es_cdmx:
                try:
                    lat = float(loc.find('y').text)
                    lon = float(loc.find('x').text)
                    if 19.0 <= lat <= 19.6 and -99.4 <= lon <= -98.8:
                        es_cdmx = True
                except: pass

            if es_cdmx:
                pid = place.get('place_id')
                cdmx_data[pid] = {
                    "id": pid,
                    "nombre": place.find('name').text,
                    "cre_id": place.find('cre_id').text if place.find('cre_id') is not None else "",
                    "direccion": address_text,
                    "precios": {}
                }

        # 3. Inyectar Precios (Solo a las que ya filtramos como CDMX)
        root_prices = ET.fromstring(res_prices.content)
        for place in root_prices.findall('place'):
            pid = place.get('place_id')
            if pid in cdmx_data:
                for p in place.findall('gas_price'):
                    tipo = p.get('type') # regular, premium o diesel
                    try:
                        cdmx_data[pid]["precios"][tipo] = float(p.text)
                    except: pass

        # 4. Generar Respuesta Final
        # Eliminamos estaciones que no tengan precios reportados para limpiar la API
        resultados_finales = [v for v in cdmx_data.values() if v["precios"]]

        api_output = {
            "status": "success",
            "updated_at_server": last_mod,
            "sync_time": datetime.now().isoformat(),
            "count": len(resultados_finales),
            "results": resultados_finales
        }

        with open('gas_api_cdmx.json', 'w', encoding='utf-8') as f:
            json.dump(api_output, f, indent=4, ensure_ascii=False)
            
        print(f"Éxito: Se encontraron {len(resultados_finales)} estaciones en CDMX.")

    except Exception as e:
        print(f"Error en la ejecución: {e}")

if __name__ == "__main__":
    run_update()
