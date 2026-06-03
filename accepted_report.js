// app/static/js/accepted_report.js
// Дополнительные функции для отчёта «Принято за сутки»

// Функция для обновления графиков при изменении даты (AJAX)
function refreshCharts(date) {
    fetch(`/control/api/daily_stats?date=${date}`)
        .then(response => response.ok ? response.json() : Promise.reject())
        .then(data => {
            // Обновляем карточки статистики
            document.getElementById('totalQuantity').innerText = data.total_quantity;
            document.getElementById('totalFirstTime').innerText = data.total_first_time;
            document.getElementById('totalAfterFix').innerText = data.total_after_fix;
            
            // Обновляем проценты
            const total = data.total_quantity;
            const firstPercent = total > 0 ? (data.total_first_time / total * 100).toFixed(1) : 0;
            const afterPercent = total > 0 ? (data.total_after_fix / total * 100).toFixed(1) : 0;
            document.getElementById('firstPercent').innerText = firstPercent + '%';
            document.getElementById('afterPercent').innerText = afterPercent + '%';
            
            // Обновляем почасовой график
            if (window.hourlyChart) {
                window.hourlyChart.data.datasets[0].data = data.hourly_accepted;
                window.hourlyChart.update();
            }
            
            // Обновляем график по сменам
            if (window.shiftChart) {
                window.shiftChart.data.datasets[0].data = data.shift_values;
                window.shiftChart.update();
            }
            
            // Обновляем значения смен в текстовом виде
            document.getElementById('shift1Value').innerText = data.shift_values[0];
            document.getElementById('shift2Value').innerText = data.shift_values[1];
        })
        .catch(err => console.error('Ошибка загрузки данных:', err));
}

// Функция для печати только графика (отдельно)
function printChart(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    const win = window.open();
    win.document.write(`
        <html>
        <head>
            <title>Печать графика</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding: 20px; }
                img { max-width: 100%; height: auto; }
                @media print {
                    body { margin: 0; padding: 0; }
                }
            </style>
        </head>
        <body>
            <h3>График - ${document.querySelector('#hourlyChart')?.closest('.card')?.querySelector('.card-header')?.innerText || 'Динамика приёмки'}</h3>
            <img src="${canvas.toDataURL('image/png')}">
            <p>Дата: ${new Date().toLocaleDateString()}</p>
        </body>
        </html>
    `);
    win.document.close();
    win.print();
    win.close();
}

// Функция для экспорта графика в PNG
function exportChartAsPNG(chartId, filename) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    const link = document.createElement('a');
    link.download = filename || 'chart.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
}

// Экспорт таблицы в CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    for (const row of rows) {
        const cells = row.querySelectorAll('th, td');
        const rowData = [];
        for (const cell of cells) {
            let text = cell.innerText.trim();
            // Экранирование кавычек и запятых
            if (text.includes(',') || text.includes('"') || text.includes('\n')) {
                text = `"${text.replace(/"/g, '""')}"`;
            }
            rowData.push(text);
        }
        csv.push(rowData.join(','));
    }
    
    const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.setAttribute('download', filename || 'export.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Добавляем кнопки экспорта в интерфейс (если их нет)
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем кнопку экспорта графика (опционально)
    const hourlyChartCard = document.querySelector('#hourlyChart')?.closest('.card');
    if (hourlyChartCard && !hourlyChartCard.querySelector('.export-chart-btn')) {
        const btnGroup = hourlyChartCard.querySelector('.card-header');
        if (btnGroup) {
            const exportBtn = document.createElement('button');
            exportBtn.className = 'btn btn-sm btn-outline-light ms-2 export-chart-btn';
            exportBtn.innerHTML = '<i class="fas fa-download"></i> PNG';
            exportBtn.style.cssText = 'float: right; margin-top: -2px;';
            exportBtn.onclick = () => exportChartAsPNG('hourlyChart', `hourly_chart_${new Date().toISOString().slice(0,10)}.png`);
            btnGroup.appendChild(exportBtn);
        }
    }
    
    // Добавляем кнопку экспорта таблицы
    const tableCard = document.querySelector('.table-responsive')?.closest('.card');
    if (tableCard && !tableCard.querySelector('.export-table-btn')) {
        const header = tableCard.querySelector('.card-header');
        if (header) {
            const exportBtn = document.createElement('button');
            exportBtn.className = 'btn btn-sm btn-outline-secondary ms-2 export-table-btn';
            exportBtn.innerHTML = '<i class="fas fa-file-csv"></i> CSV';
            exportBtn.style.cssText = 'float: right; margin-top: -2px;';
            exportBtn.onclick = () => {
                const table = document.querySelector('.table');
                if (table) exportTableToCSV(table, `accepted_report_${new Date().toISOString().slice(0,10)}.csv`);
            };
            header.appendChild(exportBtn);
        }
    }
});