(function () {
    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }

    function getSavedTheme() {
        return localStorage.getItem('theme') || 'light';
    }

    function setTheme(theme) {
        localStorage.setItem('theme', theme);
        applyTheme(theme);
    }

    // APPLY ON EVERY PAGE LOAD
    applyTheme(getSavedTheme());

    document.addEventListener('DOMContentLoaded', () => {
        const checkbox = document.getElementById('theme-checkbox');
        const icon = document.getElementById('theme-icon');

        if (!checkbox) return;

        const currentTheme = getSavedTheme();

        checkbox.checked = currentTheme === 'dark';
        if (icon) icon.textContent = currentTheme === 'dark' ? '🌙' : '☀️';

        checkbox.addEventListener('change', () => {
            const newTheme = checkbox.checked ? 'dark' : 'light';
            setTheme(newTheme);

            if (icon) icon.textContent = newTheme === 'dark' ? '🌙' : '☀️';
        });
    });
})();