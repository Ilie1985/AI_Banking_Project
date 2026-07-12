async function loadDashboard() {
  try {
    const data = await apiGet("/dashboard");

    document.getElementById("totalIncome").textContent = formatCurrency(
      data.total_income,
    );
    document.getElementById("totalExpenses").textContent = formatCurrency(
      data.total_expenses,
    );
    document.getElementById("netSavings").textContent = formatCurrency(
      data.net_savings,
    );
    document.getElementById("transactionCount").textContent =
      data.transaction_count;

    renderSourceSummary(data.source_summary || []);
    renderCategoryChart(data.spending_by_category || []);
    renderMonthlyTrendChart(data.monthly_spending_trend || []);
  } catch (error) {
    console.error("Dashboard error:", error);
  }
}

function renderSourceSummary(sourceData) {
  const container = document.getElementById("sourceSummary");
  container.innerHTML = "";

  if (sourceData.length === 0) {
    container.innerHTML =
      "<p>No source data available for the selected mode.</p>";
    return;
  }

  sourceData.forEach((item) => {
    const badge = document.createElement("span");
    badge.className = `source-badge ${getSourceClass(item.source)}`;
    badge.textContent = `${item.source}: ${item.count}`;
    container.appendChild(badge);
  });
}

function renderCategoryChart(data) {
  const ctx = document.getElementById("categoryChart");

  if (categoryChart) {
    categoryChart.destroy();
  }

  categoryChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map((item) => item.category),
      datasets: [
        {
          label: "Spending",
          data: data.map((item) => item.amount),
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

function renderMonthlyTrendChart(data) {
  const ctx = document.getElementById("monthlyTrendChart");

  if (monthlyTrendChart) {
    monthlyTrendChart.destroy();
  }

  monthlyTrendChart = new Chart(ctx, {
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