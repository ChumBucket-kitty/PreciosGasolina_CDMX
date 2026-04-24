import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import pytz

def run_update():
    URL_PLACES = "https://publicacionexterna.azurewebsites.net/publicaciones/places"
    URL_PRICES = "https://publicacionexterna.azurewebsites.net/publicaciones/prices"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    tz_cdmx = pytz.timezone('America/Mexico_City')
    fecha_actual = datetime.now(tz_cdmx).strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 1. Descarga de datos
        res_prices = requests.get(URL_PRICES, headers=headers, timeout=45)
        root_prices = ET.fromstring(res_prices.content)
        res_places = requests.get(URL_PLACES, headers=headers, timeout=45)
        root_places = ET.fromstring(res_places.content)
        
        cdmx_data = {}
        
        # LÍMITES TÉCNICOS OFICIALES CDMX
        LAT_MIN, LAT_MAX = 19.048, 19.592
        LON_MIN, LON_MAX = -99.364, -98.940

        # 2. Filtrado de estaciones
        for place in root_places.findall('place'):
            loc = place.find('location')
            if loc is not None:
                try:
                    lat = float(loc.find('y').text)
                    lon = float(loc.find('x').text)
                    if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
                        pid = place.get('place_id')
                        cdmx_data[pid] = {
                            "id": pid,
                            "nombre": place.find('name').text.strip().title(),
                            "cre_id": place.find('cre_id').text.strip() if place.find('cre_id') is not None else "N/A",
                            "coords": {"lat": lat, "lon": lon},
                            "precios": {}
                        }
                except: continue

        # 3. Procesamiento de precios y cálculo de promedios
        reg_list = []
        pre_list = []

        for place in root_prices.findall('place'):
            pid = place.get('place_id')
            if pid in cdmx_data:
                for p in place.findall('gas_price'):
                    try:
                        tipo = p.get('type')
                        val = float(p.text)
                        cdmx_data[pid]["precios"][tipo] = val
                        if tipo == 'regular': reg_list.append(val)
                        if tipo == 'premium': pre_list.append(val)
                    except: continue

        # 4. Estadísticas finales
        avg_reg = round(sum(reg_list) / len(reg_list), 2) if reg_list else 0
        avg_pre = round(sum(pre_list) / len(pre_list), 2) if pre_list else 0
        final_results = [v for v in cdmx_data.values() if v["precios"]]

        # 5. Salida JSON estructurada para humanos y sistemas (SAP)
        api_output = {
            "_resumen_ejecutivo": {
                "ultima_actualizacion": fecha_actual,
                "promedio_regular_cdmx": f"${avg_reg} MXN",
                "promedio_premium_cdmx": f"${avg_pre} MXN",
                "total_estaciones_activas": len(final_results)
            },
            "metadata": {
                "nota": "Filtro geográfico de alta precisión aplicado.",
                "fuente_datos": "CRE Azure Mirror"
            },
            "results": final_results
        }

        with open('gas_api_cdmx.json', 'w', encoding='utf-8') as f:
            json.dump(api_output, f, indent=4, ensure_ascii=False)
            
        print(f"Sincronización completa. Promedio Regular: ${avg_reg}")

    except Exception as e:
        print(f"Error en el proceso: {e}")

if __name__ == "__main__":
    run_update()
