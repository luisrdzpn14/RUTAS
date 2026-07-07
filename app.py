"""
Analizador de Rutas — App web interactiva (Streamlit + Google Routes API)

Compara trayectos en auto entre varios orígenes y varios destinos a una hora
dada (de salida o de llegada), mostrando hasta 3 rutas alternativas por
combinación en un mapa interactivo, con tiempo estimado con tráfico y km.

Uso:  streamlit run app.py
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import folium
import polyline as pl
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

from rutas_api import (
    RutasAPIError,
    compute_para_llegada,
    compute_routes,
    formatear_minutos,
    parse_duration,
)

TZ_LOCAL = ZoneInfo("America/Mexico_City")

COLORES = [
    "#1a73e8", "#e8710a", "#188038", "#d93025", "#9334e6",
    "#12b5cb", "#f9ab00", "#c5221f", "#7cb342", "#5f6368",
]

st.set_page_config(page_title="Analizador de Rutas", page_icon="🗺️", layout="wide")

load_dotenv()

st.title("🗺️ Analizador de Rutas")
st.caption(
    "Compara trayectos en auto entre varios orígenes y destinos a una hora dada, "
    "con tráfico de Google y hasta 3 rutas alternativas por combinación."
)

# ─────────────────────────────  Sidebar: configuración  ─────────────────────────────

with st.sidebar:
    st.header("⚙️ Configuración")

    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if api_key:
        st.success("API key cargada desde .env")
    else:
        api_key = st.text_input("Google Maps API key", type="password")
        st.info("Tip: crea un archivo .env con GOOGLE_MAPS_API_KEY=tu_key")

    modo = st.radio(
        "El horario es la hora de…",
        ["Llegada", "Salida"],
        help=(
            "Llegada: '¿a qué hora debo salir para llegar a las 8:00?' — "
            "Salida: 'si salgo a las 7:20, ¿cuánto tardo y a qué hora llego?'"
        ),
    )

    hoy_local = datetime.now(TZ_LOCAL)
    fecha = st.date_input(
        "Fecha del viaje",
        value=(hoy_local + timedelta(days=1)).date(),
        min_value=hoy_local.date(),
        help="El tráfico se predice para esta fecha y hora (debe ser futura).",
    )
    hora = st.time_input("Hora", value=datetime.strptime("08:00", "%H:%M").time(), step=300)

    alternativas = st.checkbox("Incluir rutas alternativas (hasta 3)", value=True)

    st.divider()
    st.caption(
        "Cada combinación origen×destino consume 1–3 llamadas a la Routes API. "
        "Google incluye una capa gratuita mensual."
    )

# ─────────────────────────────  Inputs principales  ─────────────────────────────

col_o, col_d = st.columns(2)
with col_o:
    origenes_txt = st.text_area(
        "📍 Orígenes (uno por línea)",
        placeholder="Plaza Candiles, Corregidora, Qro.\nCapital Sur, El Marqués, Qro.",
        height=140,
    )
with col_d:
    destinos_txt = st.text_area(
        "🏁 Destinos (uno por línea)",
        placeholder="Manuel Gómez Morín 3960, Centro Sur, Querétaro",
        height=140,
    )

origenes = [o.strip() for o in origenes_txt.splitlines() if o.strip()]
destinos = [d.strip() for d in destinos_txt.splitlines() if d.strip()]

analizar = st.button(
    "🔍 Analizar rutas",
    type="primary",
    disabled=not (api_key and origenes and destinos),
    use_container_width=True,
)

# ─────────────────────────────  Consulta a la API  ─────────────────────────────

if analizar:
    dt_local = datetime.combine(fecha, hora, tzinfo=TZ_LOCAL)
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))

    resultados = []   # una fila por ruta
    errores = []
    total = len(origenes) * len(destinos)
    progreso = st.progress(0.0, text="Consultando rutas…")

    par_idx = 0
    for origen in origenes:
        for destino in destinos:
            etiqueta = f"{origen} → {destino}"
            progreso.progress(par_idx / total, text=f"Consultando: {etiqueta}")
            try:
                if modo == "Llegada":
                    rutas, salida_utc = compute_para_llegada(
                        api_key, origen, destino, dt_utc, alternativas
                    )
                else:
                    rutas = compute_routes(api_key, origen, destino, dt_utc, alternativas)
                    salida_utc = dt_utc

                if not rutas:
                    errores.append(f"{etiqueta}: la API no encontró rutas.")
                for j, ruta in enumerate(rutas[:3]):
                    seg = parse_duration(ruta["duration"])
                    seg_sin = parse_duration(ruta.get("staticDuration", ruta["duration"]))
                    salida_local = salida_utc.astimezone(TZ_LOCAL)
                    llegada_local = salida_local + timedelta(seconds=seg)
                    resultados.append(
                        {
                            "par": etiqueta,
                            "par_idx": par_idx,
                            "origen": origen,
                            "destino": destino,
                            "ruta_n": j + 1,
                            "via": ruta.get("description", f"Ruta {j + 1}"),
                            "segundos": seg,
                            "tiempo": formatear_minutos(seg),
                            "tiempo_sin_trafico": formatear_minutos(seg_sin),
                            "km": round(ruta.get("distanceMeters", 0) / 1000, 1),
                            "salida": salida_local.strftime("%H:%M"),
                            "llegada": llegada_local.strftime("%H:%M"),
                            "polyline": ruta.get("polyline", {}).get("encodedPolyline", ""),
                        }
                    )
            except RutasAPIError as e:
                errores.append(f"{etiqueta}: {e}")
            except Exception as e:  # red, timeout, etc.
                errores.append(f"{etiqueta}: error inesperado — {e}")
            par_idx += 1

    progreso.empty()
    st.session_state["resultados"] = resultados
    st.session_state["errores"] = errores
    st.session_state["consulta"] = {
        "modo": modo,
        "cuando": dt_local.strftime("%A %d/%m/%Y %H:%M"),
    }

# ─────────────────────────────  Resultados  ─────────────────────────────

resultados = st.session_state.get("resultados", [])
errores = st.session_state.get("errores", [])
consulta = st.session_state.get("consulta", {})

for err in errores:
    st.error(err)

if resultados:
    st.subheader(
        f"📊 Resumen — hora de {consulta.get('modo', '').lower()}: {consulta.get('cuando', '')}"
    )

    # Mejor ruta de cada par, ordenadas de más rápida a más lenta
    mejores = {}
    for r in resultados:
        if r["par"] not in mejores or r["segundos"] < mejores[r["par"]]["segundos"]:
            mejores[r["par"]] = r
    ranking = sorted(mejores.values(), key=lambda x: x["segundos"])

    ganador = ranking[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Mejor combinación", ganador["par"], border=True)
    c2.metric("Tiempo con tráfico", ganador["tiempo"], border=True)
    c3.metric("Distancia", f"{ganador['km']} km", border=True)

    tabla = [
        {
            "🏆": "★" if i == 0 else "",
            "Origen": r["origen"],
            "Destino": r["destino"],
            "Mejor vía": r["via"],
            "Tiempo (tráfico)": r["tiempo"],
            "Km": r["km"],
            "Salida": r["salida"],
            "Llegada": r["llegada"],
            "vs. mejor": "—" if i == 0 else f"+{formatear_minutos(r['segundos'] - ranking[0]['segundos'])}",
        }
        for i, r in enumerate(ranking)
    ]
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    # Detalle por combinación: todas las rutas alternativas
    st.subheader("🛣️ Rutas alternativas por combinación")
    pares = sorted({r["par"] for r in resultados}, key=lambda p: mejores[p]["segundos"])
    for par in pares:
        rutas_par = sorted(
            (r for r in resultados if r["par"] == par), key=lambda x: x["segundos"]
        )
        with st.expander(f"{par} — mejor: {rutas_par[0]['tiempo']} ({rutas_par[0]['km']} km)"):
            st.dataframe(
                [
                    {
                        "Ruta": f"{'★ ' if k == 0 else ''}Vía {r['via']}",
                        "Tiempo (tráfico)": r["tiempo"],
                        "Sin tráfico": r["tiempo_sin_trafico"],
                        "Km": r["km"],
                        "Salida": r["salida"],
                        "Llegada": r["llegada"],
                    }
                    for k, r in enumerate(rutas_par)
                ],
                use_container_width=True,
                hide_index=True,
            )

    # ─────────────  Mapa  ─────────────
    st.subheader("🗺️ Mapa de trayectos")
    st.caption(
        "Cada combinación origen→destino tiene un color; la ruta más rápida va en línea "
        "sólida y las alternativas punteadas. Usa el control de capas (arriba a la "
        "derecha del mapa) para mostrar u ocultar combinaciones."
    )

    puntos_todos = []
    mapa = folium.Map(tiles="cartodbpositron")

    for r in resultados:
        if r["polyline"]:
            puntos_todos.extend(pl.decode(r["polyline"]))

    if puntos_todos:
        lats = [p[0] for p in puntos_todos]
        lons = [p[1] for p in puntos_todos]
        mapa.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    for par in pares:
        color = COLORES[mejores[par]["par_idx"] % len(COLORES)]
        grupo = folium.FeatureGroup(name=par, show=True)
        rutas_par = sorted(
            (r for r in resultados if r["par"] == par), key=lambda x: x["segundos"]
        )
        for k, r in enumerate(rutas_par):
            if not r["polyline"]:
                continue
            coords = pl.decode(r["polyline"])
            folium.PolyLine(
                coords,
                color=color,
                weight=6 if k == 0 else 3,
                opacity=0.9 if k == 0 else 0.6,
                dash_array=None if k == 0 else "8",
                tooltip=f"{par} | vía {r['via']} | {r['tiempo']} | {r['km']} km",
            ).add_to(grupo)
            if k == 0 and coords:
                folium.Marker(
                    coords[0],
                    tooltip=f"Origen: {r['origen']}",
                    icon=folium.Icon(color="green", icon="play"),
                ).add_to(grupo)
                folium.Marker(
                    coords[-1],
                    tooltip=f"Destino: {r['destino']}",
                    icon=folium.Icon(color="red", icon="flag"),
                ).add_to(grupo)
        grupo.add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    st_folium(mapa, width=None, height=560, returned_objects=[])

elif not analizar:
    st.info(
        "Escribe al menos un origen y un destino (pueden ser varios, uno por línea), "
        "elige el horario en la barra lateral y presiona **Analizar rutas**."
    )
