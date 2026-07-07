"""
Cliente de Google Routes API (v2) para el Analizador de Rutas.

Calcula rutas en auto con tráfico en tiempo real, incluyendo hasta 3 rutas
alternativas con su polilínea para dibujarlas en un mapa.
"""

from datetime import datetime, timedelta, timezone

import requests

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

FIELD_MASK = ",".join(
    [
        "routes.duration",
        "routes.staticDuration",
        "routes.distanceMeters",
        "routes.description",
        "routes.polyline.encodedPolyline",
        "routes.warnings",
    ]
)


class RutasAPIError(Exception):
    """Error devuelto por la Routes API, con mensaje legible para el usuario."""


def parse_duration(valor: str) -> int:
    """Convierte una duración de la API ('1935s') a segundos enteros."""
    return int(float(valor.rstrip("s")))


def formatear_minutos(segundos: int) -> str:
    mins = round(segundos / 60)
    if mins < 60:
        return f"{mins} min"
    return f"{mins // 60}h {mins % 60:02d}min"


def compute_routes(
    api_key: str,
    origen: str,
    destino: str,
    departure_utc: datetime,
    alternativas: bool = True,
    timeout: int = 30,
) -> list[dict]:
    """Consulta la Routes API y devuelve la lista de rutas (la primera es la principal)."""
    # La API rechaza horas de salida en el pasado
    ahora = datetime.now(timezone.utc)
    if departure_utc < ahora + timedelta(seconds=30):
        departure_utc = ahora + timedelta(seconds=60)

    body = {
        "origin": {"address": origen},
        "destination": {"address": destino},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
        "departureTime": departure_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "computeAlternativeRoutes": alternativas,
        "languageCode": "es-419",
        "regionCode": "MX",
        "units": "METRIC",
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    resp = requests.post(ROUTES_URL, json=body, headers=headers, timeout=timeout)
    data = resp.json()

    if resp.status_code != 200:
        err = data.get("error", {})
        msg = err.get("message", f"HTTP {resp.status_code}")
        if err.get("status") == "PERMISSION_DENIED" and "has not been used" in msg:
            raise RutasAPIError(
                "La Routes API no está habilitada en tu proyecto de Google Cloud. "
                "Habilítala aquí (1 clic) y espera unos minutos: "
                "https://console.cloud.google.com/apis/library/routes.googleapis.com"
            )
        raise RutasAPIError(f"Error de la Routes API: {msg}")

    return data.get("routes", [])


def compute_para_llegada(
    api_key: str,
    origen: str,
    destino: str,
    arrival_utc: datetime,
    alternativas: bool = True,
    max_iter: int = 3,
) -> tuple[list[dict], datetime]:
    """
    Modo "hora de llegada" para auto: la Routes API solo acepta hora de salida
    en modo DRIVE, así que se itera ajustando la salida hasta que
    salida + duración ≈ hora de llegada deseada.

    Devuelve (rutas, hora_salida_sugerida_utc).
    """
    departure = arrival_utc - timedelta(minutes=45)  # estimación inicial
    rutas: list[dict] = []
    for _ in range(max_iter):
        rutas = compute_routes(api_key, origen, destino, departure, alternativas)
        if not rutas:
            return [], departure
        mejor = min(parse_duration(r["duration"]) for r in rutas)
        nueva_salida = arrival_utc - timedelta(seconds=mejor)
        if abs((nueva_salida - departure).total_seconds()) < 120:
            departure = nueva_salida
            break
        departure = nueva_salida
    return rutas, departure
