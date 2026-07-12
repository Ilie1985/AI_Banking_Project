async function loadForecast() {
  try {
    const data = await apiGet("/forecast");

    document.getElementById("forecastPrediction").textContent =
      data.prediction !== null && data.prediction !== undefined
        ? formatCurrency(data.prediction)
        : "N/A";

    document.getElementById("forecastMae").textContent =
      data.mae !== null && data.mae !== undefined
        ? formatCurrency(data.mae)
        : "N/A";

    document.getElementById("forecastR2").textContent =
      data.r2_score !== null && data.r2_score !== undefined
        ? data.r2_score
        : "N/A";

    const reliabilityMessage = getForecastReliabilityMessage(data.r2_score);

    document.getElementById("forecastMessage").innerHTML = `
      <p>${data.message || "No forecast explanation available."}</p>
      <p class="forecast-reliability-note">${reliabilityMessage}</p>
    `;

    renderForecastChart(data.chart_data || []);
  } catch (error) {
    console.error("Forecast error:", error);
  }
}

function renderForecastChart(data) {
  const ctx = document.getElementById("forecastChart");

  if (forecastChart) {
    forecastChart.destroy();
  }

  forecastChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map((item) => item.month),
      datasets: [
        {
          label: "Actual Spending",
          data: data.map((item) => item.actual),
          tension: 0.3,
        },
        {
          label: "Predicted Spending",
          data: data.map((item) => item.predicted),
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      resizeDelay: 200,
      spanGaps: true,
    },
  });
}