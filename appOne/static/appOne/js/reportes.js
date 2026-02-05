// ===== Gráfico Estados =====
new Chart(document.getElementById('estadoChart'), {
    type: 'doughnut',
    data: {
        labels: estadosLabels,
        datasets: [{
            data: estadosData
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { position: 'bottom' }
        }
    }
});

// ===== Gráfico por días =====
new Chart(document.getElementById('diasChart'), {
    type: 'line',
    data: {
        labels: diasLabels,
        datasets: [{
            label: 'Préstamos',
            data: diasData,
            tension: 0.3,
            fill: true
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { display: false }
        }
    }
});

// ===== Dispositivos más solicitados =====
new Chart(document.getElementById('dispositivosChart'), {
    type: 'bar',
    data: {
        labels: dispositivosLabels,
        datasets: [{
            label: 'Cantidad de préstamos',
            data: dispositivosData
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { display: false }
        }
    }
});
