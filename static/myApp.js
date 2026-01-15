let map;
let markers = {};
let historyChart = null;

function renderDecayChart(rows) {
  const labels = rows.map(r => r.time).reverse();
  const decay = rows.map(r => r.decay).reverse();

  const ctx = document.getElementById('decayChart');
  if (decayChart) decayChart.destroy();

  decayChart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [{ label: 'Decay', data: decay }] },
    options: { responsive: true }
  });
}

function renderTiltChart(rows) {
  const labels = rows.map(r => r.time).reverse();
  const tilt = rows.map(r => r.tilt).reverse();

  const ctx = document.getElementById('tiltChart');
  if (tiltChart) tiltChart.destroy();

  tiltChart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [{ label: 'Tilt', data: tilt }] },
    options: { responsive: true }
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


async function loadPoles() {
  const response = await fetch('/api/poles');
  const poles = await response.json();

  const totalEl = document.getElementById('totalPoles');
  if (totalEl) totalEl.innerText = poles.length;

  poles.forEach(pole => {
    if (markers[pole.id]) return;

    const marker = L.circleMarker([pole.lat, pole.lon], {
      radius: 8,
      fillColor: "#2E7D32",
      color: "#fff",
      weight: 1,
      fillOpacity: 0.8
    }).addTo(map);

    marker.bindPopup(`
        <div>
            <div style="font-weight:700;">${pole.id}</div>
            <div>Region: ${pole.region}</div>
            </div>`);

    marker.on('click', () => onPoleClick(pole)); // passiamo tutto l'oggetto

    markers[pole.id] = marker;
  });
}

function initMap() {
  map = L.map('map').setView([45.5, 9.0], 6);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

  loadPoles();
  setInterval(loadPoles, 5000);
}

window.onload = initMap;
