// ================= AUTH GUARD =================

const userId = localStorage.getItem("user_id");
const isAdmin = localStorage.getItem("is_admin");

const publicPages = ["signin.html", "indexl.html", "index.html"];
const currentPage = window.location.pathname.split("/").pop();

if (!userId && !publicPages.includes(currentPage)) {
  window.location.href = "signin.html";
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".admin-link").forEach(link => {
    if (isAdmin !== "1") link.style.display = "none";
  });
});

function logout() {
  localStorage.clear();
  window.location.href = "signin.html";
}

if (currentPage === "admin.html" && isAdmin !== "1") {
  window.location.href = "dashboard.html";
}
