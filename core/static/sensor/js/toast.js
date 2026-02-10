function dismissToast(button) {
    const toast = button.closest('.toast-message');
    if (!toast) return;

    toast.classList.add('opacity-0', 'translate-x-full');
    setTimeout(() => toast.remove(), 300);
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.toast-message').forEach((toast, i) => {
        setTimeout(() => {
            toast.classList.remove('opacity-0', 'translate-x-full');
        }, i * 100);

        setTimeout(() => {
            if (toast.parentElement) dismissToast({ closest: () => toast });
        }, 5000 + i * 100);
    });
});
