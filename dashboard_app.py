import json
import time
from dataclasses import dataclass

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

import paho.mqtt.client as mqtt
from influxdb_client_3 import InfluxDBClient3
import requests


# -----------------------------
# Config
# -----------------------------
CATALOG_URL = "http://localhost:8080"      # Catalog CherryPy [file:34]
INFLUX_HOST = "http://localhost:8181"      # cambia se Influx Docker non è su questa porta
INFLUX_TOKEN = "apiv3_qkhm2kiMdFeqH7127QV_5-6dak5IwIrzr7Fy85eEnYpyXs2o46NdAvqqYm8BLUOWKxAO83-3UuoB9A9ikLpXVQ"
INFLUX_DB = "pole_measurements"            # database Influx (nome DB) [file:33]
INFLUX_TABLE = "pole_measurements"         # measurement/table scritta dal writer [file:33]


# -----------------------------
# Catalog REST
# -----------------------------
def load_catalog(base_url: str) -> dict:
    topics = requests.get(f"{base_url}/topic", timeout=3).json()           # {backEnd, dashboard} [file:34]
    broker = requests.get(f"{base_url}/central_broker", timeout=3).json()  # {address, port} [file:34]
    threshold = requests.get(f"{base_url}/threshold", timeout=3).json()    # {threshold: ...} [file:34]
    gateways = requests.get(f"{base_url}/gateways", timeout=3).json()      # list gateways [file:34]

    return {
        "topic": topics,
        "central_broker": broker,
        "threshold": threshold,
        "gateways": gateways,
    }


def iter_poles_from_catalog(cat: dict):
    for gw in cat.get("gateways", []):
        gw_id = gw.get("gateway_id")
        zone = gw.get("zone")
        for p in gw.get("smart_poles", []):
            yield {
                "gateway_id": gw_id,
                "zone": zone,
                "pole_id": p.get("id"),
                "lat": p.get("lat"),
                "lon": p.get("long"),
                "topic": p.get("topic"),
                "active": p.get("active", True),   
            }



# -----------------------------
# InfluxDB 3
# -----------------------------
@st.cache_resource
def influx_client():
    return InfluxDBClient3(host=INFLUX_HOST, token=INFLUX_TOKEN, database=INFLUX_DB)


def q_last_measurements(client: InfluxDBClient3, minutes: int = 240) -> pd.DataFrame:
    sql = f"""
    SELECT
      time,
      pole_id,
      gateway_id,
      temperature,
      humidity,
      tilt,
      decay
    FROM {INFLUX_TABLE}
    WHERE time >= now() - interval '{minutes} minute'
    """
    df = client.query(sql).to_pandas()
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"])
    return df


def last_by_pole(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.sort_values("time")
    return df.groupby("pole_id", as_index=False).tail(1)


def q_pole_history(client: InfluxDBClient3, pole_id: str, minutes: int = 720) -> pd.DataFrame:
    sql = f"""
    SELECT
      time,
      temperature,
      humidity,
      tilt,
      decay
    FROM {INFLUX_TABLE}
    WHERE pole_id = '{pole_id}'
      AND time >= now() - interval '{minutes} minute'
    ORDER BY time DESC
    LIMIT 200
    """
    df = client.query(sql).to_pandas()
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"])
    return df


# -----------------------------
# Alerts model
# -----------------------------
@dataclass
class AlertEvent:
    ts: float
    gateway_id: str
    pole_id: str
    payload: dict


def ensure_state():
    if "alerts" not in st.session_state:
        st.session_state.alerts = {}  # pole_id -> AlertEvent
    if "mqtt_ready" not in st.session_state:
        st.session_state.mqtt_ready = False


# -----------------------------
# MQTT (NO THREAD): setup + pump
# -----------------------------
def mqtt_setup(cat: dict):
    ensure_state()
    if st.session_state.mqtt_ready:
        return

    alert_base = cat.get("topic", {}).get("dashboard", "alert")  # default "alert" [file:29]
    broker = cat.get("central_broker", {})
    host = broker.get("address", "127.0.0.1")
    port = int(broker.get("port", 1884))

    def on_connect(client, userdata, flags, reason_code, properties=None):
        client.subscribe(f"{alert_base}/#")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        # checkThreshold payload: gateway_id, pole_id, value, threshold... [file:31]
        pole = payload.get("pole_id")
        if not pole:
            return

        st.session_state.alerts[pole] = AlertEvent(
            ts=time.time(),
            gateway_id=payload.get("gateway_id", ""),
            pole_id=pole,
            payload=payload
        )

    c = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="dashboard-subs")
    c.on_connect = on_connect
    c.on_message = on_message
    c.connect(host, port)

    st.session_state.mqtt_client = c
    st.session_state.mqtt_alert_base = alert_base
    st.session_state.mqtt_ready = True


