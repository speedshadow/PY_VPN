document.addEventListener('DOMContentLoaded', function () {
    if (window.Chart) {
        // Visits chart
        var ctxVisits = document.getElementById('visitsChart').getContext('2d');
        new Chart(ctxVisits, {
            type: 'line',
            data: visitsChartData,
            options: {responsive: true, plugins: {legend: {display: false}}}
        });
        // Bots chart
        var ctxBots = document.getElementById('botsChart').getContext('2d');
        new Chart(ctxBots, {
            type: 'doughnut',
            data: botsChartData,
            options: {responsive: true}
        });
        // Affiliate clicks chart
        var ctxAff = document.getElementById('affClicksChart').getContext('2d');
        new Chart(ctxAff, {
            type: 'bar',
            data: affClicksChartData,
            options: {responsive: true, plugins: {legend: {display: false}}}
        });
    }
});
