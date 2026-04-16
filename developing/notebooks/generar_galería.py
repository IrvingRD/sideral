import pandas as pd
import numpy as np
import requests
import json
import os
import time
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.simbad import Simbad

# ==========================================
# CONFIGURACIÓN DEL PIPELINE
# ==========================================
NUM_POR_CLASE = 25 # Galaxias por clase (empieza con 10 o 25 para probar)
CARPETA_DESTINO = "data/images"

# 🧠 EL TRUCO SENIOR: Le pedimos a SIMBAD el nombre (id) Y el redshift (z_value)
custom_simbad = Simbad()
custom_simbad.add_votable_fields('id(1)')
custom_simbad.add_votable_fields('z_value') # Magia astronómica

# ==========================================
# FUNCIONES MATEMÁTICAS Y DE API
# ==========================================
def calcular_distancia_ly(redshift):
    """Calcula la distancia en años luz usando la ley de Hubble."""
    try:
        z = float(redshift)
        if z <= 0: return "Desconocida"
        c = 299792 # Velocidad de la luz (km/s)
        H0 = 70    # Constante de Hubble (km/s/Mpc)
        dist_mpc = (z * c) / H0
        dist_ly = dist_mpc * 3.262e6
        return f"{dist_ly:,.0f}"
    except:
        return "Desconocida"

def descargar_imagen_sdss(ra, dec, filepath):
    """Descarga un recorte limpio de 512x512 centrado en las coordenadas."""
    url = f"http://skyserver.sdss.org/dr16/SkyServerWS/ImgCutout/getjpeg?TaskName=Skyserver.Chart.Image&ra={ra}&dec={dec}&scale=0.2&width=512&height=512"
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(res.content)
        return True
    return False

# ==========================================
# EL MOTOR DEL PIPELINE (ETL)
# ==========================================
def procesar_galerias():
    print("🚀 Iniciando Pipeline ETL para Sideral...")
    
    # 1. CARGA DE DATOS (Solo necesitas tu archivo filtrado)
    archivo_clases = '/home/irving/Documentos/Diplomado/Modulo 5/Sideral/data/gz2_labels_clean.csv' # Debe tener 'dr7objid', 'label', 'ra', 'dec'
    print(f"Cargando {archivo_clases}...")
    
    df_master = pd.read_csv(archivo_clases)
    # Verifica que tengas las columnas necesarias
    for col in ['dr7objid', 'label', 'ra', 'dec']:
        if col not in df_master.columns:
            raise ValueError(f"⚠️ Error: Tu CSV necesita tener la columna '{col}'")

    # 2. MUESTREO (SAMPLING)
    clases = ['merger', 'edge_on', 'spiral', 'elliptical']
    df_sample = pd.DataFrame()
    
    for c in clases:
        muestra = df_master[df_master['label'] == c].sample(n=NUM_POR_CLASE, random_state=42)
        df_sample = pd.concat([df_sample, muestra])
        
    print(f"🎯 Muestra seleccionada: {len(df_sample)} galaxias para procesar.")

    # 3. CREACIÓN DE DIRECTORIOS Y JSON
    os.makedirs(CARPETA_DESTINO, exist_ok=True)
    metadata_json = {"galaxies": []}
    
    # 4. CICLO DE EXTRACCIÓN
    for index, row in df_sample.iterrows():
        objid = row['dr7objid']
        clase = row['label']
        ra = row['ra']
        dec = row['dec']
        
        distancia = "Desconocida" # Valor por defecto
        nombre_comun = f"SDSS {objid}"
        designacion = "Catálogo SDSS"
        
        # --- A. Consulta a SIMBAD (Nombre y Redshift) ---
        try:
            coord = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')
            resultado_simbad = custom_simbad.query_region(coord, radius=2 * u.arcsec)
            
            if resultado_simbad is not None:
                # Extraemos el nombre
                nombre_principal = resultado_simbad['MAIN_ID'][0].decode('utf-8')
                if any(cat in nombre_principal for cat in ["M ", "NGC", "IC ", "UGC"]):
                    nombre_comun = nombre_principal
                    designacion = "Catálogo Principal"
                
                # Extraemos el redshift si existe en SIMBAD
                z_val = resultado_simbad['Z_VALUE'][0]
                # En astropy, los datos faltantes están "enmascarados" (masked)
                if not np.ma.is_masked(z_val):
                    distancia = calcular_distancia_ly(z_val)
        except Exception:
            pass # Si falla SIMBAD, seguimos adelante sin detener el script
            
        # --- B. Descarga de Imagen ---
        filename = f"{clase}_{objid}.jpg"
        filepath = os.path.join(CARPETA_DESTINO, filename)
        
        if not os.path.exists(filepath):
            exito = descargar_imagen_sdss(ra, dec, filepath)
            if not exito:
                print(f"⚠️ Error descargando imagen de {objid}, omitiendo...")
                continue
            
        # --- C. Agregar al diccionario JSON ---
        metadata_json["galaxies"].append({
            "id": str(objid),
            "name": nombre_comun,
            "designation": designacion,
            "class": clase,
            "distance_ly": distancia,
            "image_file": filename,
            "description": f"Magnífico ejemplo de una galaxia de tipo {clase}, clasificada con alta precisión por voluntarios astronómicos."
        })
        
        print(f"✅ [{clase.upper()}] {nombre_comun} guardada. (Distancia: {distancia} al)")
        
        # Respetamos los servidores
        time.sleep(0.5) 

    # 5. EXPORTAR JSON FINAL
    with open('data/gallery_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata_json, f, indent=4, ensure_ascii=False)
        
    print("\n🎉 ¡ETL Finalizado! Las imágenes y el JSON están listos para Sideral.")

if __name__ == "__main__":
    procesar_galerias()