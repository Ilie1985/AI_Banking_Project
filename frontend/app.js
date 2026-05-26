const API_BASE = "http://127.0.0.1:8000";

let categoryChart = null;
let monthlyTrendChart = null;
let analysisCategoryChart = null;
let analysisMonthlyChart = null;
let forecastChart = null;
let currentTransactionLimit = 5;

document.addEventListener("DOMContentLoaded", () => {
  checkApiHealth();

  loadDashboard();
  loadBudget();
  loadAnalysis();
  loadForecast();
  loadInsights();
  loadTransactions(5);
  loadAuditLog();

  setupBudgetForm();
  setupTransactionForm();
  setupUploadForm();
});

function showPage(pageId, button) {
  const pages = document.querySelectorAll(".page");
  pages.forEach((page) => page.classList.remove("active-page"));

  document.getElementById(pageId).classList.add("active-page");

  const buttons = document.querySelectorAll(".nav-btn");
  buttons.forEach((btn) => btn.classList.remove("active"));

  button.classList.add("active");

  if (pageId === "dashboard") loadDashboard();
  if (pageId === "budget") loadBudget();
  if (pageId === "analysis") loadAnalysis();
  if (pageId === "forecast") loadForecast();
  if (pageId === "insights") loadInsights();
  if (pageId === "transactions") loadTransactions(currentTransactionLimit);
  if (pageId === "audit") loadAuditLog();
}

async function apiGet(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

async function apiPost(endpoint, data) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }

  return response.json();
}

function formatCurrency(value) {
  const number = Number(value || 0);

  return number.toLocaleString("en-GB", {
    style: "currency",
    currency: "GBP",
  });
}

function formatNumber(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }

  return Number(value).toFixed(2);
}

async function checkApiHealth() {
  const statusBox = document.getElementById("apiStatus");

  try {
    const data = await apiGet("/health");

    statusBox.textContent = data.message || "API online";
    statusBox.classList.add("online");
    statusBox.classList.remove("offline");
  } catch (error) {
    statusBox.textContent = "API offline";
    statusBox.classList.add("offline");
    statusBox.classList.remove("online");
  }
}

/* ---------------- DASHBOARD ---------------- */

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
    container.innerHTML = "<p>No source data available yet.</p>";
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
    },
  });
}

/* ---------------- BUDGET ---------------- */

function setupBudgetForm() {
  const form = document.getElementById("budgetForm");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const budget = {
      month: document.getElementById("budgetMonth").value,
      monthly_income: Number(document.getElementById("monthlyIncome").value),
      category: document.getElementById("budgetCategory").value,
      budget_amount: Number(document.getElementById("budgetAmount").value),
    };

    try {
      await apiPost("/budget", budget);
      form.reset();
      await loadBudget();
      await loadDashboard();
      await loadInsights();
      await loadAuditLog();
      alert("Budget saved successfully.");
    } catch (error) {
      alert("Could not save budget. Check your backend and form values.");
      console.error(error);
    }
  });
}

async function loadBudget() {
  try {
    const data = await apiGet("/budget");

    document.getElementById("budgetIncome").textContent = formatCurrency(
      data.monthly_income,
    );
    document.getElementById("spentSoFar").textContent = formatCurrency(
      data.spent_so_far,
    );
    document.getElementById("remainingMoney").textContent = formatCurrency(
      data.remaining_money,
    );
    document.getElementById("safeDailySpending").textContent = formatCurrency(
      data.safe_daily_spending,
    );

    const tableBody = document.getElementById("budgetTableBody");
    tableBody.innerHTML = "";

    const rows = data.category_budgets || [];

    if (rows.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5">No budget categories added yet.</td>
        </tr>
      `;
      return;
    }

    rows.forEach((item) => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${item.category}</td>
        <td>${formatCurrency(item.budget_amount)}</td>
        <td>${formatCurrency(item.spent)}</td>
        <td>${formatCurrency(item.remaining)}</td>
        <td>${renderStatusBadge(item.status)}</td>
      `;

      tableBody.appendChild(row);
    });
  } catch (error) {
    console.error("Budget error:", error);
  }
}

/* ---------------- ANALYSIS ---------------- */

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
    },
  });
}

function renderAnalysisSourceTable(data) {
  const tableBody = document.getElementById("analysisSourceTable");
  tableBody.innerHTML = "";

  if (data.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="3">No source summary available.</td>
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

/* ---------------- FORECAST ---------------- */

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

    document.getElementById("forecastMessage").textContent =
      data.message || "No forecast explanation available.";

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
      spanGaps: true,
    },
  });
}

/* ---------------- INSIGHTS ---------------- */

async function loadInsights() {
  try {
    const data = await apiGet("/insights");

    document.getElementById("insightSummary").textContent =
      data.summary || "Insights generated from your available data.";

    const container = document.getElementById("insightsList");
    container.innerHTML = "";

    const insights = data.insights || [];

    if (insights.length === 0) {
      container.innerHTML = `
        <div class="insight-card">
          No insights available yet. Add budgets or transactions first.
        </div>
      `;
      return;
    }

    insights.forEach((insight) => {
      const card = document.createElement("div");
      card.className = "insight-card";
      card.textContent = insight;
      container.appendChild(card);
    });
  } catch (error) {
    console.error("Insights error:", error);
  }
}