def mqtt_pump():
    # Processa messaggi pendenti (chiamata ad ogni rerun)
    if "mqtt_client" in st.session_state:
        st.session_state.mqtt_client.loop(timeout=0.05)


# -----------------------------
# UI helpers
# -----------------------------
def pole_color(pole_id: str, decay_value, alerts: dict) -> str:
    if pole_id in alerts:
        return "#E53935"  # red
    try:
        if decay_value is not None and float(decay_value) > 50.0:
            return "#FB8C00"  # orange
    except Exception:
        pass
    return "#2E7D32"  # green


# -----------------------------
# Streamlit page
# -----------------------------
st.set_page_config(page_title="Smart Poles Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; }
    .kpi { border-radius: 14px; padding: 14px; background: #0b1220; color: #e5e7eb; }
    .kpi small { color: #9ca3af; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Smart Poles Monitoring")

with st.sidebar:
    st.header("Controlli")
    history_minutes = st.slider("Storico per palo (minuti)", 60, 24 * 60, 12 * 60, step=60)

    st.divider()
    st.caption("Catalog REST")
    st.code(CATALOG_URL)
    st.caption("Influx")
    st.code(f"{INFLUX_HOST} | DB={INFLUX_DB} | table={INFLUX_TABLE}")

# Trigger rerun periodico
st.query_params["t"] = str(int(time.time() / 10))

# Init
ensure_state()

# Catalog REST
cat = load_catalog(CATALOG_URL)

# MQTT alerts
mqtt_setup(cat)
mqtt_pump()

# TTL alerts
now = time.time()
ttl_s = 10 * 60
st.session_state.alerts = {
    pid: ev for pid, ev in st.session_state.alerts.items()
    if (now - ev.ts) <= ttl_s
}

# Poles from catalog
poles_df = pd.DataFrame(list(iter_poles_from_catalog(cat)))

# Influx data
client = influx_client()
raw_df = q_last_measurements(client, minutes=240)
last_df = last_by_pole(raw_df)

# Merge catalog + last measurement
if not poles_df.empty and not last_df.empty:
    merged = poles_df.merge(last_df, on="pole_id", how="left", suffixes=("_cat", "_db"))
    # tieni gateway dal catalog (associazione palo->gateway) [file:29]
    if "gateway_id_cat" in merged.columns:
        merged["gateway_id"] = merged["gateway_id_cat"]
    elif "gateway_id" not in merged.columns and "gateway_id_db" in merged.columns:
        merged["gateway_id"] = merged["gateway_id_db"]
else:
    merged = poles_df.copy()
    for c in ["temperature", "humidity", "tilt", "decay", "time", "gateway_id"]:
        if c not in merged.columns:
            merged[c] = None

# KPI
colA, colB, colC, colD = st.columns(4)
n_poles = int(merged["pole_id"].nunique()) if not merged.empty else 0
n_alert = len(st.session_state.alerts)
n_decay = int((pd.to_numeric(merged.get("decay", pd.Series([])), errors="coerce") > 50).sum()) if not merged.empty else 0
last_update = raw_df["time"].max() if not raw_df.empty else None

colA.markdown(f"<div class='kpi'><small>Pali</small><div style='font-size:28px'>{n_poles}</div></div>", unsafe_allow_html=True)
colB.markdown(f"<div class='kpi'><small>Alert attivi</small><div style='font-size:28px'>{n_alert}</div></div>", unsafe_allow_html=True)
colC.markdown(f"<div class='kpi'><small>Decay &gt; 50%</small><div style='font-size:28px'>{n_decay}</div></div>", unsafe_allow_html=True)
colD.markdown(f"<div class='kpi'><small>Ultimo dato</small><div style='font-size:16px'>{str(last_update) if last_update is not None else '-'}</div></div>", unsafe_allow_html=True)

# Layout
left, right = st.columns([1.35, 1.0], gap="large")

with left:
    st.subheader("Mappa")

    if not merged.empty and merged[["lat", "lon"]].dropna().shape[0] > 0:
        center = [merged["lat"].mean(), merged["lon"].mean()]
        zoom = 7
    else:
        center = [45.07, 7.69]
        zoom = 11

    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

    map_df = merged.copy()
    if "active" in map_df.columns:
        map_df = map_df[map_df["active"].fillna(True) == True]

    for _, r in map_df.iterrows():
        if pd.isna(r.get("lat")) or pd.isna(r.get("lon")) or not r.get("pole_id"):
            continue

        pid = r["pole_id"]
        color = pole_color(pid, r.get("decay"), st.session_state.alerts)

        tooltip = f"{pid} ({r.get('zone','')})"
        popup_html = f"""
        <div style="min-width:240px">
          <b>{pid}</b><br/>
          Gateway: {r.get('gateway_id', '')}<br/>
          Temp: {r.get('temperature', '-') }<br/>
          Hum: {r.get('humidity', '-') }<br/>
          Tilt: {r.get('tilt', '-') }<br/>
          Decay: {r.get('decay', '-') }<br/>
          <small>Apri 'Dettagli' a destra per vedere storico</small>
        </div>
        """

        folium.CircleMarker(
            location=[float(r["lat"]), float(r["lon"])],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            tooltip=tooltip,
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(m)

    st_folium(m, height=640, use_container_width=True)

with right:
    st.subheader("Dettagli palo")

    pole_options = merged["pole_id"].dropna().unique().tolist() if not merged.empty else []
    selected = st.selectbox("Seleziona un palo", pole_options) if pole_options else None

    if selected:
        alert_ev = st.session_state.alerts.get(selected)

        st.markdown("### Stato")
        if alert_ev:
            st.error(f"ALERT attivo (tilt sopra soglia). Gateway: {alert_ev.gateway_id}")
            st.json(alert_ev.payload)
        else:
            decay_val = pd.to_numeric(merged.loc[merged["pole_id"] == selected, "decay"], errors="coerce")
            decay_val = float(decay_val.iloc[0]) if len(decay_val) else None
            if decay_val is not None and decay_val > 50.0:
                st.warning(f"Decay alto: {decay_val:.2f}%")
            else:
                st.success("OK")

        st.markdown("### Ultima misura")
        row = merged.loc[merged["pole_id"] == selected].head(1)
        cols = [c for c in ["pole_id", "gateway_id", "zone", "time", "temperature", "humidity", "tilt", "decay"] if c in row.columns]
        st.dataframe(row[cols], use_container_width=True, hide_index=True)

        st.markdown("### Storico recente (DB)")
        hist = q_pole_history(client, selected, minutes=history_minutes)
        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.info("Nessun palo selezionato.")

    st.divider()
    st.subheader("Alert live (debug)")
    st.caption(f"Sottoscritto a: {st.session_state.get('mqtt_alert_base','alert')}/#")
    if st.session_state.alerts:
        # mostra ultimi alert per tempo
        items = sorted(st.session_state.alerts.items(), key=lambda x: x[1].ts, reverse=True)
        st.write([{"pole_id": k, "ts": v.ts, **v.payload} for k, v in items[:20]])
    else:
        st.write("Nessun alert ricevuto (ancora).")
