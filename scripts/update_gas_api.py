import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import pytz # Importante para manejar el horario de CDMX

def run_update():
    URL_PLACES = "https://publicacionexterna.azurewebsites.net/publicaciones/places"
    URL_PRICES = "https://publicacionexterna.azurewebsites.net/publicaciones/prices"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Manejo de zona horaria CDMX
    tz_cdmx = pytz.timezone('America/Mexico_City')
    fecha_actual = datetime.now(tz_cdmx).strftime("%Y-%m-%d %H:%M:%S")

    try:
        res_prices = requests.get(URL_PRICES, headers=headers, timeout=45)
        last_mod_server = res_prices.headers.get('Last-Modified', 'No disponible')
        root_prices = ET.fromstring(res_prices.content)

        res_places = requests.get(URL_PLACES, headers=headers, timeout=45)
        root_places = ET.fromstring(res_places.content)
        
        cdmx_data = {}
        
        for place in root_places.findall('place'):
            address_text = ""
            addr_node = place.find('.//address')
            if addr_node is not None:
                if addr_node.text:
                    address_text = addr_node.text.strip().upper()
                else:
                    address_text = ", ".join([c.text.strip() for c in addr_node if c.text]).upper()
            
            # Filtro CDMX
            if any(k in address_text for k in ["CIUDAD DE MEXICO", "DISTRITO FEDERAL", "CDMX"]):
                pid = place.get('place_id')
                cdmx_data[pid] = {
                    "id": pid,
                    "nombre": place.find('name').text.strip() if place.find('name') is not None else "S/N",
                    "direccion": address_text,
                    "precios": {}
                }

        # Matcheo de precios
        for place in root_prices.findall('place'):
            pid = place.get('place_id')
            if pid in cdmx_data:
                for p in place.findall('gas_price'):
                    cdmx_data[pid]["precios"][p.get('type')] = float(p.text)

        # Limpiar estaciones sin precio
        final_list = [v for v in cdmx_data.values() if v["precios"]]

        # Estructura Final con la NOTA solicitada
        api_output = {
            "_nota_actualizacion": f"Datos sincronizados el {fecha_actual} (Hora CDMX). Origen: CRE Azure Mirror.",
            "metadata": {
                "ultima_modificacion_servidor": last_mod_server,
                "total_estaciones": len(final_list)
            },
            "results": final_list
        }

        with open('gas_api_cdmx.json', 'w', encoding='utf-8') as f:
            json.dump(api_output, f, indent=4, ensure_ascii=False)
            
        print(f"Sincronización exitosa: {len(final_list)} estaciones.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_update()
