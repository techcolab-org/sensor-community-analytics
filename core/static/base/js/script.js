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

// Optional: Password Strength Indicator
// Add this to your change_password.html template if you want a strength meter

document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('id_new_password1');

    if (passwordInput) {
        // Create strength indicator
        const strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'mt-2 hidden';
        strengthIndicator.innerHTML = `
            <div class="flex items-center gap-2 mb-1">
                <span class="text-xs text-slate-400">Password Strength:</span>
                <span id="strength-text" class="text-xs font-medium"></span>
            </div>
            <div class="flex gap-1">
                <div class="h-1 flex-1 rounded-full bg-slate-800"></div>
                <div class="h-1 flex-1 rounded-full bg-slate-800"></div>
                <div class="h-1 flex-1 rounded-full bg-slate-800"></div>
                <div class="h-1 flex-1 rounded-full bg-slate-800"></div>
            </div>
        `;
        passwordInput.parentElement.appendChild(strengthIndicator);

        const bars = strengthIndicator.querySelectorAll('.h-1');
        const strengthText = strengthIndicator.querySelector('#strength-text');

        passwordInput.addEventListener('input', function() {
            const password = this.value;

            if (password.length === 0) {
                strengthIndicator.classList.add('hidden');
                return;
            }

            strengthIndicator.classList.remove('hidden');

            let strength = 0;

            // Length check
            if (password.length >= 8) strength++;
            if (password.length >= 12) strength++;

            // Character variety checks
            if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
            if (/\d/.test(password)) strength++;
            if (/[^a-zA-Z0-9]/.test(password)) strength++;

            // Cap at 4
            strength = Math.min(strength, 4);

            // Update bars
            bars.forEach((bar, index) => {
                if (index < strength) {
                    if (strength === 1) {
                        bar.style.backgroundColor = '#ef4444'; // red
                        strengthText.textContent = 'Weak';
                        strengthText.className = 'text-xs font-medium text-red-400';
                    } else if (strength === 2) {
                        bar.style.backgroundColor = '#f59e0b'; // orange
                        strengthText.textContent = 'Fair';
                        strengthText.className = 'text-xs font-medium text-orange-400';
                    } else if (strength === 3) {
                        bar.style.backgroundColor = '#eab308'; // yellow
                        strengthText.textContent = 'Good';
                        strengthText.className = 'text-xs font-medium text-yellow-400';
                    } else if (strength === 4) {
                        bar.style.backgroundColor = '#22c55e'; // green
                        strengthText.textContent = 'Strong';
                        strengthText.className = 'text-xs font-medium text-green-400';
                    }
                } else {
                    bar.style.backgroundColor = '#1e293b';
                }
            });
        });
    }

    // Password confirmation validation
    const confirmInput = document.getElementById('id_new_password2');

    if (confirmInput && passwordInput) {
        confirmInput.addEventListener('input', function() {
            if (this.value && this.value !== passwordInput.value) {
                this.classList.add('border-red-500/50');
                this.classList.remove('border-white/10');
            } else {
                this.classList.remove('border-red-500/50');
                this.classList.add('border-white/10');
            }
        });
    }
});