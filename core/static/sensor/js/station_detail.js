// Station Detail Modal with Full Screen Leaflet Map
let currentStationData = null;
let detailMap = null;
let stationMarker = null;

function openStationDetail(stationId) {
    console.log('Opening detail for station:', stationId);
    console.log('Opening detail for station:', stationsData);

    const station = stationsData.find(s => s.id.toString() === stationId.toString());

    if (!station) {
        console.error('Station not found:', stationId);
        showToast('Station not found', 'error');
        return;
    }

    currentStationData = station;
    console.log('Station data:', station);

    // Populate info
    document.getElementById('detailStationName').textContent = station.name || 'Unnamed Station';
    document.getElementById('detailStationLocation').innerHTML = `
        <i class="fas fa-map-marker-alt text-cyan-400"></i>
        <span>${station.location || 'Unknown Location'}</span>
    `;
    document.getElementById('detailStationId').textContent = `#${station.uid || station.id}`;
    document.getElementById('detailSensorCount').textContent = station.sensorCount || 0;
    document.getElementById('detailSensorBadge').textContent = station.sensorCount || 0;

    // Parse coordinates - Handle both [lat, lng] array and "lat, lng" string formats
    let lat = null, lng = null, fullCoords = '--';

    if (station.coordinates) {
        if (Array.isArray(station.coordinates) && station.coordinates.length === 2) {
            // Array format [lat, lng]
            lat = parseFloat(station.coordinates[0]);
            lng = parseFloat(station.coordinates[1]);
            fullCoords = `${lat}, ${lng}`;
        } else if (typeof station.coordinates === 'string') {
            // String format "lat, lng"
            const parts = station.coordinates.split(',').map(p => parseFloat(p.trim()));
            if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
                lat = parts[0];
                lng = parts[1];
                fullCoords = station.coordinates;
            }
        }
    }

    console.log('Coordinates parsed:', { lat, lng, fullCoords });

    document.getElementById('detailLatitude').textContent = lat !== null ? lat.toFixed(6) : '--';
    document.getElementById('detailLongitude').textContent = lng !== null ? lng.toFixed(6) : '--';
    document.getElementById('detailCoordinates').textContent = fullCoords;

    // Show modal
    const modal = document.getElementById('stationDetailModal');
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';

    // Initialize map after modal is visible
    setTimeout(() => {
        initDetailMap(lat, lng, station);
        loadStationSensors(station);
    }, 100);
}

function closeStationDetail() {
    const modal = document.getElementById('stationDetailModal');
    modal.classList.add('hidden');
    document.body.style.overflow = '';

    // Clean up map
    if (detailMap) {
        detailMap.remove();
        detailMap = null;
        stationMarker = null;
    }
    currentStationData = null;
}

function initDetailMap(lat, lng, station) {
    const mapContainer = document.getElementById('stationDetailMap');
    if (!mapContainer) {
        console.error('Map container not found');
        return;
    }

    // Default to Berlin if no coordinates
    const centerLat = lat !== null ? lat : 52.5200;
    const centerLng = lng !== null ? lng : 13.4050;
    const hasCoords = lat !== null && lng !== null;

    console.log('Initializing map at:', centerLat, centerLng, 'Has coords:', hasCoords);

    // Initialize map
    detailMap = L.map('stationDetailMap', {
        zoomControl: false,
        attributionControl: true
    }).setView([centerLat, centerLng], hasCoords ? 15 : 5);

    // Dark theme tile layer - CartoDB Dark Matter
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(detailMap);

    // Add marker if coordinates exist
    if (hasCoords) {
        // Custom pulsing marker icon using CSS animation
        const pulsingIcon = L.divIcon({
            className: 'custom-pulsing-marker',
            html: `
                <div class="relative w-4 h-4">
                    <div class="absolute inset-0 bg-cyan-500 rounded-full animate-ping opacity-75"></div>
                    <div class="relative w-4 h-4 bg-cyan-500 border-2 border-white rounded-full shadow-lg shadow-cyan-500/50"></div>
                </div>
            `,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        });

        stationMarker = L.marker([lat, lng], { icon: pulsingIcon }).addTo(detailMap);

        // Popup with station info
        const popupContent = `
            <div class="p-3 min-w-[220px]">
                <h3 class="font-bold text-cyan-400 mb-1 text-base">${station.name || 'Station'}</h3>
                <p class="text-xs text-gray-400 mb-2">${station.location || ''}</p>
                <div class="flex items-center gap-2 text-xs mb-2">
                    <span class="px-2 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        <i class="fas fa-microchip mr-1"></i>${station.sensorCount || 0} sensors
                    </span>
                </div>
                <p class="text-[10px] text-gray-500 font-mono">UID: ${station.uid || station.id}</p>
            </div>
        `;

        stationMarker.bindPopup(popupContent, {
            closeButton: false,
            offset: [0, -10],
            className: 'custom-popup'
        }).openPopup();

        // Add accuracy circle
        L.circle([lat, lng], {
            color: '#00D9FF',
            fillColor: '#00D9FF',
            fillOpacity: 0.1,
            radius: 100,
            weight: 1
        }).addTo(detailMap);
    } else {
        // Show "no coordinates" message
        const noCoordsControl = L.control({position: 'center'});
        noCoordsControl.onAdd = function() {
            const div = L.DomUtil.create('div', 'bg-gray-800/95 text-white px-6 py-3 rounded-xl border border-amber-500/50 shadow-2xl backdrop-blur-sm');
            div.innerHTML = `
                <div class="flex items-center gap-3">
                    <i class="fas fa-exclamation-triangle text-amber-400 text-xl"></i>
                    <div>
                        <p class="font-semibold">No coordinates available</p>
                        <p class="text-xs text-gray-400">This station has no location data</p>
                    </div>
                </div>
            `;
            return div;
        };
        noCoordsControl.addTo(detailMap);
    }

    // Force map refresh after container resize
    setTimeout(() => {
        if (detailMap) detailMap.invalidateSize();
    }, 300);
}

