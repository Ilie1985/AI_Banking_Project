async function loadAnalysis() {
  try {
    const data = await apiGet("/analysis");

    document.getElementById("averageMonthlySpending").textContent =
      formatCurrency(data.average_monthly_spending);

    document.getElementById("highestMonth").textContent =
      data.highest_spending_month
        ? `${data.highest_spending_month.month} (${formatCurrency(data.highest_spending_month.amount)})`
        : "N/A";

    document.getElementById("lowestMonth").textContent =
      data.lowest_spending_month
        ? `${data.lowest_spending_month.month} (${formatCurrency(data.lowest_spending_month.amount)})`
        : "N/A";

    renderAnalysisCategoryChart(data.top_categories || []);
    renderAnalysisMonthlyChart(data.monthly_analysis || []);
    renderAnalysisSourceTable(data.source_summary || []);
  } catch (error) {
    console.error("Analysis error:", error);
  }
}

function renderAnalysisCategoryChart(data) {
  const ctx = document.getElementById("analysisCategoryChart");

  if (analysisCategoryChart) {
    analysisCategoryChart.destroy();
  }

  analysisCategoryChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map((item) => item.category),
      datasets: [
        {
          label: "Total Spending",
          data: data.map((item) => item.amount),
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      resizeDelay: 200,
      indexAxis: "y",
    },
  });
}

function renderAnalysisMonthlyChart(data) {
  const ctx = document.getElementById("analysisMonthlyChart");

  if (analysisMonthlyChart) {
    analysisMonthlyChart.destroy();
  }

  analysisMonthlyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map((item) => item.month),
      datasets: [
        {
          label: "Monthly Spending",
          data: data.map((item) => item.amount),
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      resizeDelay: 200,
    },
  });
}

function renderAnalysisSourceTable(data) {
  const tableBody = document.getElementById("analysisSourceTable");
  tableBody.innerHTML = "";

  if (data.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="3">No source summary available for the selected mode.</td>
      </tr>
    `;
    return;
  }

  data.forEach((item) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${renderSourceBadge(item.source)}</td>
      <td>${item.transaction_count}</td>
      <td>${formatCurrency(item.total_amount)}</td>
    `;

    tableBody.appendChild(row);
  });
}