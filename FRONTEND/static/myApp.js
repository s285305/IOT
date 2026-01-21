let map;
let markers = {};
let historyChart = null;
// Add these to your global variables at the top
let alarmedPoles = new Set(); 
let poleDataCache = {}; // Stores the latest info for each pole

async function loadPoles() {
  const response = await fetch('/api/poles');
  const poles = await response.json();
  
  const totalEl = document.getElementById('totalPoles');
  if (totalEl) totalEl.innerText = poles.length;

  poles.forEach(pole => {
    // Save to cache so we can check health later
    poleDataCache[pole.id] = pole;

    if (!markers[pole.id]) {
      const marker = L.circleMarker([pole.lat, pole.lon], {
        radius: 9,
        weight: 2,
        fillOpacity: 0.8
      }).addTo(map);

      marker.bindPopup(`<b>ID: ${pole.id}</b><br>Region: ${pole.region}`);
      marker.on('click', () => onPoleClick(pole));
      markers[pole.id] = marker;
    }
  });

  updateStatsAndMarkers();
}

/**
 * Calculates health and updates box counts + marker colors
 */
function updateStatsAndMarkers() {
  let healthyCount = 0;
  let alarmCount = alarmedPoles.size;

  Object.values(poleDataCache).forEach(pole => {
    const isAlarmed = alarmedPoles.has(pole.id);
    
    // Logic: Healthy ONLY if No Alarms AND Decay > 50
    // Note: 'pole.decay' comes from your Catalog placeholder or last Influx sample
    const isHealthy = !isAlarmed && (pole.decay === undefined || pole.decay > 50);

    if (isHealthy) healthyCount++;

    // Update Map Marker Color
    if (markers[pole.id]) {
      const color = isAlarmed ? "#ef4444" : (isHealthy ? "#22c55e" : "#f59e0b");
      markers[pole.id].setStyle({
        fillColor: color,
        color: "#fff"
      });
    }
  });

  document.getElementById('healthyPoles').innerText = healthyCount;
  document.getElementById('activeAlarms').innerText = alarmCount;
  document.getElementById('activeAlarmsBadge').innerText = alarmCount;
}

// Add this helper for a consistent dark theme
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: 'rgba(255,255,255,0.8)', font: { size: 12 } } }
    },
    scales: {
        x: { ticks: { color: 'rgba(255,255,255,0.5)' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: 'rgba(255,255,255,0.5)' }, grid: { color: 'rgba(255,255,255,0.05)' } }
    }
};

