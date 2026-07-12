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