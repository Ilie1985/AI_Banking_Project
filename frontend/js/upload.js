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