// Map control functions
function mapZoomIn() {
    if (detailMap) detailMap.zoomIn();
}

function mapZoomOut() {
    if (detailMap) detailMap.zoomOut();
}

function centerMapOnStation() {
    if (detailMap && stationMarker) {
        const latLng = stationMarker.getLatLng();
        detailMap.flyTo(latLng, 17, {
            duration: 1.5,
            easeLinearity: 0.25
        });
        setTimeout(() => stationMarker.openPopup(), 1600);
    }
}

function openInGoogleMaps() {
    if (!currentStationData) return;

    let query;
    if (currentStationData.coordinates) {
        if (Array.isArray(currentStationData.coordinates)) {
            query = `${currentStationData.coordinates[0]},${currentStationData.coordinates[1]}`;
        } else {
            query = currentStationData.coordinates;
        }
    } else {
        query = currentStationData.location;
    }

    if (query) {
        window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`, '_blank');
    } else {
        showToast('No location data available', 'error');
    }
}

// Load sensors list - FIXED for your data structure
function loadStationSensors(station) {
    const container = document.getElementById('detailSensorsList');
    const sensors = station.sensors;

    console.log('Loading sensors:', sensors);

    // Handle case where sensors might be string (from bad template serialization)
    let sensorsArray = sensors;
    if (typeof sensors === 'string') {
        try {
            sensorsArray = JSON.parse(sensors);
        } catch (e) {
            console.error('Failed to parse sensors string:', e);
            container.innerHTML = `
                <div class="text-center text-red-400 py-6">
                    <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                    <p class="text-sm">Error loading sensors data</p>
                </div>
            `;
            return;
        }
    }

    if (!sensorsArray || !Array.isArray(sensorsArray) || sensorsArray.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i class="fas fa-microchip text-3xl mb-3 opacity-30"></i>
                <p class="text-sm">No sensors connected</p>
            </div>
        `;
        return;
    }

    let html = '';

    sensorsArray.forEach(sensor => {
        // Determine icon based on sensor type
        let icon = 'fa-microchip';
        const sensorType = (sensor.sensor_type && sensor.sensor_type.name) || '';
        const sensorId = sensor.sensor_id || sensor.id || 'Unknown';

        if (sensorType.includes('SDS') || sensorType.includes('PM')) icon = 'fa-smog';
        else if (sensorType.includes('DHT') || sensorType.includes('temp')) icon = 'fa-temperature-half';
        else if (sensorType.includes('BMP') || sensorType.includes('pressure')) icon = 'fa-gauge';
        else if (sensorType.includes('humidity')) icon = 'fa-droplet';

        // Build values HTML
        let valuesHtml = '';
        if (sensor.values && typeof sensor.values === 'object' && Object.keys(sensor.values).length > 0) {
            Object.entries(sensor.values).forEach(([key, data]) => {
                const value = typeof data === 'object' ? data.value : data;
                const timestamp = typeof data === 'object' ? data.timestamp : 'N/A';

                valuesHtml += `
                    <div class="flex items-center gap-2 mt-1">
                        <span class="text-xs text-cyan-400 font-medium">${key}:</span>
                        <span class="text-xs text-white">${value}</span>
                    </div>
                    ${timestamp !== 'N/A' ? `<p class="text-[10px] text-gray-500">Updated: ${timestamp}</p>` : ''}
                `;
            });
        } else {
            valuesHtml = `<p class="text-xs text-gray-500 mt-1">No recent data</p>`;
        }

        html += `
            <div class="sensor-row flex items-center justify-between p-3 rounded-xl bg-gray-800/40 border border-gray-700/30 hover:border-cyan-500/30 hover:bg-gray-800/60 transition-all group">
                <div class="flex items-center gap-3 flex-1 min-w-0">
                    <div class="w-10 h-10 rounded-lg bg-slate-700/50 flex items-center justify-center text-cyan-400 flex-shrink-0">
                        <i class="fas ${icon}"></i>
                    </div>
                    <div class="min-w-0 flex-1">
                        <h4 class="text-white font-semibold text-sm truncate">
                            ${sensorType} <span class="text-gray-400 font-normal">• ${sensorId}</span>
                        </h4>
                        ${valuesHtml}
                    </div>
                </div>

                <div class="flex items-center gap-2 ml-3">
                    <button onclick="openSensorDownloadModal(${station.id}, ${sensor.id || 0}, '${station.uid}')"
                            class="w-8 h-8 rounded-lg bg-slate-700/30 hover:bg-cyan-500/20 text-gray-400 hover:text-cyan-400 transition-colors flex items-center justify-center border border-white/5 hover:border-cyan-500/30"
                            title="Download sensor data">
                        <i class="fas fa-download text-xs"></i>
                    </button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Action functions
function copyCoordinates() {
    if (!currentStationData || !currentStationData.coordinates) {
        showToast('No coordinates to copy', 'error');
        return;
    }

    let coordString;
    if (Array.isArray(currentStationData.coordinates)) {
        coordString = `${currentStationData.coordinates[0]}, ${currentStationData.coordinates[1]}`;
    } else {
        coordString = currentStationData.coordinates;
    }

    navigator.clipboard.writeText(coordString).then(() => {
        showToast('Coordinates copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy coordinates', 'error');
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('stationDetailModal');
        if (modal && !modal.classList.contains('hidden')) {
            closeStationDetail();
        }
    }
});