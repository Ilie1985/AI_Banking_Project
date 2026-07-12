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

    currentBudgetItems = {};

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
              currentBudgetItems[item.id] = item;

              const spent = Number(item.spent || 0);
              const budgetAmount = Number(item.budget_amount || 0);
              const percentage =
                budgetAmount > 0
                  ? Math.min((spent / budgetAmount) * 100, 100)
                  : 0;

              return `
                <article class="budget-category-row" id="budget-row-${item.id}">
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

                  <div class="budget-progress-area">
                    <div class="budget-progress-track">
                      <div class="budget-progress-fill" style="width: ${percentage}%"></div>
                    </div>

                    <div class="budget-action-buttons">
                      <button type="button" class="small-edit-btn" onclick="startBudgetEdit(${item.id})">
                        Edit
                      </button>

                      <button type="button" class="small-delete-btn" onclick="startBudgetDelete(${item.id})">
                        Delete
                      </button>
                    </div>
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

function startBudgetEdit(budgetId) {
  const item = currentBudgetItems[budgetId];
  const row = document.getElementById(`budget-row-${budgetId}`);

  if (!item || !row) {
    showInlineMessage(
      "Could not load this budget category for editing.",
      "error",
    );
    return;
  }

  row.classList.add("editing-budget-row");

  row.innerHTML = `
    <div class="budget-edit-title">
      <h4>Edit Budget Category</h4>
      <p>${item.month}</p>
    </div>

    <div class="budget-edit-fields">
      <label>
        Category
        <input type="text" id="editBudgetCategory-${budgetId}" value="${item.category}" />
      </label>

      <label>
        Budget Amount
        <input type="number" id="editBudgetAmount-${budgetId}" value="${item.budget_amount}" min="0" step="0.01" />
      </label>
    </div>

    <div class="budget-edit-actions">
      <button type="button" class="small-save-btn" onclick="saveBudgetEdit(${budgetId})">
        Save Changes
      </button>

      <button type="button" class="small-cancel-btn" onclick="loadBudget()">
        Cancel
      </button>
    </div>
  `;
}

async function saveBudgetEdit(budgetId) {
  const categoryInput = document.getElementById(
    `editBudgetCategory-${budgetId}`,
  );
  const amountInput = document.getElementById(`editBudgetAmount-${budgetId}`);

  if (!categoryInput || !amountInput) {
    showInlineMessage("Could not read the edited budget values.", "error");
    return;
  }

  const category = categoryInput.value.trim();
  const budgetAmount = Number(amountInput.value);

  if (!category) {
    showInlineMessage("Category name cannot be empty.", "error");
    return;
  }

  if (Number.isNaN(budgetAmount) || budgetAmount < 0) {
    showInlineMessage("Budget amount must be zero or more.", "error");
    return;
  }

  try {
    await apiPut(`/budget/${budgetId}`, {
      category,
      budget_amount: budgetAmount,
    });

    await refreshAllData();

    showInlineMessage("Budget category updated successfully.", "success");
  } catch (error) {
    showInlineMessage("Could not update the budget category.", "error");
    console.error(error);
  }
}

function startBudgetDelete(budgetId) {
  const item = currentBudgetItems[budgetId];
  const row = document.getElementById(`budget-row-${budgetId}`);

  if (!item || !row) {
    showInlineMessage(
      "Could not load this budget category for deletion.",
      "error",
    );
    return;
  }

  row.classList.add("deleting-budget-row");

  row.innerHTML = `
    <div class="budget-edit-title">
      <h4>Delete ${item.category}?</h4>
      <p>This removes the budget category for ${item.month}. Transactions will not be deleted.</p>
    </div>

    <div class="budget-edit-actions">
      <button type="button" class="small-delete-btn" onclick="confirmBudgetDelete(${budgetId})">
        Confirm Delete
      </button>

      <button type="button" class="small-cancel-btn" onclick="loadBudget()">
        Cancel
      </button>
    </div>
  `;
}

async function confirmBudgetDelete(budgetId) {
  try {
    await apiDelete(`/budget/${budgetId}`);

    await refreshAllData();

    showInlineMessage("Budget category deleted successfully.", "success");
  } catch (error) {
    showInlineMessage("Could not delete the budget category.", "error");
    console.error(error);
  }
}