/* ---------------- TRANSACTIONS ---------------- */

function setupTransactionForm() {
  const form = document.getElementById("transactionForm");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const transaction = {
      date: document.getElementById("transactionDate").value,
      description: document.getElementById("transactionDescription").value,
      amount: Number(document.getElementById("transactionAmount").value),
      transaction_type: document.getElementById("transactionType").value,
      category: document.getElementById("transactionCategory").value,
      payment_method:
        document.getElementById("paymentMethod").value || "Manual",
    };

    try {
      await apiPost("/transactions", transaction);
      form.reset();

      await loadTransactions(currentTransactionLimit);
      await loadDashboard();
      await loadBudget();
      await loadAnalysis();
      await loadForecast();
      await loadInsights();
      await loadAuditLog();

      alert("Transaction saved successfully.");
    } catch (error) {
      alert("Could not save transaction.");
      console.error(error);
    }
  });
}

async function loadTransactions(limit = 5) {
  currentTransactionLimit = limit;

  try {
    const data = await apiGet(`/transactions?limit=${limit}`);

    const tableBody = document.getElementById("transactionsTableBody");
    const note = document.getElementById("transactionViewNote");
    const lastFiveBtn = document.getElementById("showLastFiveBtn");
    const showAllBtn = document.getElementById("showAllTransactionsBtn");

    tableBody.innerHTML = "";

    if (note) {
      note.textContent =
        limit === 5
          ? "Showing the last 5 transactions."
          : "Showing all available transactions.";
    }

    if (lastFiveBtn && showAllBtn) {
      lastFiveBtn.classList.toggle("active-small-btn", limit === 5);
      showAllBtn.classList.toggle("active-small-btn", limit !== 5);
    }

    if (!data || data.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7">No transactions available.</td>
        </tr>
      `;
      return;
    }

    data.forEach((item) => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${item.date}</td>
        <td>${item.description}</td>
        <td>${formatCurrency(item.amount)}</td>
        <td>${item.transaction_type}</td>
        <td>${item.category}</td>
        <td>${item.payment_method}</td>
        <td>${renderSourceBadge(item.source)}</td>
      `;

      tableBody.appendChild(row);
    });
  } catch (error) {
    console.error("Transactions error:", error);
  }
}

/* ---------------- CSV UPLOAD ---------------- */

function setupUploadForm() {
  const form = document.getElementById("uploadForm");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const fileInput = document.getElementById("csvFile");
    const file = fileInput.files[0];

    if (!file) {
      showUploadResult("Please select a CSV file first.", "error");
      return;
    }

    const formData = new FormData();

    formData.append("file", file);
    formData.append("date_column", document.getElementById("dateColumn").value);
    formData.append(
      "description_column",
      document.getElementById("descriptionColumn").value,
    );
    formData.append(
      "amount_column",
      document.getElementById("amountColumn").value,
    );
    formData.append(
      "category_column",
      document.getElementById("categoryColumn").value,
    );
    formData.append("type_column", document.getElementById("typeColumn").value);
    formData.append(
      "payment_method_column",
      document.getElementById("paymentMethodColumn").value,
    );

    try {
      const response = await fetch(`${API_BASE}/upload-csv`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const result = await response.json();

      showUploadResult(
        `${result.message} Rows uploaded: ${result.rows_uploaded}`,
        "success",
      );

      form.reset();

      await loadTransactions();
      await loadDashboard();
      await loadBudget();
      await loadAnalysis();
      await loadForecast();
      await loadInsights();
      await loadAuditLog();
    } catch (error) {
      showUploadResult(
        "Upload failed. Check that the column names exactly match your CSV headers.",
        "error",
      );

      console.error(error);
    }
  });
}

function showUploadResult(message, type) {
  const box = document.getElementById("uploadResult");
  box.textContent = message;
  box.className = `result-box ${type}`;
}

/* ---------------- AUDIT LOG ---------------- */

async function loadAuditLog() {
  try {
    const data = await apiGet("/audit-log");

    const tableBody = document.getElementById("auditTableBody");
    tableBody.innerHTML = "";

    if (!data || data.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5">No audit records available yet.</td>
        </tr>
      `;
      return;
    }

    data.forEach((item) => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${item.created_at}</td>
        <td>${item.action}</td>
        <td>${item.record_type}</td>
        <td>${renderSourceBadge(item.source)}</td>
        <td>${item.details || ""}</td>
      `;

      tableBody.appendChild(row);
    });
  } catch (error) {
    console.error("Audit log error:", error);
  }
}

/* ---------------- BADGES ---------------- */

function getSourceClass(source) {
  if (source === "manual") return "source-manual";
  if (source === "uploaded") return "source-uploaded";
  return "source-demo";
}

function renderSourceBadge(source) {
  const safeSource = source || "demo";
  return `<span class="source-badge ${getSourceClass(safeSource)}">${safeSource}</span>`;
}

function renderStatusBadge(status) {
  let className = "status-healthy";

  if (status === "Over budget") {
    className = "status-over";
  } else if (status === "Close to limit") {
    className = "status-close";
  }

  return `<span class="status-badge ${className}">${status}</span>`;
}
