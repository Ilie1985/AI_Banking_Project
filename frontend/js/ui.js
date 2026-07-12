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

function getForecastReliabilityMessage(r2Score) {
  const score = Number(r2Score || 0);

  if (score < 0.3) {
    return (
      "A low R² score means the selected data has irregular spending patterns, " +
      "so the forecast should be treated as an estimate rather than a precise prediction."
    );
  }

  if (score < 0.6) {
    return (
      "The R² score suggests the forecast has moderate reliability. " +
      "The prediction can be useful as a guide, but spending patterns may still vary."
    );
  }

  return (
    "The R² score suggests the model has found a stronger pattern in the selected data. " +
    "The forecast is likely to be more reliable, but it should still be treated as an estimate."
  );
}

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