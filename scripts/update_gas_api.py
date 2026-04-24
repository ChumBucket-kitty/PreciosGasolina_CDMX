import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import pytz

def run_update():
    # URL de los espejos oficiales en Azure
    URL_PLACES = "https://publicacionexterna.azurewebsites.net/publicaciones/places"
    URL_PRICES = "https://publicacionexterna.azurewebsites.net/publicaciones/prices"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Configuración de zona horaria CDMX
    tz_cdmx = pytz.timezone('America/Mexico_City')
    fecha_actual = datetime.now(tz_cdmx).strftime("%Y-%m-%d %H:%M:%S")

    try:
        print("Descargando datos...")
        res_prices = requests.get(URL_PRICES, headers=headers, timeout=45)
        root_prices = ET.fromstring(res_prices.content)

        res_places = requests.get(URL_PLACES, headers=headers, timeout=45)
        root_places = ET.fromstring(res_places.content)
        
        cdmx_data = {}
        
        # Coordenadas aproximadas para cubrir CDMX (Bounding Box)
        LAT_MIN, LAT_MAX = 19.04, 19.59
        LON_MIN, LON_MAX = -99.36, -98.94

        print("Analizando ubicaciones geográficas...")
        for place in root_places.findall('place'):
            pid = place.get('place_id')
            loc = place.find('location')
            
            if loc is not None:
                try:
                    lat = float(loc.find('y').text)
                    lon = float(loc.find('x').text)
                    
                    # Verificamos si la estación está dentro de los límites de CDMX
                    if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
                        name_node = place.find('name')
                        cre_node = place.find('cre_id')
                        
                        cdmx_data[pid] = {
                            "id": pid,
                            "nombre": name_node.text.strip() if name_node is not None else "SIN NOMBRE",
                            "cre_id": cre_node.text.strip() if cre_node is not None else "N/A",
                            "coords": {"lat": lat, "lon": lon},
                            "precios": {}
                        }
                except (ValueError, AttributeError):
                    continue

        print(f"Estaciones en zona CDMX: {len(cdmx_data)}")

        # Cruzar con precios
        for place in root_prices.findall('place'):
            pid = place.get('place_id')
            if pid in cdmx_data:
                for p in place.findall('gas_price'):
                    tipo = p.get('type')
                    try:
                        cdmx_data[pid]["precios"][tipo] = float(p.text)
                    except ValueError:
                        continue

        # Filtrar solo las que tienen precios reportados
        final_list = [v for v in cdmx_data.values() if v["precios"]]

        # Estructura del JSON con la nota solicitada
        api_output = {
            "_nota_actualizacion": f"Datos sincronizados el {fecha_actual} (Hora CDMX). Filtrado por geolocalización.",
            "metadata": {
                "total_estaciones": len(final_list),
                "zona_busqueda": "CDMX (Coords)"
            },
            "results": final_list
        }

        with open('gas_api_cdmx.json', 'w', encoding='utf-8') as f:
            json.dump(api_output, f, indent=4, ensure_ascii=False)
            
        print(f"Éxito: Archivo generado con {len(final_list)} estaciones.")

    except Exception as e:
        print(f"Error crítico en el script: {e}")

if __name__ == "__main__":
    run_update()
