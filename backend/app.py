from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "perene.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atractivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT,
            descripcion_es TEXT,
            descripcion_en TEXT,
            descripcion_ash TEXT,
            modelo_url TEXT,
            estado TEXT DEFAULT 'Abierto'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atractivo_codigo TEXT,
            idioma TEXT,
            fecha_hora TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atractivo_codigo TEXT,
            mensaje TEXT,
            fecha_hora TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM atractivos")
    if cursor.fetchone()[0] == 0:
        datos_iniciales = [
            (
                "BAYOZ", 
                "Catarata Bayoz", 
                "Impresionante caída de agua de tres saltos rodeada de abundante vegetación en el distrito de Perené.", 
                "Impressive three-tier waterfall surrounded by lush vegetation in the Perené district.", 
                "Kametsa tasorentsi paokiki Bayoz, tsinane shinki tsiteniki Perené.",
                "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Duck/glTF-Binary/Duck.glb",
                "Abierto"
            ),
            (
                "VELO", 
                "Catarata Velo de la Novia", 
                "Caída cristalina de 55 metros que desciende por la pared rocosa como un velo nupcial.", 
                "Crystal-clear 55-meter drop cascading down the rocky cliff like a bridal veil.", 
                "Tsiteniki Velo de la Novia, tasorentsi kametsa 55 metros.",
                "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Fox/glTF-Binary/Fox.glb",
                "Abierto"
            ),
            (
                "PAMPA", 
                "Comunidad Nativa Pampa Michi", 
                "Centro de preservación cultural Asháninka donde se comparten danzas, tradiciones y artesanía ancestral.", 
                "Asháninka cultural preservation center sharing ancestral dances, traditions, and crafts.", 
                "Asháninka Pampa Michi, osheki tasorentsi kantaimentotsi.",
                "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/FlightHelmet/glTF-Binary/FlightHelmet.glb",
                "Abierto"
            ),
            (
                "MIRADOR", 
                "Mirador Turístico de Perené", 
                "Punto estratégico para admirar la majestuosidad del valle del río Perené y los campos de café.", 
                "Strategic viewpoint to admire the majesty of the Perené river valley and coffee plantations.", 
                "Kametsa irashi Perené, osheki kashiro.",
                "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/CesiumMilkTruck/glTF-Binary/CesiumMilkTruck.glb",
                "Abierto"
            )
        ]
        cursor.executemany(
            "INSERT INTO atractivos (codigo, nombre, descripcion_es, descripcion_en, descripcion_ash, modelo_url, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
            datos_iniciales
        )
    
    conn.commit()
    conn.close()

init_db()

class ReporteInput(BaseModel):
    atractivo_codigo: str
    mensaje: str

@app.get("/api/atractivo/{codigo}")
def obtener_atractivo(codigo: str, lang: str = "es"):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM atractivos WHERE codigo = ?", (codigo.upper(),))
    atractivo = cursor.fetchone()
    
    if not atractivo:
        conn.close()
        return {"error": "Atractivo no encontrado"}
    
    # Seleccionar la descripción según el idioma solicitado
    if lang == "en":
        desc = atractivo["descripcion_en"]
    elif lang == "ash":
        desc = atractivo["descripcion_ash"]
    else:
        desc = atractivo["descripcion_es"]

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO visitas (atractivo_codigo, idioma, fecha_hora) VALUES (?, ?, ?)",
        (codigo.upper(), lang.upper(), ahora)
    )
    conn.commit()
    conn.close()
    
    return {
        "id": atractivo["id"],
        "codigo": atractivo["codigo"],
        "nombre": atractivo["nombre"],
        "descripcion": desc,
        "modelo_url": atractivo["modelo_url"],
        "estado": atractivo["estado"]
    }

@app.post("/api/reporte")
def crear_reporte(reporte: ReporteInput):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO reportes (atractivo_codigo, mensaje, fecha_hora) VALUES (?, ?, ?)",
        (reporte.atractivo_codigo.upper(), reporte.mensaje, ahora)
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "mensaje": "Reporte registrado"}

@app.get("/api/estadisticas")
def obtener_estadisticas():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT atractivo_codigo, COUNT(*) as total FROM visitas GROUP BY atractivo_codigo")
    conteo = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM reportes ORDER BY id DESC LIMIT 10")
    ultimos_reportes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"visitas_por_lugar": conteo, "reportes": ultimos_reportes}