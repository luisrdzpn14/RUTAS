# 🗺️ RUTAS — Analizador de Rutas con Tráfico

App web interactiva para **comparar trayectos en auto** entre varios orígenes y
varios destinos a una hora dada, usando el tráfico en tiempo real de Google.
Ideal para decidir *desde dónde conviene salir, a qué hora y por cuál ruta*
para llegar a un destino (por ejemplo, al trabajo).

## ¿Qué hace?

- **Inputs:** N orígenes y N destinos (cualquier dirección o lugar, uno por
  línea), fecha y hora del viaje, y si esa hora es de **salida** o de
  **llegada** ("quiero llegar a las 8:00 → ¿a qué hora salgo?").
- **Output:**
  - 📊 Tabla resumen con **ranking** de todas las combinaciones
    origen→destino: tiempo con tráfico, km, hora de salida/llegada y
    diferencia contra la mejor opción.
  - 🛣️ Hasta **3 rutas alternativas** por combinación (vía qué avenidas/
    carreteras, tiempo con y sin tráfico, km).
  - 🗺️ **Mapa interactivo** con los trayectos dibujados: la ruta más rápida en
    línea sólida, las alternativas punteadas, control de capas para
    mostrar/ocultar cada combinación y vista **Mapa o Satélite**.
- 🔒 **Login con contraseña** (opcional): si defines `APP_PASSWORD`, la app
  pide contraseña antes de usarse — útil al publicarla en internet.

## Requisitos

1. **Python 3.10+**
2. Una **API key de Google Maps Platform** con la **Routes API** habilitada:
   - Habilítala aquí (1 clic): <https://console.cloud.google.com/apis/library/routes.googleapis.com>
   - Google incluye una capa gratuita mensual de llamadas; cada combinación
     origen×destino consume 1–3 llamadas.

## Instalación y uso

```bash
git clone https://github.com/luisrdzpn14/RUTAS.git
cd RUTAS
pip install -r requirements.txt

# Configura tu API key (NUNCA va en el código ni en el repo)
copy .env.example .env    # en Windows  (cp en Linux/Mac)
# edita .env y pon tu key real

streamlit run app.py
```

Se abre en el navegador (por defecto <http://localhost:8501>).

## Publicar en internet (Streamlit Community Cloud, gratis)

1. Entra a <https://share.streamlit.io> con tu cuenta de GitHub.
2. **New app** → repo `luisrdzpn14/RUTAS`, branch `main`, archivo `app.py`.
3. En **Settings → Secrets** pega (con tus valores reales):

   ```toml
   GOOGLE_MAPS_API_KEY = "tu_key"
   APP_PASSWORD = "tu_contraseña"
   ```

4. Deploy. Te da una URL pública (`https://….streamlit.app`) que puedes
   compartir; quien entre necesitará la contraseña.

> La key y la contraseña viven en los *Secrets* del servidor, nunca en el
> repositorio.

## Estructura

| Archivo | Descripción |
|---|---|
| `app.py` | App web Streamlit (interfaz, tablas, mapa) |
| `rutas_api.py` | Cliente de la Google Routes API (tráfico, alternativas, modo llegada) |
| `analizar_rutas.py` | Versión original de consola (Distance Matrix API), aún funcional |
| `.env.example` | Plantilla para la API key |

## Seguridad de la API key

- La key se lee del archivo `.env`, que está en `.gitignore` y **no se sube a
  GitHub**.
- ⚠️ En versiones anteriores de este repo hubo una key expuesta en el código;
  esa key debe considerarse comprometida y **regenerarse** en
  [Google Cloud Console → Credenciales](https://console.cloud.google.com/apis/credentials).
- Recomendado: restringe la key para que solo pueda usar Routes API y
  Distance Matrix API.

## Notas técnicas

- El modo **"hora de llegada"** en auto no lo soporta la Routes API
  directamente, así que la app itera ajustando la hora de salida hasta que
  `salida + duración ≈ llegada deseada` (2–3 llamadas).
- El tráfico se predice con `TRAFFIC_AWARE_OPTIMAL`; la fecha/hora debe ser
  futura.
- Zona horaria: America/Mexico_City (Querétaro).
