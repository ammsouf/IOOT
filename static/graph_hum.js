let humidityChart = null;

// Set default dates (last 7 days)
function setDefaultDates() {
  const today = new Date();
  const lastWeek = new Date(today);
  lastWeek.setDate(today.getDate() - 7);

  document.getElementById('end-date').valueAsDate = today;
  document.getElementById('start-date').valueAsDate = lastWeek;
}

// Quick filter buttons
function setQuickFilter(period) {
  const today = new Date();
  const startDate = new Date(today);

  // Remove active class from all buttons
  document.querySelectorAll('.quick-filter-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Add active class to clicked button
  event.target.classList.add('active');

  switch(period) {
    case 'week':
      startDate.setDate(today.getDate() - 7);
      break;
    case 'month':
      startDate.setDate(today.getDate() - 30);
      break;
    case '3months':
      startDate.setMonth(today.getMonth() - 3);
      break;
    case 'all':
      startDate.setFullYear(2020); // Far back date to get all data
      break;
  }

  document.getElementById('start-date').valueAsDate = startDate;
  document.getElementById('end-date').valueAsDate = today;

  loadHumidityData();
}

// Apply custom date filter
function applyCustomFilter() {
  const startDate = document.getElementById('start-date').value;
  const endDate = document.getElementById('end-date').value;

  if (!startDate || !endDate) {
    alert('Veuillez sélectionner les deux dates');
    return;
  }

  if (new Date(startDate) > new Date(endDate)) {
    alert('La date de début doit être antérieure à la date de fin');
    return;
  }

  // Remove active class from quick filter buttons
  document.querySelectorAll('.quick-filter-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  loadHumidityData();
}

// Load humidity data with date filter
async function loadHumidityData() {
  const historyUrl = document.body.getAttribute('data-history-url');
  const startDate = document.getElementById('start-date').value;
  const endDate = document.getElementById('end-date').value;

  // Build URL with date parameters
  let url = historyUrl;
  if (startDate && endDate) {
    url += `?start_date=${startDate}&end_date=${endDate}`;
  }

  console.log('Fetching humidity data from:', url);

  try {
    const response = await fetch(url);
    const json = await response.json();

    if (!json.success) {
      console.error('API error:', json.error);
      alert('Erreur lors du chargement des données: ' + json.error);
      return;
    }

    const data = json.data;
    console.log('Humidity data loaded:', data.length, 'points');

    // Update info
    document.getElementById('data-info').innerHTML = `
      📊 <strong>${json.count}</strong> mesures du <strong>${formatDate(json.start_date)}</strong> au <strong>${formatDate(json.end_date)}</strong>
    `;

    // Extract labels and values
    const labels = data.map(item => {
      const date = new Date(item.timestamp);
      return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    });

    const humidity = data.map(item => item.humidity);

    // Destroy existing chart if exists
    if (humidityChart) {
      humidityChart.destroy();
    }

    // Create the chart
    const ctx = document.getElementById('humChart');
    humidityChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Humidité (%)',
          data: humidity,
          borderColor: 'rgb(54, 162, 235)',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true,
          pointRadius: data.length > 100 ? 0 : 3,
          pointHoverRadius: 6,
          pointBackgroundColor: 'rgb(54, 162, 235)',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              font: {
                size: 13,
                weight: '500'
              },
              padding: 15,
              boxWidth: 15,
              boxHeight: 15
            }
          },
          tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            titleFont: {
              size: 13,
              weight: 'bold'
            },
            bodyFont: {
              size: 12
            },
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1
          },
          datalabels: {
            display: false
          }
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: 'Date et Heure',
              font: {
                size: 13,
                weight: '600'
              },
              padding: { top: 10 }
            },
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              maxTicksLimit: 20,
              font: {
                size: 11
              }
            },
            grid: {
              display: true,
              color: 'rgba(0, 0, 0, 0.05)',
              drawBorder: true
            }
          },
          y: {
            display: true,
            title: {
              display: true,
              text: 'Humidité (%)',
              font: {
                size: 13,
                weight: '600'
              },
              padding: { bottom: 10 }
            },
            beginAtZero: false,
            ticks: {
              font: {
                size: 11
              },
              padding: 8
            },
            grid: {
              display: true,
              color: 'rgba(0, 0, 0, 0.08)',
              drawBorder: true
            }
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        },
        layout: {
          padding: {
            top: 10,
            right: 15,
            bottom: 10,
            left: 10
          }
        }
      }
    });

  } catch (error) {
    console.error('Error loading humidity data:', error);
    alert('Erreur lors du chargement des données d\'humidité');
  }
}

// Format date for display
function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
  const ctx = document.getElementById('humChart');
  if (!ctx) {
    console.error('Canvas #humChart not found');
    return;
  }

  // Set default dates and load data
  setDefaultDates();
  loadHumidityData();
});