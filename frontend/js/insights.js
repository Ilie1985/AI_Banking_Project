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