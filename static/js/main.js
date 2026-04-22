/* ─────────────────────────────────────────────────────────────────────────
   Vigilant — Client-side JavaScript
   Handles filter pills, notification dropdown, and micro-interactions.
   ───────────────────────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {

    // ── Filter pills ────────────────────────────────────────────────────
    const pills = document.querySelectorAll('.filter-pill');
    const rows  = document.querySelectorAll('.sub-row');

    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            // Update active state
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            const filter = pill.dataset.filter;

            rows.forEach(row => {
                if (filter === 'all' || row.dataset.status === filter) {
                    row.classList.remove('hidden-by-filter');
                } else {
                    row.classList.add('hidden-by-filter');
                }
            });
        });
    });


    // ── Notification dropdown ───────────────────────────────────────────
    const bell     = document.getElementById('notif-bell');
    const dropdown = document.getElementById('notif-dropdown');

    if (bell && dropdown) {
        bell.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && e.target !== bell) {
                dropdown.classList.add('hidden');
            }
        });
    }


    // ── Staggered animation on load ─────────────────────────────────────
    const animatedEls = document.querySelectorAll('.animate-slide-up');
    animatedEls.forEach((el, i) => {
        el.style.animationDelay = `${0.05 + i * 0.05}s`;
    });

});
