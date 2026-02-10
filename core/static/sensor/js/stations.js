// Selection counter
function updateSelection() {
    const checked = document.querySelectorAll('.sensor-checkbox:checked');
    const counter = document.getElementById('selectedCounter');
    if (!counter) return;

    counter.textContent = checked.length;
    counter.classList.add('text-cyan-400');
    setTimeout(() => counter.classList.remove('text-cyan-400'), 200);
}

// Filter stations
function filterLocations(status) {
    document.querySelectorAll('.location-card').forEach(card => {
        card.style.display =
            status === 'all' || card.dataset.status === status
                ? 'flex'
                : 'none';
    });
}

// Search
document.addEventListener('DOMContentLoaded', () => {
    const search = document.getElementById('globalSearch');
    if (!search) return;

    search.addEventListener('input', e => {
        const term = e.target.value.toLowerCase();
        document.querySelectorAll('.location-card').forEach(card => {
            card.style.display = card.dataset.name.includes(term)
                ? 'flex'
                : 'none';
        });
    });
});