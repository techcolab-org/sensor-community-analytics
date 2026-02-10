/**
 * Station Data Download JavaScript
 * Handles download button clicks and communicates with Django backend
 *
 * Add this to: static/sensor/js/download_station_data.js
 */

// Configuration
const DOWNLOAD_CONFIG = {
    defaultStartDate: '2024-01-01',
    defaultEndDate: new Date().toISOString().split('T')[0],
    merge: true,
    mergeByYear: true
};

// Global download state
let isDownloadInProgress = false;

/**
 * Disable all download buttons in the application
 */
function disableAllDownloadButtons() {
    isDownloadInProgress = true;

    // Show download progress overlay
    showDownloadProgressOverlay();

    // Get all download buttons
    const downloadButtons = document.querySelectorAll('[onclick*="downloadLocation"], [onclick*="downloadSensor"]');

    downloadButtons.forEach(button => {
        button.disabled = true;
        button.dataset.originalOpacity = button.style.opacity || '1';
        button.style.opacity = '0.5';
        button.style.cursor = 'not-allowed';

        // Store original content if not already stored
        if (!button.dataset.originalButtonContent) {
            button.dataset.originalButtonContent = button.innerHTML;
        }

        // Add downloading indicator
        const icon = button.querySelector('i.fa-download');
        if (icon) {
            icon.classList.remove('fa-download');
            icon.classList.add('fa-spinner', 'fa-spin');
        }
    });

    // Also disable the modal submit buttons
    const modalButtons = document.querySelectorAll('#downloadConfigForm button[type="submit"], #startSensorDownloadBtn');
    modalButtons.forEach(button => {
        button.disabled = true;
        button.style.opacity = '0.5';
        button.style.cursor = 'not-allowed';
    });
}

/**
 * Enable all download buttons in the application
 */
function enableAllDownloadButtons() {
    isDownloadInProgress = false;

    // Hide download progress overlay
    hideDownloadProgressOverlay();

    // Get all download buttons
    const downloadButtons = document.querySelectorAll('[onclick*="downloadLocation"], [onclick*="downloadSensor"]');

    downloadButtons.forEach(button => {
        button.disabled = false;
        button.style.opacity = button.dataset.originalOpacity || '1';
        button.style.cursor = 'pointer';

        // Restore original content
        if (button.dataset.originalButtonContent) {
            button.innerHTML = button.dataset.originalButtonContent;
        }

        // Restore download icon
        const icon = button.querySelector('i.fa-spinner');
        if (icon) {
            icon.classList.remove('fa-spinner', 'fa-spin');
            icon.classList.add('fa-download');
        }
    });

    // Re-enable modal submit buttons
    const modalButtons = document.querySelectorAll('#downloadConfigForm button[type="submit"], #startSensorDownloadBtn');
    modalButtons.forEach(button => {
        button.disabled = false;
        button.style.opacity = '1';
        button.style.cursor = 'pointer';
    });
}

/**
 * Show download progress overlay
 */
