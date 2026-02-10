 function toggleSensorsList(button) {
            const card = button.closest('.location-card');
            const sensorsList = card.querySelector('.sensors-list-content');
            const toggleIcon = button.querySelector('.toggle-icon');
            const toggleText = button.querySelector('.toggle-text');

            // Use getComputedStyle to check actual height
            const computedHeight = window.getComputedStyle(sensorsList).maxHeight;

            if (computedHeight === '0px' || computedHeight === 'none' || !computedHeight) {
                // Expand
                sensorsList.style.maxHeight = sensorsList.scrollHeight + 'px';
                sensorsList.style.opacity = '1';
                toggleIcon.style.transform = 'rotate(180deg)';
                toggleText.textContent = 'Collapse';
            } else {
                // Collapse
                sensorsList.style.maxHeight = '0px';
                sensorsList.style.opacity = '0';
                toggleIcon.style.transform = 'rotate(0deg)';
                toggleText.textContent = 'Expand';
            }
        }