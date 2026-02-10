// Debounce utility function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Station form handling with debounce
const addStationForm = document.getElementById('addStationForm');
let stationIsSubmitting = false;

if (addStationForm) {
    const handleStationSubmit = debounce(function(form) {
        if (stationIsSubmitting) return;

        stationIsSubmitting = true;

        const submitBtn = document.getElementById('submitStationBtn');
        const btnIcon = document.getElementById('stationBtnIcon');
        const btnText = document.getElementById('stationBtnText');
        const spinner = document.getElementById('stationSpinner');

        // Disable button and show loading
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
        btnIcon.classList.add('hidden');
        btnText.textContent = 'Creating...';
        spinner.classList.remove('hidden');

        // Submit the form
        form.submit();
    }, 500);

    addStationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        handleStationSubmit(this);
    });
}

// Sensor form handling with debounce
const addSensorForm = document.getElementById('addSensorForm');
let sensorIsSubmitting = false;

if (addSensorForm) {
    const handleSensorSubmit = debounce(function(form) {
        if (sensorIsSubmitting) return;

        sensorIsSubmitting = true;

        const submitBtn = document.getElementById('submitSensorBtn');
        const btnIcon = document.getElementById('sensorBtnIcon');
        const btnText = document.getElementById('sensorBtnText');
        const spinner = document.getElementById('sensorSpinner');

        // Disable button and show loading
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
        btnIcon.classList.add('hidden');
        btnText.textContent = 'Adding...';
        spinner.classList.remove('hidden');

        // Submit the form
        form.submit();
    }, 500);

    addSensorForm.addEventListener('submit', function(e) {
        e.preventDefault();
        handleSensorSubmit(this);
    });
}

// Reset button states on page load
window.addEventListener('DOMContentLoaded', function() {
    resetStationButton();
    resetSensorButton();
});

function resetStationButton() {
    const submitBtn = document.getElementById('submitStationBtn');
    const btnIcon = document.getElementById('stationBtnIcon');
    const btnText = document.getElementById('stationBtnText');
    const spinner = document.getElementById('stationSpinner');

    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-75', 'cursor-not-allowed');
        btnIcon.classList.remove('hidden');
        btnText.textContent = 'Create Station';
        spinner.classList.add('hidden');
        stationIsSubmitting = false;
    }
}

function resetSensorButton() {
    const submitBtn = document.getElementById('submitSensorBtn');
    const btnIcon = document.getElementById('sensorBtnIcon');
    const btnText = document.getElementById('sensorBtnText');
    const spinner = document.getElementById('sensorSpinner');

    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-75', 'cursor-not-allowed');
        btnIcon.classList.remove('hidden');
        btnText.textContent = 'Add Sensor';
        spinner.classList.add('hidden');
        sensorIsSubmitting = false;
    }
}

// Reset forms when modals are closed
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('hidden');

    if (modalId === 'addStationModal') {
        resetStationButton();
        document.getElementById('addStationForm').reset();
    }

    if (modalId === 'addSensorModal') {
        resetSensorButton();
        document.getElementById('addSensorForm').reset();
    }
}

// Open Station Modal
function openStationModal() {
    const modal = document.getElementById('addStationModal');
    const modalContent = document.getElementById('stationModalContent');

    modal.classList.remove('hidden');

    // Trigger animation
    setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }, 10);

    resetStationButton();
}

// Open Sensor Modal
function openSensorModal(stationId, stationName) {
    const modal = document.getElementById('addSensorModal');
    const modalContent = document.getElementById('sensorModalContent');
    const subtitle = document.getElementById('sensorModalSubtitle');
    const stationInput = document.getElementById('sensorStationId');

    // Set the station ID in the hidden input
    stationInput.value = stationId;

    // Update subtitle with station name
    subtitle.textContent = `Configure sensor for ${stationName}`;

    modal.classList.remove('hidden');

    // Trigger animation
    setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }, 10);

    resetSensorButton();
}