function showDownloadProgressOverlay() {
    // Check if overlay already exists
    let overlay = document.getElementById('downloadProgressOverlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'downloadProgressOverlay';
        overlay.className = 'fixed top-4 right-4 z-[70] pointer-events-none';
        overlay.innerHTML = `
            <div class="glass-panel px-6 py-4 rounded-xl border border-cyan-500/30 shadow-2xl flex items-center gap-3 min-w-[280px] bg-cyan-500/10 animate-pulse-slow">
                <div class="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400">
                    <i class="fas fa-spinner fa-spin text-xl"></i>
                </div>
                <div class="flex-1">
                    <p class="text-sm font-semibold text-white">Download in Progress</p>
                    <p class="text-xs text-gray-400 mt-0.5">Please wait...</p>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    // Animate in
    setTimeout(() => {
        overlay.style.opacity = '1';
        overlay.style.transform = 'translateY(0)';
    }, 10);
}

/**
 * Hide download progress overlay
 */
function hideDownloadProgressOverlay() {
    const overlay = document.getElementById('downloadProgressOverlay');
    if (overlay) {
        overlay.style.opacity = '0';
        overlay.style.transform = 'translateY(-20px)';

        setTimeout(() => {
            overlay.remove();
        }, 300);
    }
}

/**
 * Get CSRF token for Django POST requests
 */
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

/**
 * Show loading state on button
 */
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalContent = button.innerHTML;
        button.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            Downloading...
        `;
    } else {
        button.disabled = false;
        if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
        }
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `toast-message pointer-events-auto transform transition-all duration-300 ease-out translate-x-full opacity-0`;
    toast.setAttribute('data-type', type);

    const bgClass = {
        'success': 'bg-emerald-500/10 border-emerald-500/30',
        'error': 'bg-red-500/10 border-red-500/30',
        'warning': 'bg-amber-500/10 border-amber-500/30',
        'info': 'bg-cyan-500/10 border-cyan-500/30'
    }[type] || 'bg-cyan-500/10 border-cyan-500/30';

    const iconBgClass = {
        'success': 'bg-emerald-500/20 text-emerald-400',
        'error': 'bg-red-500/20 text-red-400',
        'warning': 'bg-amber-500/20 text-amber-400',
        'info': 'bg-cyan-500/20 text-cyan-400'
    }[type] || 'bg-cyan-500/20 text-cyan-400';

    const icon = {
        'success': 'fa-check',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    }[type] || 'fa-info-circle';

    toast.innerHTML = `
        <div class="glass-panel px-5 py-4 rounded-xl border border-white/10 shadow-2xl flex items-center gap-3 min-w-[300px] max-w-md ${bgClass}">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${iconBgClass}">
                <i class="fas ${icon}"></i>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-white">${message}</p>
            </div>
            <button onclick="dismissToast(this)" class="w-6 h-6 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors flex items-center justify-center flex-shrink-0">
                <i class="fas fa-times text-xs"></i>
            </button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
    }, 10);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        dismissToast(toast.querySelector('button'));
    }, 5000);
}

/**
 * Dismiss toast notification
 */
function dismissToast(button) {
    const toast = button.closest('.toast-message');
    if (toast) {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

/**
 * Get all selected station IDs
 */
function getSelectedStationIds() {
    const checkboxes = document.querySelectorAll('.station-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.dataset.id));
}

/**
 * Get selected sensors within a location card
 */
function getSelectedSensorsInCard(card) {
    const checkboxes = card.querySelectorAll('.sensor-checkbox:checked');
    const sensors = Array.from(checkboxes).map(cb => {
        const sensorId = cb.dataset.sensorId || cb.getAttribute('data-sensor-id');
        const stationId = cb.dataset.stationId || cb.getAttribute('data-station-id');

        return {
            sensor_id: sensorId ? parseInt(sensorId) : null,
            station_id: stationId ? parseInt(stationId) : null
        };
    }).filter(s => s.sensor_id !== null && !isNaN(s.sensor_id)); // Filter out invalid IDs

    console.log('Selected sensors in card:', sensors); // Debug log
    return sensors;
}

// Initialize end dates to yesterday (today - 1 day) when page loads
document.addEventListener('DOMContentLoaded', function () {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayString = yesterday.toISOString().split('T')[0];

    // Set end date for Download Station modal
    const downloadEndDate = document.getElementById('downloadEndDate');
    if (downloadEndDate) {
        downloadEndDate.value = yesterdayString;
        downloadEndDate.max = yesterdayString; // Prevent selecting dates after yesterday
    }

    // Set end date for Download Sensor modal
    const downloadSensorEndDate = document.getElementById('downloadSensorEndDate');
    if (downloadSensorEndDate) {
        downloadSensorEndDate.value = yesterdayString;
        downloadSensorEndDate.max = yesterdayString; // Prevent selecting dates after yesterday
    }
});

// Helper function to format date as YYYY-MM-DD
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

/**
 * Set date preset ranges for Station modal
 */
function setDatePreset(preset) {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const startDateInput = document.getElementById('downloadStartDate');
    const endDateInput = document.getElementById('downloadEndDate');

    switch (preset) {
        case 'today':
            startDateInput.value = formatDate(yesterday);
            endDateInput.value = formatDate(yesterday);
            break;
        case 'last7days':
            const sevenDaysAgo = new Date(today);
            sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
            startDateInput.value = formatDate(sevenDaysAgo);
            endDateInput.value = formatDate(yesterday);
            break;
        case 'last30days':
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            startDateInput.value = formatDate(thirtyDaysAgo);
            endDateInput.value = formatDate(yesterday);
            break;
        case 'lastyear':
            const oneYearAgo = new Date(today);
            oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
            startDateInput.value = formatDate(oneYearAgo);
            endDateInput.value = formatDate(yesterday);
            break;
    }
}

/**
 * Open download configuration modal
 */
function openDownloadModal(stationIds, stationName, isDownloadAll, selectedSensors = []) {
    // Store station IDs for later use
    window.downloadStationIds = stationIds;
    window.downloadSelectedSensors = selectedSensors;

    // Update subtitle
    const subtitle = document.getElementById('downloadModalSubtitle');
    if (subtitle) {
        if (selectedSensors.length > 0) {
            subtitle.textContent = `Configure download settings for ${selectedSensors.length} selected sensor(s)`;
        } else if (stationIds.length === 1) {
            subtitle.textContent = `Configure download settings for all sensors in this station`;
        } else {
            subtitle.textContent = `Configure download settings for ${stationIds.length} station(s)`;
        }
    }

    // Set default end date to yesterday if not set
    const endDateInput = document.getElementById('downloadEndDate');
    if (endDateInput && !endDateInput.value) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        endDateInput.value = formatDate(yesterday);
    }

    // Show the modal
    const modal = document.getElementById('downloadConfigModal');
    const content = document.getElementById('downloadModalContent');

    // Update sensor info in the info box
    const stationInfoElem = document.getElementById('stationInfo');
    if (isDownloadAll) {
        stationInfoElem.style.display = 'none';
    } else {
        stationInfoElem.style.display = 'block';
    }

    const stationNameElem = document.getElementById('stationInfoStationName');
    const pathStationName = document.getElementById('stationPathStationName');

    if (stationNameElem) stationNameElem.textContent = stationName;
    if (pathStationName) pathStationName.textContent = stationName.toLowerCase()
        .replace(/[(),]/g, '_')   // replace (, ) and ,
        .replace(/\s+/g, '_')     // replace spaces
        .replace(/_+/g, '_')      // remove multiple underscores
        .replace(/-+/g, '_')      // replace hyphens with underscores
        .replace(/^_|_$/g, '');   // trim underscores from start/end

    if (!modal || !content) {
        console.error('Download modal not found in DOM');
        showToast('Error: Modal not found', 'error');
        return;
    }

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    modal.classList.remove('hidden');

    // Animate in
    setTimeout(() => {
        content.classList.remove('scale-95', 'opacity-0');
        content.classList.add('scale-100', 'opacity-100');
    }, 10);
}

/**
 * Close download configuration modal
 */
function closeDownloadModal() {
    const modal = document.getElementById('downloadConfigModal');
    const content = document.getElementById('downloadModalContent');

    if (!modal || !content) return;

    content.classList.remove('scale-100', 'opacity-100');
    content.classList.add('scale-95', 'opacity-0');

    setTimeout(() => {
        modal.classList.add('hidden');
        // Re-enable body scroll
        document.body.style.overflow = '';
    }, 200);
}

/**
 * Execute the station download with given configuration
 */
async function executeDownload(config) {
    // Disable all download buttons
    disableAllDownloadButtons();

    showToast('Starting download...', 'info');

    try {
        const response = await fetch(STATION_DOWNLOAD_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');

            if (data.station_path) {
                document.getElementById('viewStationBtn').classList.remove('hidden');
            }

            // Show detailed results if available
            if (data.summary) {
                console.log('Download Summary:', data.summary);
                console.log('Detailed Results:', data.results);
            }
        } else {
            showToast(data.error || 'Download failed', 'error');
        }

    } catch (error) {
        console.error('Download error:', error);
        showToast('Network error during download', 'error');
    } finally {
        // Re-enable all download buttons
        enableAllDownloadButtons();
    }
}

/**
 * Handle station download form submission
 */
async function handleStationDownloadSubmit(event) {
    // Prevent default form submission if this is called from a form
    if (event) {
        event.preventDefault();
    }

    // Get the stored station IDs
    const stationIds = window.downloadStationIds;
    const selectedSensors = window.downloadSelectedSensors || [];

    if (!stationIds || stationIds.length === 0) {
        showToast('Error: No stations selected', 'error');
        return;
    }

    // Get form values
    const startDate = document.getElementById('downloadStartDate')?.value;
    const endDate = document.getElementById('downloadEndDate')?.value;
    const merge = document.getElementById('downloadMerge')?.checked ?? true;
    const mergeByYear = document.getElementById('downloadMergeByYear')?.checked ?? true;

    // Validate dates
    if (!startDate || !endDate) {
        showToast('Please select both start and end dates', 'error');
        return;
    }

    if (new Date(startDate) > new Date(endDate)) {
        showToast('Start date must be before end date', 'error');
        return;
    }

    // Extract and filter sensor IDs
    const sensorIds = selectedSensors
        .map(s => s.sensor_id)
        .filter(id => id !== null && id !== undefined && !isNaN(id));

    console.log('Filtered sensor IDs (empty = download all):', sensorIds);

    // Build configuration object
    // If sensorIds is empty, send null to indicate "download all sensors"
    const config = {
        station_ids: stationIds,
        sensor_ids: sensorIds.length > 0 ? sensorIds : null, // null = download all
        start_date: startDate,
        end_date: endDate,
        merge: merge,
        merge_by_year: mergeByYear
    };

    console.log('Submitting download config:', config);

    // Close modal
    closeDownloadModal();

    // Execute download
    await executeDownload(config);
}

// Add event listener when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Handle form submission for station download
    const downloadForm = document.getElementById('downloadConfigForm');
    if (downloadForm) {
        downloadForm.addEventListener('submit', handleStationDownloadSubmit);
    }
});

/**
 * Download data for selected stations (called from template)
 */
function downloadLocation(button, stationName, isDownloadAll) {
    // Check if download is already in progress
    if (isDownloadInProgress) {
        showToast('A download is already in progress. Please wait...', 'warning');
        return;
    }

    // Check if button is inside a location card (single station)
    const card = button.closest('.location-card');

    let stationIds = [];
    let selectedSensors = []; // Track selected sensors

    if (card) {
        // Single station download
        const stationId = parseInt(card.dataset.stationId);
        stationIds = [stationId];

        // Get selected sensors in this card
        selectedSensors = getSelectedSensorsInCard(card);

        console.log('Station ID:', stationId);
        console.log('Selected sensors:', selectedSensors);

        // REMOVED: No longer checking if sensors are selected
        // If no sensors selected, it will download all sensors for the station

    } else {
        // Multiple stations download (from top button)
        stationIds = getSelectedStationIds();

        if (stationIds.length === 0) {
            showToast('Please select at least one station', 'warning');
            return;
        }
    }

    console.log('Opening download modal for stations:', stationIds);
    console.log('Selected sensors (empty = download all):', selectedSensors);

    // Open configuration modal
    openDownloadModal(stationIds, stationName, isDownloadAll, selectedSensors);
}

/**
 * ============================================================================
 * SENSOR DOWNLOAD FUNCTIONS
 * ============================================================================
 */

/**
 * Set date preset ranges for sensor download
 */
function setSensorDatePreset(preset) {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const startDateInput = document.getElementById('downloadSensorStartDate');
    const endDateInput = document.getElementById('downloadSensorEndDate');

    switch (preset) {
        case 'today':
            startDateInput.value = formatDate(yesterday);
            endDateInput.value = formatDate(yesterday);
            break;
        case 'last7days':
            const sevenDaysAgo = new Date(today);
            sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
            startDateInput.value = formatDate(sevenDaysAgo);
            endDateInput.value = formatDate(yesterday);
            break;
        case 'last30days':
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            startDateInput.value = formatDate(thirtyDaysAgo);
            endDateInput.value = formatDate(yesterday);
            break;
        case 'lastyear':
            const oneYearAgo = new Date(today);
            oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
            startDateInput.value = formatDate(oneYearAgo);
            endDateInput.value = formatDate(yesterday);
            break;
        case 'all':
            startDateInput.value = '2024-01-01'; // Or your earliest data date
            endDateInput.value = formatDate(yesterday);
            break;
    }
}

/**
 * Open sensor download configuration modal
 */
function openSensorDownloadModal(sensorId, stationId, stationName) {
    // Store sensor and station info
    window.downloadSensorData = {
        sensorId: sensorId,
        stationId: stationId,
        stationName: stationName
    };

    // Update modal subtitle and info
    const subtitle = document.getElementById('downloadSensorModalSubtitle');
    if (subtitle) {
        subtitle.textContent = `Download data for sensor ${sensorId}`;
    }

    // Update sensor info in the info box
    const stationNameElem = document.getElementById('sensorInfoStationName');
    const sensorIdElem = document.getElementById('sensorInfoSensorId');
    const pathStationName = document.getElementById('sensorPathStationName');
    const pathSensorId = document.getElementById('sensorPathSensorId');

    if (stationNameElem) stationNameElem.textContent = stationName;
    if (sensorIdElem) sensorIdElem.textContent = sensorId;
    if (pathStationName) pathStationName.textContent = stationName.toLowerCase()
        .replace(/[(),]/g, '_')   // replace (, ) and ,
        .replace(/\s+/g, '_')     // replace spaces
        .replace(/_+/g, '_')      // remove multiple underscores
        .replace(/-+/g, '_')      // replace hyphens with underscores
        .replace(/^_|_$/g, '');   // trim underscores from start/end
    if (pathSensorId) pathSensorId.textContent = sensorId;



    // Set default end date to yesterday if not set
    const endDateInput = document.getElementById('downloadSensorEndDate');
    if (endDateInput && !endDateInput.value) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        endDateInput.value = formatDate(yesterday);
    }

    // Show the modal
    const modal = document.getElementById('downloadSensorModal');
    const content = document.getElementById('downloadSensorModalContent');

    if (!modal || !content) {
        console.error('Sensor download modal not found in DOM');
        showToast('Error: Modal not found', 'error');
        return;
    }

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    modal.classList.remove('hidden');

    // Animate in
    setTimeout(() => {
        content.classList.remove('scale-95', 'opacity-0');
        content.classList.add('scale-100', 'opacity-100');
    }, 10);
}

/**
 * Close sensor download configuration modal
 */
function closeSensorDownloadModal() {
    const modal = document.getElementById('downloadSensorModal');
    const content = document.getElementById('downloadSensorModalContent');

    if (!modal || !content) return;

    content.classList.remove('scale-100', 'opacity-100');
    content.classList.add('scale-95', 'opacity-0');

    setTimeout(() => {
        modal.classList.add('hidden');
        // Re-enable body scroll
        document.body.style.overflow = '';
    }, 200);
}

/**
 * Execute sensor download with given configuration
 */
async function executeSensorDownload(config) {
    // Disable all download buttons
    disableAllDownloadButtons();

    showToast('Starting sensor download...', 'info');

    try {
        const response = await fetch(SENSOR_DOWNLOAD_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');

            if (data.station_path) {
                document.getElementById('viewStationBtn').classList.remove('hidden');
            }

            // Show detailed results if available
            if (data.summary) {
                console.log('Download Summary:', data.summary);
                console.log('Detailed Results:', data.results);
            }
        } else {
            showToast(data.error || 'Download failed', 'error');
        }

    } catch (error) {
        console.error('Sensor download error:', error);
        showToast('Network error during download', 'error');
    } finally {
        // Re-enable all download buttons
        enableAllDownloadButtons();
    }
}

/**
 * Handle sensor download form submission
 */
async function handleSensorDownloadSubmit(event) {
    // Prevent default if this is from form submission
    if (event) {
        event.preventDefault();
    }

    // Get the stored sensor/station info
    const downloadData = window.downloadSensorData;
    if (!downloadData) {
        showToast('Error: Sensor information not found', 'error');
        return;
    }

    // Get form values
    const startDate = document.getElementById('downloadSensorStartDate')?.value;
    const endDate = document.getElementById('downloadSensorEndDate')?.value;
    const merge = document.getElementById('downloadSensorMerge')?.checked ?? true;
    const mergeByYear = document.getElementById('downloadSensorMergeByYear')?.checked ?? true;

    // Validate dates
    if (!startDate || !endDate) {
        showToast('Please select both start and end dates', 'error');
        return;
    }

    if (new Date(startDate) > new Date(endDate)) {
        showToast('Start date must be before end date', 'error');
        return;
    }

    // Build configuration object
    const config = {
        sensor_id: downloadData.sensorId,
        station_id: downloadData.stationId,
        start_date: startDate,
        end_date: endDate,
        merge: merge,
        merge_by_year: mergeByYear
    };

    console.log('Submitting sensor download config:', config);

    // Close modal
    closeSensorDownloadModal();

    // Execute download
    await executeSensorDownload(config);
}

// Add event listener when DOM is ready for sensor download
document.addEventListener('DOMContentLoaded', function () {
    const sensorDownloadButton = document.getElementById('startSensorDownloadBtn');
    if (sensorDownloadButton) {
        sensorDownloadButton.addEventListener('click', handleSensorDownloadSubmit);
    }

    // Also handle form submission
    const sensorDownloadForm = document.getElementById('downloadSensorConfigForm');
    if (sensorDownloadForm) {
        sensorDownloadForm.addEventListener('submit', handleSensorDownloadSubmit);
    }
});

/**
 * Download specific sensor data (called from template)
 * This is the function called by the button: onclick="downloadSensor(this, stationId, sensorId, stationUid)"
 */
function downloadSensor(button, stationId, sensorId, stationUid) {
    // Check if download is already in progress
    if (isDownloadInProgress) {
        showToast('A download is already in progress. Please wait...', 'warning');
        return;
    }

    // Get station name from the card
    let stationName = 'Unknown Station';

    const stationNameElem = document.getElementById(`station-${stationUid}`);
    if (stationNameElem) {
        stationName = stationNameElem.dataset.name;
    }

    console.log('Opening sensor download modal:', {stationId, sensorId, stationName});

    // Open the sensor download modal
    openSensorDownloadModal(sensorId, stationId, stationName);
}

/**
 * Update station selection state
 */
function updateStationSelection() {
    const selectedCount = getSelectedStationIds().length;
    const selectAllBtn = document.querySelector('[onclick="selectAllStations(this)"]');

    if (selectAllBtn && selectedCount > 0) {
        selectAllBtn.textContent = `Selected (${selectedCount})`;
        selectAllBtn.classList.add('bg-cyan-600', 'text-white');
    } else if (selectAllBtn) {
        selectAllBtn.textContent = 'Select All';
        selectAllBtn.classList.remove('bg-cyan-600', 'text-white');
    }
}

/**
 * Select all stations
 */
function selectAllStations(button) {
    const checkboxes = document.querySelectorAll('.station-checkbox');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);

    checkboxes.forEach(cb => {
        cb.checked = !allChecked;
    });

    updateStationSelection();
}

/**
 * Select all sensors in a location card
 */
function selectAllInLocation(button) {
    const card = button.closest('.location-card');
    const checkboxes = card.querySelectorAll('.sensor-checkbox');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);

    checkboxes.forEach(cb => {
        cb.checked = !allChecked;
    });

    button.textContent = allChecked ? 'Select All' : 'Deselect All';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    // Add change listeners to all station checkboxes
    document.querySelectorAll('.station-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateStationSelection);
    });

    // Close modals on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeDownloadModal();
            closeSensorDownloadModal();
        }
    });
});