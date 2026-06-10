const API_BASE = window.APP_CONFIG?.API_BASE || "http://127.0.0.1:8000";

const SUPABASE_URL = window.APP_CONFIG?.SUPABASE_URL || "";
const SUPABASE_ANON_KEY = window.APP_CONFIG?.SUPABASE_ANON_KEY || "";

let supabaseClient = null;
let currentUser = null;

let categoryChart = null;
let monthlyTrendChart = null;
let analysisCategoryChart = null;
let analysisMonthlyChart = null;
let forecastChart = null;

let currentTransactionLimit = 5;
let currentDataMode = "mock";

document.addEventListener("DOMContentLoaded", async () => {
  checkApiHealth();

  setupBudgetForm();
  setupTransactionForm();
  setupUploadForm();
  setupAuthForms();

  initialiseSupabase();

  if (supabaseClient) {
    await initialiseAuth();
  } else {
    showAuthMessage(
      "Supabase is not configured yet. Add your Supabase URL and anon key in .env, then run python generate_config.py.",
      "error",
    );
    showLoggedOutState();
  }
});

/* ---------------- SUPABASE AUTH ---------------- */

function initialiseSupabase() {
  const urlIsMissing = SUPABASE_URL.trim() === "";
  const keyIsMissing = SUPABASE_ANON_KEY.trim() === "";

  if (urlIsMissing || keyIsMissing) {
    supabaseClient = null;
    return;
  }

  supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

async function initialiseAuth() {
  const { data, error } = await supabaseClient.auth.getSession();

  if (error) {
    showAuthMessage("Could not check login session.", "error");
    showLoggedOutState();
    return;
  }

  if (data.session && data.session.user) {
    currentUser = data.session.user;
    showLoggedInState(currentUser);
    await refreshAllData();
  } else {
    showLoggedOutState();
  }

  supabaseClient.auth.onAuthStateChange(async (event, session) => {
    if (session && session.user) {
      currentUser = session.user;
      showLoggedInState(currentUser);
      await refreshAllData();
    } else {
      currentUser = null;
      showLoggedOutState();
    }
  });
}

function setupAuthForms() {
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!supabaseClient) {
      showAuthMessage("Supabase is not configured yet.", "error");
      return;
    }

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    try {
      const { data, error } = await supabaseClient.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        showAuthMessage(error.message, "error");
        return;
      }

      currentUser = data.user;
      showAuthMessage("Login successful.", "success");
      loginForm.reset();
    } catch (error) {
      showAuthMessage("Login failed. Please try again.", "error");
      console.error(error);
    }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!supabaseClient) {
      showAuthMessage("Supabase is not configured yet.", "error");
      return;
    }

    const email = document.getElementById("signupEmail").value;
    const password = document.getElementById("signupPassword").value;

    try {
      const { data, error } = await supabaseClient.auth.signUp({
        email,
        password,
      });

      if (error) {
        showAuthMessage(error.message, "error");
        return;
      }

      signupForm.reset();

      if (data.user && data.session) {
        showAuthMessage(
          "Account created and logged in successfully.",
          "success",
        );
      } else {
        showAuthMessage(
          "Account created. Please check your email to confirm your account, then log in.",
          "success",
        );
      }
    } catch (error) {
      showAuthMessage("Sign up failed. Please try again.", "error");
      console.error(error);
    }
  });
}

function showAuthForm(type) {
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");
  const loginTabBtn = document.getElementById("loginTabBtn");
  const signupTabBtn = document.getElementById("signupTabBtn");

  if (type === "login") {
    loginForm.classList.remove("hidden-auth-form");
    signupForm.classList.add("hidden-auth-form");
    loginTabBtn.classList.add("active-auth-tab");
    signupTabBtn.classList.remove("active-auth-tab");
  } else {
    signupForm.classList.remove("hidden-auth-form");
    loginForm.classList.add("hidden-auth-form");
    signupTabBtn.classList.add("active-auth-tab");
    loginTabBtn.classList.remove("active-auth-tab");
  }

  showAuthMessage("", "clear");
}

function showLoggedInState(user) {
  const authSection = document.getElementById("authSection");
  const appSection = document.getElementById("appSection");
  const emailBox = document.getElementById("loggedInUserEmail");

  authSection.style.display = "none";
  appSection.classList.remove("hidden-app-section");

  emailBox.textContent = user.email || "Logged in user";
}

function showLoggedOutState() {
  const authSection = document.getElementById("authSection");
  const appSection = document.getElementById("appSection");
  const emailBox = document.getElementById("loggedInUserEmail");

  authSection.style.display = "block";
  appSection.classList.add("hidden-app-section");

  emailBox.textContent = "Not logged in";
}