function fmtTime(t) {
  const d = new Date(t); // funziona con ISO tipo "2026-01-21T18:15:00Z"
  return d.toLocaleString('it-IT', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' });
}

function renderDecayChart(rows) {
    const ctx = document.getElementById('decayChart').getContext('2d');
    if (decayChart) decayChart.destroy();

    decayChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: rows.map(r => fmtTime(r.time)).reverse(),
            datasets: [{
                label: 'Decay %',
                data: rows.map(r => r.decay).reverse(),
                borderColor: '#22c55e', // Success Green
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: chartOptions
    });
}

function renderTiltChart(rows) {
    const ctx = document.getElementById('tiltChart').getContext('2d');
    if (tiltChart) tiltChart.destroy();

    tiltChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: rows.map(r => fmtTime(r.time)).reverse(),
            datasets: [{
                label: 'Tilt Degrees',
                data: rows.map(r => r.tilt).reverse(),
                borderColor: '#3b82f6', // Accent Blue
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: chartOptions
    });
}

let decayChart = null;
let tiltChart = null;

async function onPoleClick(pole) {
  // dettagli statici (Catalog)
  document.getElementById('selected-pole-id').innerText = `ID: ${pole.id}`;
  document.getElementById('details-placeholder').style.display = 'none';
  document.getElementById('pole-info').style.display = 'block';

  // prendi storico da Influx
  const response = await fetch(`/api/history/${pole.id}`);
  const rows = await response.json();

  if (rows && rows.length > 0) {
    // Update the cache with the real decay value from the latest InfluxDB sample
    poleDataCache[pole.id].decay = rows[0].decay;
    updateStatsAndMarkers(); // Recalculate health
  }

  // se non ci sono dati, mostra comunque info Catalog
  const infoDiv = document.getElementById('pole-static');
  infoDiv.innerHTML = `
    <p><b>Region</b>: ${pole.region}</p>
    <p><b>Gateway</b>: ${pole.gateway}</p>
    <p><b>Lat</b>: ${pole.lat}</p>
    <p><b>Lon</b>: ${pole.lon}</p>
  `;

  if (!rows || rows.length === 0) return;

  const last = rows[0]; // ORDER BY time DESC
  const lastDiv = document.getElementById('pole-last');
  lastDiv.innerHTML = `
    <p><b>Last sample</b></p>
    <p>Time: ${last.time}</p>
    <p>Temperature: ${last.temperature}</p>
    <p>Humidity: ${last.humidity}</p>
    <p>Tilt: ${last.tilt}</p>
    <p>Decay: ${last.decay}</p>
  `;

  renderDecayChart(rows);
  renderTiltChart(rows);
}

async function fetchAlerts() {
  try {
    const response = await fetch('/api/alerts');
    const alerts = await response.json();

    if (alerts && alerts.length > 0) {
      alerts.forEach(alert => {
        // 1. Update the logical state for health tracking
        alarmedPoles.add(alert.pole_id); 
        
        // 2. Show the pop-up notification
        // showAlertNotification(alert);
        
        // 3. Add to the sidebar history list
        addAlertToList(alert);
      });
      
      // 4. Recalculate stats and change marker colors to red
      updateStatsAndMarkers(); 
    }
  } catch (error) {
    console.error("Error fetching alerts:", error);
  }
}

function initMap() {
  map = L.map('map').setView([45.5, 9.0], 6);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

  loadPoles();
  setInterval(loadPoles, 5000);
  setInterval(fetchAlerts, 3000);
  
}


/**
 * Creates a visual notification (toast) on the screen
 */
function showAlertNotification(data) {
  const container = document.getElementById('alert-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'alert-toast';
  // Assumes your MQTT message looks like: { pole_id: 'P01', alert: 'High Tilt detected' }
  toast.innerHTML = `
    <strong>⚠️ ALERT: Pole ${data.pole_id}</strong><br>
    ${data.alert || 'Threshold exceeded!'}
  `;

  container.appendChild(toast);

  // Auto-remove the notification after 5 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 500);
  }, 5000);
}

let alarmCount = 0;

function addAlertToList(data) {
  const list = document.getElementById('alert-log');
  if (!list) return;

  // Increment badge
  alarmCount++;
  const badge = document.getElementById('activeAlarmsBadge');
  const activeAlarmsEl = document.getElementById('activeAlarms');
  if (badge) badge.innerText = alarmCount;
  if (activeAlarmsEl) activeAlarmsEl.innerText = alarmCount;

  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  
  const card = document.createElement('div');
  // Assign "warning" class if the message contains certain keywords
  const isWarning = data.alert?.toLowerCase().includes('check');
  card.className = `alert-card ${isWarning ? 'warning' : ''}`;

  card.innerHTML = `
    <div class="alert-card-header">
      <span class="pole-tag">📍 Pole ${data.pole_id}</span>
      <span class="alert-time">${time}</span>
    </div>
    <span class="alert-msg">${data.alert || 'Critical Threshold Exceeded'}</span>
  `;

  // Prepend so newest is at the top
  list.insertBefore(card, list.firstChild);

  // Optional: keep only the last 10 alerts to prevent UI lag
  if (list.children.length > 10) {
    list.removeChild(list.lastChild);
  }
}

window.onload = initMap;
