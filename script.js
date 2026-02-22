// ================================================================
// script.js — Single source of truth for auth + UI logic
// Auth state = token existence ONLY. No isLoggedIn flag anywhere.
// ================================================================

const API = "http://127.0.0.1:5000";

// ────────────────────────────────────────────
// TOAST NOTIFICATIONS (replaces all alert())
// ────────────────────────────────────────────
function toast(msg, type = "info") {
  const colors = { info: "#2b7a4b", error: "#c0392b", warn: "#d68910" };
  const t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText = `
    position:fixed; bottom:24px; right:24px;
    padding:12px 20px; border-radius:8px; color:#fff;
    background:${colors[type] || colors.info};
    font-family:Inter,sans-serif; font-size:14px;
    box-shadow:0 4px 12px rgba(0,0,0,0.25);
    z-index:9999; max-width:340px; line-height:1.4;
  `;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

// ────────────────────────────────────────────
// DATE FORMATTER
// ────────────────────────────────────────────
function formatUTCtoLocal(utcString) {
  if (!utcString) return "";
  let s = utcString.includes("T") ? utcString : utcString.replace(" ", "T");
  if (!s.endsWith("Z")) s += "Z";
  const d = new Date(s);
  return isNaN(d.getTime()) ? "Invalid Date" : d.toLocaleString();
}

// ────────────────────────────────────────────
// VALIDATION HELPERS
// ────────────────────────────────────────────
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
function validatePassword(password) {
  return password.length >= 8 && /[A-Z]/.test(password) && /[0-9]/.test(password);
}

// ────────────────────────────────────────────
// AUTH STATE — token existence only, NO isLoggedIn flag
// ────────────────────────────────────────────
function isLoggedIn() {
  return !!localStorage.getItem("accessToken");
}

function saveSession(data) {
  localStorage.setItem("accessToken",  data.access_token);
  localStorage.setItem("refreshToken", data.refresh_token);
  localStorage.setItem("user_id",      data.user.id);
  localStorage.setItem("user_email",   data.user.email);
  localStorage.setItem("full_name",    data.user.full_name);
  localStorage.setItem("is_admin",     data.user.is_admin ? "1" : "0");
}

function clearSession() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("user_id");
  localStorage.removeItem("user_email");
  localStorage.removeItem("full_name");
  localStorage.removeItem("is_admin");
}

function logout() {
  clearSession();
  window.location.href = "signin.html";
}

// ────────────────────────────────────────────
// TOKEN REFRESH
// ────────────────────────────────────────────
async function tryRefresh() {
  const rt = localStorage.getItem("refreshToken");
  if (!rt) return false;
  try {
    const res = await fetch(`${API}/token/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${rt}` },
    });
    if (!res.ok) { clearSession(); return false; }
    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem("accessToken", data.access_token);
      return true;
    }
  } catch (_) {}
  return false;
}

// ────────────────────────────────────────────
// CENTRALIZED FETCH WRAPPER (authenticated routes)
// ────────────────────────────────────────────
async function apiFetch(url, options = {}) {
  const buildHeaders = () => ({
    "Content-Type": "application/json",
    ...(options.headers || {}),
    ...(localStorage.getItem("accessToken")
      ? { Authorization: `Bearer ${localStorage.getItem("accessToken")}` }
      : {}),
  });

  let res = await fetch(url, { ...options, headers: buildHeaders() });

  // Auto-refresh on 401, then retry once
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await fetch(url, { ...options, headers: buildHeaders() });
    } else {
      clearSession();
      window.location.href = "signin.html";
      throw new Error("Session expired. Please log in again.");
    }
  }

  if (!res.ok) {
    let errMsg = `${res.status} ${res.statusText}`;
    try {
      const body = await res.clone().json();
      if (body.error) errMsg = body.error;
    } catch (_) {}
    throw new Error(errMsg);
  }
  return res;
}

// Public routes (login, register, forgot/reset password) — no auth header
async function publicFetch(url, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    let errMsg = `${res.status} ${res.statusText}`;
    try {
      const body = await res.clone().json();
      if (body.error) errMsg = body.error;
    } catch (_) {}
    throw new Error(errMsg);
  }
  return res;
}

// ────────────────────────────────────────────
// ACCESS GUARD — runs immediately on page load
// ────────────────────────────────────────────
(function guardProtectedPages() {
  const protectedPages = ["dashboard.html", "history.html", "profile.html", "admin.html"];
  const currentPage = window.location.pathname.split("/").pop();
  if (protectedPages.includes(currentPage) && !isLoggedIn()) {
    toast("You must log in first.", "error");
    setTimeout(() => { window.location.href = "signin.html"; }, 800);
  }
})();

