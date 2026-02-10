// Debug: Check if data exists
console.log('🔍 Search script loaded');
console.log('stationsData available?', typeof stationsData !== 'undefined');
if (typeof stationsData !== 'undefined') {
    console.log('Stations count:', stationsData.length);
}

// Open modal
function openSearchModal() {
    console.log('Opening search modal...');
    const modal = document.getElementById('searchModal');
    const searchInput = document.getElementById('searchInput');

    if (!modal) {
        console.error('❌ searchModal not found!');
        return;
    }
    if (!searchInput) {
        console.error('❌ searchInput not found!');
        return;
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');

    // Small delay to ensure modal is visible before focusing
    setTimeout(() => {
        searchInput.focus();
        console.log('✅ Search input focused');
    }, 50);

    // Show all stations initially (or placeholder)
    performSearch('');
}

// Close modal
function closeSearchModal() {
    const modal = document.getElementById('searchModal');
    const searchInput = document.getElementById('searchInput');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    if (searchInput) {
        searchInput.value = '';
    }
}

// Search function - FIXED
function performSearch(query) {
    console.log('Searching for:', query);

    const resultsContainer = document.getElementById('searchResults');
    const noResults = document.getElementById('noResults');

    if (!resultsContainer) {
        console.error('❌ searchResults container not found!');
        return;
    }

    if (typeof stationsData === 'undefined' || !Array.isArray(stationsData)) {
        console.error('❌ stationsData is not available!');
        resultsContainer.innerHTML = '<div class="p-4 text-red-400">Error: Station data not loaded</div>';
        return;
    }

    query = query.toLowerCase().trim();

    // Filter stations
    const filtered = stationsData.filter(station => {
        if (!station) return false;
        const name = (station.name || '').toLowerCase();
        const location = (station.location || '').toLowerCase();

        return name.includes(query) || location.includes(query);
    });

    console.log('Filtered results:', filtered.length);

    // Handle no results
    if (filtered.length === 0) {
        resultsContainer.innerHTML = '';
        if (noResults) noResults.classList.remove('hidden');
        return;
    }

    if (noResults) noResults.classList.add('hidden');

    // Build results HTML - FIXED: Always show results, not placeholder
    let html = '<div class="p-2">';

    // In performSearch(), replace the result item HTML:
    filtered.forEach((station) => {
        if (!station) return;

        html += `
        <div onclick="openStationDetail(${station.id})" 
             class="cursor-pointer block p-4 mb-2 rounded-lg hover:bg-gray-800/50 transition-all group border border-transparent hover:border-cyan-500/20 bg-gray-900/20 hover:shadow-lg hover:shadow-cyan-500/10">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center border border-cyan-500/30 group-hover:border-cyan-500/50 transition-all group-hover:scale-110">
                            <i class="fas fa-map-marker-alt text-cyan-400"></i>
                        </div>
                        <div>
                            <h3 class="text-white font-medium group-hover:text-cyan-400 transition-colors">
                                ${highlightMatch(station.name || 'Unnamed', query)}
                            </h3>
                            <p class="text-sm text-gray-400">
                                <i class="fas fa-location-dot text-xs mr-1"></i>
                                ${highlightMatch(station.location || 'Unknown', query)}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="text-right ml-4">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 group-hover:bg-cyan-500/20 transition-all">
                        <i class="fas fa-broadcast-tower text-xs mr-1"></i>
                        ${station.sensorCount || 0}
                    </span>
                </div>
            </div>
            <div class="mt-2 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                <span class="text-xs text-cyan-400 flex items-center gap-1">
                    <i class="fas fa-expand"></i>
                    Click for full details
                </span>
                <i class="fas fa-chevron-right text-gray-600 group-hover:text-cyan-400 transition-colors"></i>
            </div>
        </div>
    `;
    });

    html += '</div>';
    resultsContainer.innerHTML = html;
    console.log('✅ Results HTML updated');
}

// Highlight matching text
function highlightMatch(text, query) {
    if (!query || !text) return text;
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<span class="bg-cyan-500/30 text-cyan-300 px-1 rounded">$1</span>');
}

// Escape special regex characters
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Event listeners - CRITICAL FIX HERE
document.addEventListener('DOMContentLoaded', function () {
    console.log('🔥 DOM loaded, setting up search...');

    // Global search input in navbar
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        console.log('✅ Found globalSearch input');

        globalSearch.addEventListener('click', function (e) {
            console.log('Global search clicked');
            e.preventDefault();
            openSearchModal();
        });

        globalSearch.addEventListener('focus', function (e) {
            console.log('Global search focused');
            e.preventDefault();
            openSearchModal();
            this.blur();
        });
    } else {
        console.error('❌ globalSearch input not found!');
    }

    // CRITICAL FIX: Use event delegation for search input
    // The modal might be loaded dynamically, so we attach to document
    document.addEventListener('input', function (e) {
        if (e.target && e.target.id === 'searchInput') {
            console.log('Input event fired, value:', e.target.value);
            performSearch(e.target.value);
        }
    });

    // Also try direct attachment if element exists now
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        console.log('✅ Found searchInput, attaching listener directly');
        searchInput.addEventListener('input', (e) => {
            console.log('Direct input event:', e.target.value);
            performSearch(e.target.value);
        });
        // Handle keyup as backup
        searchInput.addEventListener('keyup', (e) => {
            console.log('Keyup event:', e.target.value);
            performSearch(e.target.value);
        });
    } else {
        console.log('⚠️ searchInput not found yet (might be in modal)');
    }

    // Click outside to close
    const modal = document.getElementById('searchModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeSearchModal();
            }
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openSearchModal();
        }
        if (e.key === 'Escape') {
            closeSearchModal();
        }
    });
});