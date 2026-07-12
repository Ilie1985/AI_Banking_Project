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