function refreshData() {
    const csrfToken = document.getElementById("csrfToken").value;

    const btn = event.currentTarget;
    btn.disabled = true;

    fetch(REFRESH_URL, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "ok") {
            alert("✅ Sensor data refreshed!");
        } else {
            alert("⚠️ Failed to refresh sensor data");
        }
    })
    .catch(error => {
        console.error(error);
        alert("❌ Error refreshing sensor data");
    })
    .finally(() => {
        btn.disabled = false;
    });
}


function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    const isHidden = dropdown.classList.contains('hidden');

    if (isHidden) {
        dropdown.classList.remove('hidden');
        setTimeout(() => {
            dropdown.classList.add('opacity-100', 'scale-100');
            dropdown.classList.remove('opacity-0', 'scale-95');
        }, 10);
    } else {
        dropdown.classList.add('opacity-0', 'scale-95');
        dropdown.classList.remove('opacity-100', 'scale-100');
        setTimeout(() => {
            dropdown.classList.add('hidden');
        }, 200);
    }
}

document.addEventListener('click', function (event) {
    const container = document.getElementById('userMenuContainer');
    const dropdown = document.getElementById('userDropdown');

    if (container && !container.contains(event.target) && !dropdown.classList.contains('hidden')) {
        dropdown.classList.add('opacity-0', 'scale-95');
        dropdown.classList.remove('opacity-100', 'scale-100');
        setTimeout(() => {
            dropdown.classList.add('hidden');
        }, 200);
    }
});

// Prevent typing in the navbar search input
document.addEventListener('DOMContentLoaded', function() {
    const globalSearch = document.getElementById('globalSearch');

    if (globalSearch) {
        // Prevent all keyboard input
        globalSearch.addEventListener('keydown', function(e) {
            e.preventDefault();
            // Open modal on any keypress
            openSearchModal();
        });

        // Prevent paste
        globalSearch.addEventListener('paste', function(e) {
            e.preventDefault();
            openSearchModal();
        });

        // Clear any value that might get in
        globalSearch.addEventListener('input', function(e) {
            e.target.value = '';
            openSearchModal();
        });

        // Open on focus
        globalSearch.addEventListener('focus', function(e) {
            openSearchModal();
            e.target.blur(); // Remove focus immediately
        });
    }
});