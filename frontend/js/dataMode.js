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