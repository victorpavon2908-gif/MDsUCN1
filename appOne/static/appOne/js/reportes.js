document.addEventListener('DOMContentLoaded', () => {
    // Paleta de colores corporativos (Sin Cambios)
    const colors = {
        primary: '#019446',
        secondary: '#0d9488',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#0284c7',
        purple: '#9333ea',
        grayBg: '#f8fafc'
    };

    // Configuración global avanzada de Chart.js
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.color = '#64748b';
    Chart.defaults.plugins.tooltip.backgroundColor = '#0f172a';
    Chart.defaults.plugins.tooltip.titleFont = { size: 13, weight: '600' };
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;

    // --- 1. Gráfico de Estados (Dona / Donut) ---
    const ctxEstado = document.getElementById('estadoChart');
    if (ctxEstado) {
        new Chart(ctxEstado, {
            type: 'doughnut',
            data: {
                labels: estadosLabels,
                datasets: [{
                    data: estadosData,
                    backgroundColor: [colors.warning, colors.primary, colors.info, colors.danger],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 8,
                            padding: 20,
                            font: { size: 12, weight: '500' }
                        }
                    }
                }
            }
        });
    }

    // --- 2. Gráfico de Tendencia (Línea con Suavizado / Curva) ---
    const ctxDias = document.getElementById('diasChart');
    if (ctxDias) {
        const context = ctxDias.getContext('2d');
        const gradient = context.createLinearGradient(0, 0, 0, 250);
        gradient.addColorStop(0, 'rgba(1, 148, 70, 0.35)');
        gradient.addColorStop(1, 'rgba(1, 148, 70, 0.0)');

        new Chart(ctxDias, {
            type: 'line',
            data: {
                labels: diasLabels,
                datasets: [{
                    label: 'Solicitudes',
                    data: diasData,
                    borderColor: colors.primary,
                    borderWidth: 3,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.38,
                    pointBackgroundColor: '#ffffff',
                    pointBorderColor: colors.primary,
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    pointHoverBackgroundColor: colors.primary,
                    pointHoverBorderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: '#f1f5f9' }
                    },
                    x: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // --- 3. Gráfico Top Dispositivos (Barras Horizontales con Gradiente) ---
    const ctxDispositivos = document.getElementById('dispositivosChart');
    if (ctxDispositivos) {
        const contextDisp = ctxDispositivos.getContext('2d');
        const gradientBar = contextDisp.createLinearGradient(0, 0, 400, 0);
        gradientBar.addColorStop(0, colors.secondary);
        gradientBar.addColorStop(1, '#14b8a6'); // Tono complementario suave de la misma gama Teal

        new Chart(ctxDispositivos, {
            type: 'bar',
            data: {
                labels: dispositivosLabels,
                datasets: [{
                    label: 'Total Préstamos',
                    data: dispositivosData,
                    backgroundColor: gradientBar,
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 16
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: '#f1f5f9' }
                    },
                    y: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
});