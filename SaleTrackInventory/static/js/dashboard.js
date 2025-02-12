function initializeDashboard(stats) {
    // Initialize sales chart
    const salesCtx = document.getElementById('salesChart').getContext('2d');
    const salesData = stats.recent_sales.map(sale => ({
        x: new Date(sale.date),
        y: sale.total
    }));

    new Chart(salesCtx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Recent Sales',
                data: salesData,
                borderColor: '#0d6efd',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM D'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });

    // Initialize purchases chart
    const purchasesCtx = document.getElementById('purchasesChart').getContext('2d');
    const purchasesData = stats.recent_purchases.map(purchase => ({
        x: new Date(purchase.date),
        y: purchase.total
    }));

    new Chart(purchasesCtx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Recent Purchases',
                data: purchasesData,
                borderColor: '#dc3545',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM D'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });

    // Initialize Feather icons
    feather.replace();
}
