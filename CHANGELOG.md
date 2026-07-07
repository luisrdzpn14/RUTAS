# Changelog

## v2.0.0 — 2026-07-06

### Nuevo
- **App web interactiva** (`app.py`, Streamlit): orígenes y destinos libres
  (N×N), horario interpretado como hora de salida **o** de llegada, hasta
  3 rutas alternativas por combinación.
- **Mapa interactivo** con los trayectos dibujados (ruta más rápida sólida,
  alternativas punteadas, control de capas por combinación) y marcadores de
  origen/destino.
- **Tabla resumen** con ranking de combinaciones: tiempo con tráfico, tiempo
  sin tráfico, km, hora de salida/llegada y diferencia vs. la mejor opción.
- Cliente de la **Google Routes API v2** (`rutas_api.py`) con modo
  "hora de llegada" por iteración.
- `requirements.txt`, `.env.example`, `.gitignore` y documentación completa
  en `README.md`.

### Seguridad
- La API key ya **no está en el código**: se lee de un archivo `.env`
  ignorado por git. La key que estuvo expuesta en versiones anteriores debe
  regenerarse en Google Cloud Console.

### Cambios
- `analizar_rutas.py` (versión de consola original) ahora lee la key desde
  `.env` y se conserva como herramienta legada.

## v1.0.0

- Script de consola con Google Distance Matrix API: compara tiempos desde
  5 orígenes fijos a 1 destino fijo por día de la semana.
