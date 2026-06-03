// app/static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    loadDailyChart();
    loadDefectsChart();
});

// Принудительное обновление при возврате на страницу (например, после удаления актов)
window.addEventListener('pageshow', function() {
    loadDashboardData();
    loadDailyChart();
    loadDefectsChart();
});

function loadDashboardData() {
    const timestamp = Date.now();
    fetch('/api/quality_stats?_=' + timestamp)
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(data => {
            const acceptedFirst = data.accepted_first || 0;
            const acceptedAfterFix = data.accepted_after_fix || 0;
            const finalReject = data.final_reject || 0;
            const total = acceptedFirst + acceptedAfterFix + finalReject;
            const totalAccepted = acceptedFirst + acceptedAfterFix;
            const fttPercent = total > 0 ? (acceptedFirst / total * 100) : 0;
            const defectPercent = total > 0 ? (finalReject / total * 100) : 0;
            document.getElementById('stat_accepted').innerText = totalAccepted;
            document.getElementById('stat_ftt').innerText = fttPercent.toFixed(1) + '%';
            document.getElementById('stat_defect_percent').innerText = defectPercent.toFixed(1) + '%';
            const fttCard = document.getElementById('fttCard');
            if (fttCard) {
                fttCard.classList.remove('bg-danger', 'bg-warning', 'bg-success');
                fttCard.classList.add(getFttColorClass(fttPercent));
            }
        })
        .catch(e => console.warn('quality_stats error:', e));
    
    fetch('/api/operational_stats?_=' + timestamp)
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(data => {
            const acceptedFirst = data.accepted_first || 0;
            const total = data.total || (acceptedFirst + (data.accepted_after_fix||0) + (data.final_reject||0));
            const fttPercent = total > 0 ? (acceptedFirst / total * 100) : 0;
            document.getElementById('stat_oper_ftt').innerText = fttPercent.toFixed(1) + '%';
            const operCard = document.getElementById('operFttCard');
            if (operCard) {
                operCard.classList.remove('bg-danger', 'bg-warning', 'bg-success');
                operCard.classList.add(getFttColorClass(fttPercent));
            }
        })
        .catch(e => console.warn('operational_stats error:', e));
    
    fetch('/api/defect_stats_month?_=' + timestamp)
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(defects => {
            const container = document.getElementById('defectStatsTable');
            if (!container) return;
            if (!defects || defects.length === 0) {
                container.innerHTML = '<p class="text-muted">Нет дефектов за текущий месяц</p>';
                return;
            }
            let html = '<table class="table table-striped table-hover table-sm"><thead><tr><th>Дефект</th><th>Доля от всех дефектов, %</th></tr></thead><tbody>';
            defects.forEach(d => {
                html += `<tr><td>${escapeHtml(d.name)}</td><td>${d.percent}%</td></tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        })
        .catch(e => console.warn('defect_stats_month error:', e));
    
    fetch('/api/defect_rejects_month?_=' + timestamp)
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(rejects => {
            const container = document.getElementById('rejectTable');
            if (!container) return;
            if (!rejects || rejects.length === 0) {
                container.innerHTML = '<p class="text-muted">Нет бракованных изделий за текущий месяц</p>';
                return;
            }
            let html = '<table class="table table-striped table-hover table-sm"><thead><tr><th>Изделие</th><th>Количество</th><th>Причина</th></tr></thead><tbody>';
            rejects.forEach(r => {
                html += `<tr><td>${escapeHtml(r.product_article)}</td><td>${r.quantity}</td><td>${escapeHtml(r.notes || '—')}</td></tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        })
        .catch(e => console.warn('defect_rejects_month error:', e));
}

function loadDailyChart() {
    fetch('/api/daily_stats?_=' + Date.now())
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(data => {
            const ctx = document.getElementById('dailyChart')?.getContext('2d');
            if (!ctx) return;
            if (window.dailyChartInstance) window.dailyChartInstance.destroy();
            window.dailyChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates.map(d => d.slice(5)),
                    datasets: [
                        { label: 'Принято (шт)', data: data.accepted, borderColor: '#28a745', backgroundColor: 'rgba(40,167,69,0.1)', tension: 0.3, fill: true },
                        { label: 'Брак (шт)', data: data.reject, borderColor: '#dc3545', backgroundColor: 'rgba(220,53,69,0.1)', tension: 0.3, fill: true }
                    ]
                },
                options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true, title: { display: true, text: 'Количество (шт)' } } } }
            });
        })
        .catch(e => console.warn('daily_stats error:', e));
}

function loadDefectsChart() {
    fetch('/api/defects_distribution?_=' + Date.now())
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(data => {
            const ctx = document.getElementById('defectsChart')?.getContext('2d');
            if (!ctx) return;
            if (window.defectsChartInstance) window.defectsChartInstance.destroy();
            window.defectsChartInstance = new Chart(ctx, {
                type: 'pie',
                data: { labels: data.labels, datasets: [{ data: data.counts, backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40'], borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'right' } } }
            });
        })
        .catch(e => console.warn('defects_distribution error:', e));
}

function getFttColorClass(fttPercent) {
    if (fttPercent < 50) return 'bg-danger';
    if (fttPercent <= 70) return 'bg-warning';
    return 'bg-success';
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, m => m === '&' ? '&amp;' : (m === '<' ? '&lt;' : '&gt;'));
}