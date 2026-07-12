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