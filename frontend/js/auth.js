function initialiseSupabase() {
  const urlIsMissing = SUPABASE_URL.trim() === "";
  const keyIsMissing = SUPABASE_ANON_KEY.trim() === "";

  if (urlIsMissing || keyIsMissing) {
    supabaseClient = null;
    return;
  }

  supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      storage: window.sessionStorage,
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
}

async function initialiseAuth() {
  const { data, error } = await supabaseClient.auth.getSession();

  if (error) {
    showAuthMessage("Could not check login session.", "error");
    showLoggedOutState();
    return;
  }

  if (data.session && data.session.user) {
    currentUser = data.session.user;
    showLoggedInState(currentUser);
    await refreshAllData();
  } else {
    showLoggedOutState();
  }

  supabaseClient.auth.onAuthStateChange(async (event, session) => {
    if (session && session.user) {
      currentUser = session.user;
      showLoggedInState(currentUser);
      await refreshAllData();
    } else {
      currentUser = null;
      showLoggedOutState();
    }
  });
}

function setupAuthForms() {
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!supabaseClient) {
      showAuthMessage("Supabase is not configured yet.", "error");
      return;
    }

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    try {
      const { data, error } = await supabaseClient.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        showAuthMessage(error.message, "error");
        return;
      }

      currentUser = data.user;
      showAuthMessage("Login successful.", "success");
      loginForm.reset();
    } catch (error) {
      showAuthMessage("Login failed. Please try again.", "error");
      console.error(error);
    }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!supabaseClient) {
      showAuthMessage("Supabase is not configured yet.", "error");
      return;
    }

    const email = document.getElementById("signupEmail").value;
    const password = document.getElementById("signupPassword").value;

    try {
      const { data, error } = await supabaseClient.auth.signUp({
        email,
        password,
      });

      if (error) {
        showAuthMessage(error.message, "error");
        return;
      }

      signupForm.reset();

      if (data.user && data.session) {
        showAuthMessage(
          "Account created and logged in successfully.",
          "success",
        );
      } else {
        showAuthMessage(
          "Account created. Please check your email to confirm your account, then log in.",
          "success",
        );
      }
    } catch (error) {
      showAuthMessage("Sign up failed. Please try again.", "error");
      console.error(error);
    }
  });
}

function showAuthForm(type) {
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");
  const loginTabBtn = document.getElementById("loginTabBtn");
  const signupTabBtn = document.getElementById("signupTabBtn");

  if (type === "login") {
    loginForm.classList.remove("hidden-auth-form");
    signupForm.classList.add("hidden-auth-form");
    loginTabBtn.classList.add("active-auth-tab");
    signupTabBtn.classList.remove("active-auth-tab");
  } else {
    signupForm.classList.remove("hidden-auth-form");
    loginForm.classList.add("hidden-auth-form");
    signupTabBtn.classList.add("active-auth-tab");
    loginTabBtn.classList.remove("active-auth-tab");
  }

  showAuthMessage("", "clear");
}

function showLoggedInState(user) {
  const authSection = document.getElementById("authSection");
  const appSection = document.getElementById("appSection");
  const emailBox = document.getElementById("loggedInUserEmail");

  authSection.style.display = "none";
  appSection.classList.remove("hidden-app-section");

  emailBox.textContent = user.email || "Logged in user";
}

function showLoggedOutState() {
  const authSection = document.getElementById("authSection");
  const appSection = document.getElementById("appSection");
  const emailBox = document.getElementById("loggedInUserEmail");

  authSection.style.display = "block";
  appSection.classList.add("hidden-app-section");

  emailBox.textContent = "Not logged in";
}

async function logoutUser() {
  if (!supabaseClient) {
    showAuthMessage("Supabase is not configured yet.", "error");
    return;
  }

  const { error } = await supabaseClient.auth.signOut();

  if (error) {
    showInlineMessage("Could not log out. Please try again.", "error");
    console.error(error);
    return;
  }

  currentUser = null;
  showAuthMessage("You have logged out successfully.", "success");
}

function showAuthMessage(message, type) {
  const box = document.getElementById("authMessage");

  box.textContent = message;
  box.className = "auth-message";

  if (!message || type === "clear") {
    return;
  }

  if (type === "success") {
    box.classList.add("auth-success");
  } else if (type === "error") {
    box.classList.add("auth-error");
  }
}