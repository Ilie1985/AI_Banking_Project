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