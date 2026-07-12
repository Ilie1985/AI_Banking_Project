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

async function apiPut(endpoint, data) {
  const authHeaders = await getAuthHeaders();

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "PUT",
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

async function apiDelete(endpoint) {
  const authHeaders = await getAuthHeaders();

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "DELETE",
    headers: authHeaders,
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