for place in root_places.findall('place'):
            # 1. Intentamos obtener la dirección de varias formas
            address_text = ""
            # Buscamos en cualquier nivel el nodo 'address'
            addr_node = place.find('.//address')
            
            if addr_node is not None:
                # Si tiene texto directo lo tomamos
                if addr_node.text:
                    address_text = addr_node.text.strip().upper()
                # Si no tiene texto pero tiene hijos (calle, colonia), los unimos
                else:
                    parts = [child.text for child in addr_node if child.text]
                    address_text = " ".join(parts).upper()
            
            # 2. Filtro de CDMX
            es_cdmx = False
            if any(palabra in address_text for palabra in ["CIUDAD DE MEXICO", "DISTRITO FEDERAL", "CDMX", "MEXICO DF"]):
                es_cdmx = True
            
            # Refuerzo por coordenadas
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
                # Si por alguna razón sigue vacío, ponemos una etiqueta por defecto
                final_address = address_text if address_text else "DIRECCIÓN NO DISPONIBLE EN ORIGEN"
                
                cdmx_data[pid] = {
                    "id": pid,
                    "nombre": place.find('name').text if place.find('name') is not None else "SIN NOMBRE",
                    "cre_id": place.find('cre_id').text if place.find('cre_id') is not None else "",
                    "direccion": final_address,
                    "precios": {}
                }