// ────────────────────────────────────────────
// DOMContentLoaded — wire up all forms/buttons
// ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {

  // ── Password toggles ─────────────────────
  function initToggle(iconId, inputId) {
    const icon  = document.getElementById(iconId);
    const input = document.getElementById(inputId);
    if (!icon || !input) return;
    icon.addEventListener("click", function () {
      const hidden = input.type === "password";
      input.type = hidden ? "text" : "password";
      icon.src   = hidden ? "eye-open.png" : "eye-close.png";
    });
  }
  initToggle("eye-icon",    "password");
  initToggle("eye-confirm", "confirmPassword");

  // ── Sidebar ──────────────────────────────
  const menuIcon = document.getElementById("menu-icon");
  const sidebar  = document.getElementById("sidebar");
  const overlay  = document.getElementById("overlay");
  const mainEl   = document.querySelector(".main");

  if (menuIcon && sidebar) {
    menuIcon.addEventListener("click", function () {
      menuIcon.classList.toggle("active");
      sidebar.classList.toggle("hidden");
      if (mainEl) mainEl.classList.toggle("expanded");
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle("active");
        if (overlay) overlay.classList.toggle("active");
      }
    });
  }
  if (overlay) {
    overlay.addEventListener("click", function () {
      if (menuIcon) menuIcon.classList.remove("active");
      if (sidebar)  sidebar.classList.remove("active");
      overlay.classList.remove("active");
      if (window.innerWidth > 768) {
        if (sidebar) sidebar.classList.add("hidden");
        if (mainEl)  mainEl.classList.add("expanded");
      }
    });
  }
  if (sidebar) {
    sidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.innerWidth <= 768) {
          if (menuIcon) menuIcon.classList.remove("active");
          sidebar.classList.remove("active");
          if (overlay) overlay.classList.remove("active");
        }
      });
    });
  }

  // ── Logout buttons ───────────────────────
  document.querySelectorAll("[data-action='logout'], a[href='signout.html']").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      apiFetch(`${API}/logout`, { method: "POST" }).catch(() => {});
      logout();
    });
  });

  // ── Populate user info in navbar ─────────
  const nameEl  = document.getElementById("nav-user-name");
  const emailEl = document.getElementById("nav-user-email");
  if (nameEl)  nameEl.textContent  = localStorage.getItem("full_name")  || "";
  if (emailEl) emailEl.textContent = localStorage.getItem("user_email") || "";

  // ── SIGN IN FORM ─────────────────────────
  const signInForm = document.getElementById("signInForm");
  if (signInForm) {
    signInForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const email    = document.getElementById("email").value.trim().toLowerCase();
      const password = document.getElementById("password").value;
      if (!email || !password) { toast("Email and password are required.", "error"); return; }
      try {
        const res  = await publicFetch(`${API}/login`, {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        saveSession(data);
        toast("Sign in successful! Redirecting…");
        setTimeout(() => { window.location.href = "dashboard.html"; }, 600);
      } catch (err) {
        toast("Login failed: " + err.message, "error");
      }
    });
  }

  // ── REGISTER FORM ─────────────────────────
  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const fullName        = document.getElementById("fullName").value.trim();
      const email           = document.getElementById("email").value.trim().toLowerCase();
      const password        = document.getElementById("password").value;
      const confirmPassword = document.getElementById("confirmPassword").value;

      if (!fullName) { toast("Full name is required.", "error"); return; }
      if (!validateEmail(email)) { toast("Please enter a valid email.", "error"); return; }
      if (!validatePassword(password)) {
        toast("Password must be 8+ chars, include a number and uppercase letter.", "warn");
        return;
      }
      if (password !== confirmPassword) { toast("Passwords do not match!", "error"); return; }

      try {
        await publicFetch(`${API}/register`, {
          method: "POST",
          body: JSON.stringify({ fullName, email, password }),
        });
        toast("Account created! Redirecting to sign in…");
        setTimeout(() => { window.location.href = "signin.html"; }, 800);
      } catch (err) {
        toast("Registration failed: " + err.message, "error");
      }
    });
  }

  // ── FORGOT PASSWORD FORM ─────────────────
  const forgotPasswordForm = document.getElementById("forgotPasswordForm");
  if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const email = document.getElementById("email").value.trim().toLowerCase();
      if (!validateEmail(email)) { toast("Please enter a valid email.", "error"); return; }
      try {
        const res  = await publicFetch(`${API}/forgot_password`, {
          method: "POST",
          body: JSON.stringify({ email }),
        });
        const data = await res.json();
        toast(data.message || "If that email exists, a reset link has been sent.");
        if (data.reset_link) console.info("Reset link:", data.reset_link);
      } catch (err) {
        toast("Request failed: " + err.message, "error");
      }
    });
  }

  // ── RESET PASSWORD FORM ──────────────────
  const resetPasswordForm = document.getElementById("resetPasswordForm");
  if (resetPasswordForm) {
    resetPasswordForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const newPassword     = document.getElementById("newPassword").value;
      const confirmPassword = document.getElementById("confirmPassword").value;
      const token = new URLSearchParams(window.location.search).get("token");

      if (!token) { toast("Invalid or missing reset token.", "error"); return; }
      if (!validatePassword(newPassword)) {
        toast("Password must be 8+ chars, include a number and uppercase letter.", "warn");
        return;
      }
      if (newPassword !== confirmPassword) { toast("Passwords do not match!", "error"); return; }

      try {
        await publicFetch(`${API}/reset_password`, {
          method: "POST",
          body: JSON.stringify({ token, new_password: newPassword }),
        });
        toast("Password reset successful!");
        setTimeout(() => { window.location.href = "signin.html"; }, 800);
      } catch (err) {
        toast("Reset failed: " + err.message, "error");
      }
    });
  }

  // ── PROFILE FORM ─────────────────────────
  const profileForm = document.getElementById("profileForm");
  if (profileForm) {
    const fnEl = document.getElementById("fullName");
    const emEl = document.getElementById("email");
    if (fnEl) fnEl.value = localStorage.getItem("full_name")  || "";
    if (emEl) emEl.value = localStorage.getItem("user_email") || "";

    profileForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const full_name = document.getElementById("fullName").value.trim();
      const email     = document.getElementById("email").value.trim().toLowerCase();
      if (!full_name || !email) { toast("All fields are required.", "error"); return; }
      if (!validateEmail(email)) { toast("Invalid email address.", "error"); return; }
      try {
        await apiFetch(`${API}/update_profile`, {
          method: "POST",
          body: JSON.stringify({ full_name, email }),
        });
        localStorage.setItem("full_name",  full_name);
        localStorage.setItem("user_email", email);
        toast("Profile updated successfully!");
      } catch (err) {
        toast("Profile update failed: " + err.message, "error");
      }
    });
  }

  // ── HISTORY PAGE ─────────────────────────
  if (window.location.pathname.includes("history.html")) {
    loadUserHistory();
  }

});  // end DOMContentLoaded


