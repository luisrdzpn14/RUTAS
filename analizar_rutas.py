"""
Analizador de Rutas - Google Distance Matrix API
Compara tiempos de viaje desde múltiples orígenes a tu trabajo
Uso: python analizar_rutas.py
"""

import os
import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─────────────────────────────────────────────
#  CONFIGURACIÓN — edita aquí tus datos
# ─────────────────────────────────────────────

# La API key se lee del archivo .env (GOOGLE_MAPS_API_KEY=...), nunca del código
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "TU_API_KEY_AQUI")

DESTINO = "LIC. MANUEL GOMEZ MORIN NO. 3960 CENTRO SUR, HIRG PARK CORPORATE, QUERETARO, QRO. "

ORIGENES = [
    "CAPITAL SUR, EL MARQUES, QRO.",
    "MANAHAL, CORREGIDORA, QRO.",
    "VILLAS LA JOYA, QUERETARO, QRO.",
    "PLAZA CANDILES, CORREGIDORA, QRO.",
    "PASEOS DEL BOSQUE, CORREGIDORA, QRO.",
]

# Días: 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes
# Hora de llegada: Lun-Jue = 8:00 AM, Vie = 9:00 AM
HORARIO = {
    0: 8,  # Lunes → 8am
    1: 8,  # Martes → 8am
    2: 8,  # Miércoles → 8am
    3: 8,  # Jueves → 8am
    4: 9,  # Viernes → 9am
}

# ─────────────────────────────────────────────


def get_arrival_timestamp(dia_semana: int) -> int:
    """Calcula el timestamp UNIX de la próxima llegada en el día indicado."""
    hora = HORARIO[dia_semana]
    hoy = datetime.now()
    dias_hasta = (dia_semana - hoy.weekday() + 7) % 7
    if dias_hasta == 0 and hoy.hour >= hora:
        dias_hasta = 7
    target = hoy + timedelta(days=dias_hasta)
    target = target.replace(hour=hora, minute=0, second=0, microsecond=0)
    return int(target.timestamp())


def consultar_api(origenes: list, destino: str, arrival_time: int) -> dict:
    """Llama a Distance Matrix API y devuelve el JSON."""
    params = {
        "origins": "|".join(origenes),
        "destinations": destino,
        "arrival_time": arrival_time,
        "language": "es",
        "region": "mx",
        "key": API_KEY,
    }
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())


def formatear_minutos(segundos: int) -> str:
    mins = segundos // 60
    if mins < 60:
        return f"{mins} min"
    return f"{mins // 60}h {mins % 60}min"


def analizar(dia_semana: int):
    nombre_dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"][dia_semana]
    hora = HORARIO[dia_semana]
    arrival_ts = get_arrival_timestamp(dia_semana)

    print(f"\n{'═' * 58}")
    print(f"  Analizador de Rutas — {nombre_dia} {hora}:00 AM")
    print(f"  Destino: {DESTINO}")
    print(f"{'═' * 58}")

    data = consultar_api(ORIGENES, DESTINO, arrival_ts)

    if data.get("status") != "OK":
        print(f"  ERROR de API: {data.get('status')}")
        print(f"  Mensaje: {data.get('error_message', 'Sin detalle')}")
        return

    resultados = []
    for i, row in enumerate(data["rows"]):
        el = row["elements"][0]
        if el["status"] != "OK":
            print(f"  [!] No se pudo calcular ruta desde: {ORIGENES[i]} ({el['status']})")
            continue
        dur = el.get("duration_in_traffic", el["duration"])["value"]
        dist = el["distance"]["text"]
        resultados.append({
            "origen": ORIGENES[i],
            "segundos": dur,
            "tiempo": formatear_minutos(dur),
            "distancia": dist,
        })

    resultados.sort(key=lambda x: x["segundos"])
    min_seg = resultados[0]["segundos"] if resultados else 0

    print(f"\n  {'#':<4} {'Origen':<32} {'Tiempo':<12} {'Distancia':<12} Diff")
    print(f"  {'─' * 72}")

    for i, r in enumerate(resultados):
        diff = r["segundos"] - min_seg
        diff_str = "  —  mejor ruta" if diff == 0 else f"  +{formatear_minutos(diff)}"
        marca = "★" if i == 0 else " "
        print(f"  {marca} {i+1:<3} {r['origen'][:30]:<32} {r['tiempo']:<12} {r['distancia']:<12}{diff_str}")

    print(f"\n  Ganador: {resultados[0]['origen']}")
    print(f"  Tiempo estimado con tráfico: {resultados[0]['tiempo']} ({resultados[0]['distancia']})")
    print(f"{'═' * 58}\n")


def menu():
    print("\n╔══════════════════════════════════════╗")
    print("║    Analizador de Rutas — AP73        ║")
    print("╠══════════════════════════════════════╣")
    print("║  1) Lunes (8:00 AM)                  ║")
    print("║  2) Martes (8:00 AM)                 ║")
    print("║  3) Miércoles (8:00 AM)              ║")
    print("║  4) Jueves (8:00 AM)                 ║")
    print("║  5) Viernes (9:00 AM)                ║")
    print("║  6) Todos los días                   ║")
    print("║  0) Salir                            ║")
    print("╚══════════════════════════════════════╝")

    while True:
        try:
            op = input("\n  Selecciona opción: ").strip()
            if op == "0":
                break
            elif op in ["1", "2", "3", "4", "5"]:
                analizar(int(op) - 1)
            elif op == "6":
                for d in range(5):
                    analizar(d)
            else:
                print("  Opción no válida.")
        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    if API_KEY == "TU_API_KEY_AQUI":
        print("\n⚠ Crea un archivo .env con GOOGLE_MAPS_API_KEY=tu_api_key (ver .env.example).\n")
    else:
        menu()