async function logoutUser() {
  if (!supabaseClient) {
    showAuthMessage("Supabase is not configured yet.", "error");
    return;
  }

  const { error } = await supabaseClient.auth.signOut();

  if (error) {
    showInlineMessage("Could not log out. Please try again.", "error");
    console.error(error);
    return;
  }

  currentUser = null;
  showAuthMessage("You have logged out successfully.", "success");
}

function showAuthMessage(message, type) {
  const box = document.getElementById("authMessage");

  box.textContent = message;
  box.className = "auth-message";

  if (!message || type === "clear") {
    return;
  }

  if (type === "success") {
    box.classList.add("auth-success");
  } else if (type === "error") {
    box.classList.add("auth-error");
  }
}

/* ---------------- PAGE NAVIGATION ---------------- */

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

  loadDataStatus();
}

/* ---------------- API HELPERS ---------------- */

async function getAuthHeaders() {
  if (!supabaseClient) {
    throw new Error("Supabase is not configured.");
  }

  const { data, error } = await supabaseClient.auth.getSession();

  if (error || !data.session) {
    throw new Error("You must be logged in to use this feature.");
  }

  return {
    Authorization: `Bearer ${data.session.access_token}`,
  };
}

async function apiGet(endpoint) {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

async function apiPost(endpoint, data) {
  const authHeaders = await getAuthHeaders();

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: {
      ...authHeaders,
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

async function checkApiHealth() {
  const statusBox = document.getElementById("apiStatus");

  try {
    const response = await fetch(`${API_BASE}/health`);
    const data = await response.json();

    statusBox.textContent = data.message || "API online";
    statusBox.classList.add("online");
    statusBox.classList.remove("offline");
  } catch (error) {
    statusBox.textContent = "API offline";
    statusBox.classList.add("offline");
    statusBox.classList.remove("online");
  }
}

function formatCurrency(value) {
  const number = Number(value || 0);

  return number.toLocaleString("en-GB", {
    style: "currency",
    currency: "GBP",
  });
}

function formatBudgetMonth(monthValue) {
  if (!monthValue) {
    return "Unknown Month";
  }

  const [year, month] = monthValue.split("-");

  const date = new Date(Number(year), Number(month) - 1, 1);

  return date.toLocaleDateString("en-GB", {
    month: "long",
    year: "numeric",
  });
}

/* ---------------- DATA MODE ---------------- */

async function loadDataStatus() {
  try {
    const data = await apiGet("/data-status");

    currentDataMode = data.active_dataset || "mock";

    document.getElementById("activeDatasetMode").textContent = currentDataMode;
    document.getElementById("dataModeMessage").textContent =
      data.message || "Data mode loaded.";

    document.getElementById("mockCount").textContent =
      data.mock_transactions ?? 0;

    document.getElementById("uploadedCount").textContent =
      data.uploaded_transactions ?? 0;

    document.getElementById("manualCount").textContent =
      data.manual_transactions ?? 0;

    updateDataModeButtons(currentDataMode);
  } catch (error) {
    console.error("Data status error:", error);

    document.getElementById("activeDatasetMode").textContent = "error";
    document.getElementById("dataModeMessage").textContent =
      "Could not load data mode. Please log in again or check the backend.";
  }
}

function updateDataModeButtons(mode) {
  const buttons = {
    mock: document.getElementById("modeMockBtn"),
    uploaded: document.getElementById("modeUploadedBtn"),
    manual: document.getElementById("modeManualBtn"),
    combined: document.getElementById("modeCombinedBtn"),
  };

  Object.keys(buttons).forEach((key) => {
    if (buttons[key]) {
      buttons[key].classList.toggle("active-data-mode", key === mode);
    }
  });
}

async function setDataMode(mode) {
  try {
    const result = await apiPost("/dataset-mode", { mode });

    await refreshAllData();

    if (result.changed === false) {
      showInlineMessage(result.message, "warning");
    } else {
      showInlineMessage(
        result.message || `Data mode changed to ${mode}.`,
        "success",
      );
    }
  } catch (error) {
    showInlineMessage(
      "Could not switch data mode. Please check that you are logged in and the backend is running.",
      "error",
    );
    console.error(error);
  }
}

async function refreshAllData() {
  await loadDataStatus();
  await loadDashboard();
  await loadBudget();
  await loadAnalysis();
  await loadForecast();
  await loadInsights();
  await loadTransactions(currentTransactionLimit);
  await loadAuditLog();
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
      await refreshAllData();
      showInlineMessage(
        "Budget saved successfully for your account.",
        "success",
      );
    } catch (error) {
      showInlineMessage(
        "Could not save budget. Please check your form values.",
        "error",
      );
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

    const container = document.getElementById("budgetGroupsContainer");
    container.innerHTML = "";

    const budgetGroups = data.budget_groups || [];

    if (budgetGroups.length === 0) {
      container.innerHTML = `
        <div class="empty-state-box">
          <h4>No budgets added yet</h4>
          <p>Add a monthly income and category budget to start tracking your spending.</p>
        </div>
      `;
      return;
    }

    budgetGroups.forEach((group) => {
      const monthCard = document.createElement("section");
      monthCard.className = "budget-month-card";

      monthCard.innerHTML = `
        <div class="budget-month-card-header">
          <div>
            <h3>${formatBudgetMonth(group.month)}</h3>
            <p>${group.month} budget summary</p>
          </div>

          <span class="budget-month-badge">${group.month}</span>
        </div>

        <div class="budget-month-summary-grid">
          <div>
            <span>Income</span>
            <strong>${formatCurrency(group.monthly_income)}</strong>
          </div>

          <div>
            <span>Total Budget</span>
            <strong>${formatCurrency(group.total_budget)}</strong>
          </div>

          <div>
            <span>Spent</span>
            <strong>${formatCurrency(group.spent_so_far)}</strong>
          </div>

          <div>
            <span>Remaining</span>
            <strong>${formatCurrency(group.remaining_money)}</strong>
          </div>

          <div>
            <span>Safe Daily</span>
            <strong>${formatCurrency(group.safe_daily_spending)}</strong>
          </div>
        </div>

        <div class="budget-category-list">
          ${(group.category_budgets || [])
            .map((item) => {
              const spent = Number(item.spent || 0);
              const budgetAmount = Number(item.budget_amount || 0);
              const percentage =
                budgetAmount > 0
                  ? Math.min((spent / budgetAmount) * 100, 100)
                  : 0;

              return `
                <article class="budget-category-row">
                  <div class="budget-category-name">
                    <h4>${item.category}</h4>
                    ${renderStatusBadge(item.status)}
                  </div>

                  <div class="budget-category-money">
                    <div>
                      <span>Budget</span>
                      <strong>${formatCurrency(item.budget_amount)}</strong>
                    </div>

                    <div>
                      <span>Spent</span>
                      <strong>${formatCurrency(item.spent)}</strong>
                    </div>

                    <div>
                      <span>Remaining</span>
                      <strong>${formatCurrency(item.remaining)}</strong>
                    </div>
                  </div>

                  <div class="budget-progress-track">
                    <div class="budget-progress-fill" style="width: ${percentage}%"></div>
                  </div>
                </article>
              `;
            })
            .join("")}
        </div>
      `;

      container.appendChild(monthCard);
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
      resizeDelay: 200,
      spanGaps: true,
    },
  });
}

/* ---------------- INSIGHTS ---------------- */

async function loadInsights() {
  try {
    const data = await apiGet("/insights");

    document.getElementById("insightSummary").textContent =
      data.summary || "Insights generated from your selected data mode.";

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
        document.getElementById("paymentMethod").value || "Debit Card",
    };

    try {
      await apiPost("/transactions", transaction);
      form.reset();

      await refreshAllData();

      showInlineMessage(
        "Transaction saved successfully for your account.",
        "success",
      );
    } catch (error) {
      showInlineMessage(
        "Could not save transaction. Please check the form and try again.",
        "error",
      );
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
          ? `Showing the last 5 transactions for ${currentDataMode} mode.`
          : `Showing all available transactions for ${currentDataMode} mode.`;
    }

    if (lastFiveBtn && showAllBtn) {
      lastFiveBtn.classList.toggle("active-small-btn", limit === 5);
      showAllBtn.classList.toggle("active-small-btn", limit !== 5);
    }

    if (!data || data.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7">No transactions available for the selected data mode.</td>
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
      const authHeaders = await getAuthHeaders();

      const response = await fetch(`${API_BASE}/upload-csv`, {
        method: "POST",
        headers: {
          ...authHeaders,
        },
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
      await refreshAllData();
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

/* ---------------- INLINE MESSAGES ---------------- */

function showInlineMessage(message, type = "success") {
  const messageBox = document.getElementById("dataModeMessage");

  if (!messageBox) {
    return;
  }

  messageBox.textContent = message;

  messageBox.classList.remove(
    "success-message",
    "warning-message",
    "error-message",
  );

  if (type === "success") {
    messageBox.classList.add("success-message");
  } else if (type === "warning") {
    messageBox.classList.add("warning-message");
  } else if (type === "error") {
    messageBox.classList.add("error-message");
  }
}

/* ---------------- BADGES ---------------- */

function getSourceClass(source) {
  if (source === "manual") return "source-manual";
  if (source === "uploaded") return "source-uploaded";
  if (source === "mock") return "source-mock";
  if (source === "demo") return "source-demo";
  if (source === "combined") return "source-combined";
  return "source-demo";
}

function renderSourceBadge(source) {
  const safeSource = source || "mock";
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