// ────────────────────────────────────────────
// HISTORY LOADER
// ────────────────────────────────────────────
async function loadUserHistory() {
  const userId     = localStorage.getItem("user_id");
  const historyDiv = document.getElementById("history");
  if (!historyDiv || !userId) return;

  historyDiv.innerHTML = "<p style='color:#888'>Loading history…</p>";

  try {
    const res  = await apiFetch(`${API}/history/${userId}`);
    const data = await res.json();

    historyDiv.innerHTML = "<h3>Prediction History</h3>";

    if (!Array.isArray(data) || data.length === 0) {
      historyDiv.innerHTML += '<div class="result-box">No prediction history found.</div>';
      return;
    }

    data.forEach(function (entry) {
      const block = document.createElement("div");
      block.className = "result-box";
      block.innerHTML =
        `<strong>${formatUTCtoLocal(entry.created_at)}</strong><br/>` +
        `<b>Inputs:</b> N=${entry.nitrogen}, P=${entry.phosphorus}, K=${entry.potassium}, ` +
        `Temp=${entry.temperature}°C, Humidity=${entry.humidity}%, pH=${entry.ph}, Rainfall=${entry.rainfall} mm<br/>` +
        `<b>Recommended Crop:</b> <span style="color:#2b7a4b;font-weight:700">${entry.predicted_crop}</span><br/>` +
        `<b>Best Model:</b> ${entry.best_model || "—"}`;
      historyDiv.appendChild(block);
    });
  } catch (err) {
    historyDiv.innerHTML =
      `<div class="result-box" style="color:#c0392b">Error loading history: ${err.message}</div>`;
  }
}