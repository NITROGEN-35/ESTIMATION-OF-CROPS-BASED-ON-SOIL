// ================= Utility =================
function formatUTCtoLocal(utcString) {
  if (!utcString) return "";
  let dateString = utcString.includes("T")
    ? utcString
    : utcString.replace(" ", "T") + "Z";
  const date = new Date(dateString);
  return isNaN(date.getTime()) ? "Invalid Date" : date.toLocaleString();
}

// ================= Input Validation =================


const THRESHOLDS = {
  N: { min: 0, max: 140 },
  P: { min: 0, max: 145 },
  K: { min: 0, max: 205 },
  temperature: { min: 5, max: 45 },
  humidity: { min: 20, max: 100 },
  ph: { min: 3.5, max: 9.0 },
  rainfall: { min: 20, max: 300 }
};

function validateSoilInput(data) {
  const errors = [];
  const warnings = [];

  for (const key in THRESHOLDS) {
    const value = Number(data[key]);
    const { min, max } = THRESHOLDS[key];


    if (isNaN(value)) {
      errors.push(`${key} is not a number`);
      continue;
    }
    
    if (value < min || value > max) {
  warnings.push(
    `${key} is outside the recommended range (${min}–${max})`
  );
}
 else {
      // warning if close to boundary (10%)
      const range = max - min;
      if (value < min + range * 0.1 || value > max - range * 0.1) {
        warnings.push(
          `${key} is near its acceptable limit`
        );
      }
    }
  }

  return { errors, warnings };
}


// ================= Menu Functionality =================
const menuIcon = document.getElementById("menu-icon");
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");
const main = document.querySelector(".main");

function toggleMenu() {
  if (menuIcon && sidebar && main) {
    menuIcon.classList.toggle("active");
    sidebar.classList.toggle("hidden");
    main.classList.toggle("expanded");

    if (window.innerWidth <= 768 && overlay) {
      sidebar.classList.toggle("active");
      overlay.classList.toggle("active");
    }
  }
}

function closeMenu() {
  if (menuIcon && sidebar && overlay) {
    menuIcon.classList.remove("active");
    sidebar.classList.remove("active");
    overlay.classList.remove("active");

    if (window.innerWidth > 768 && main) {
      sidebar.classList.add("hidden");
      main.classList.add("expanded");
    }
  }
}

if (menuIcon) menuIcon.addEventListener("click", toggleMenu);
if (overlay) overlay.addEventListener("click", closeMenu);
if (sidebar) {
  sidebar.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeMenu);
  });
}

// ================= Crop Estimation =================
const soilForm = document.getElementById("soilForm");

if (soilForm) {
  soilForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const data = {
      N: parseFloat(document.getElementById("N").value),
      P: parseFloat(document.getElementById("P").value),
      K: parseFloat(document.getElementById("K").value),
      temperature: parseFloat(document.getElementById("temperature").value),
      humidity: parseFloat(document.getElementById("humidity").value),
      ph: parseFloat(document.getElementById("ph").value),
      rainfall: parseFloat(document.getElementById("rainfall").value),
    };

    const { errors, warnings } = validateSoilInput(data);

if (errors.length) {
  alert(errors.join("\n"));
  return; // ⛔ HARD STOP — Phase 2 compliant
}

if (warnings.length) {
  console.warn(warnings.join("\n"));
}


    

    fetch("http://127.0.0.1:5000/profile", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-User-Id": localStorage.getItem("user_id")
  },
  body: JSON.stringify({
    full_name: document.getElementById("fullName").value,
    email: document.getElementById("email").value
  })
})

      .then((res) => {
        if (!res.ok) throw new Error("Prediction request failed");
        return res.json();
      })
      .then((pred) => {
        const results = document.getElementById("results");

        results.innerHTML = `
          <h3>Recommended Crops</h3>
          <table class="results-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Prediction</th>
                <th>Accuracy (%)</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Random Forest</td><td>${pred.predictions.random_forest}</td><td>${pred.accuracies.random_forest}</td></tr>
              <tr><td>Decision Tree</td><td>${pred.predictions.decision_tree}</td><td>${pred.accuracies.decision_tree}</td></tr>
              <tr><td>SVM</td><td>${pred.predictions.svm}</td><td>${pred.accuracies.svm}</td></tr>
              <tr><td>Logistic Regression</td><td>${pred.predictions.logistic_regression}</td><td>${pred.accuracies.logistic_regression}</td></tr>
              <tr><td>KNN</td><td>${pred.predictions.knn}</td><td>${pred.accuracies.knn}</td></tr>
              <tr><td>Naive Bayes</td><td>${pred.predictions.naive_bayes}</td><td>${pred.accuracies.naive_bayes}</td></tr>
              <tr><td>Gradient Boost</td><td>${pred.predictions.gradient_boost}</td><td>${pred.accuracies.gradient_boost}</td></tr>
              <tr><td>AdaBoost</td><td>${pred.predictions.adaboost}</td><td>${pred.accuracies.adaboost}</td></tr>
            </tbody>
          </table>

          <div class="best-box">
            <strong>Recommended (Best Model: ${pred.best_model})</strong> :
            ${pred.recommended_crop}
          </div>
        `;

        // Local research history (NO USER, NO AUTH)
        let history = JSON.parse(localStorage.getItem("cropHistory")) || [];
        history.push({
          date: new Date().toISOString(),
          inputs: data,
          predictions: pred,
        });
        localStorage.setItem("cropHistory", JSON.stringify(history));
      })
      .catch((err) => {
        alert("❌ Prediction failed: " + err.message);
        console.error(err);
      });
  });
}

// ================= Local Prediction History =================
function showLocalStorageHistory() {
  const historyData = JSON.parse(localStorage.getItem("cropHistory")) || [];
  const historyDiv = document.getElementById("history");
  if (!historyDiv) return;

  historyDiv.innerHTML = "<h3>Prediction History</h3>";
  if (historyData.length === 0) {
    historyDiv.innerHTML += "<div>No history available.</div>";
    return;
  }

  historyData
    .slice(-10)
    .reverse()
    .forEach((entry) => {
      const block = document.createElement("div");
      block.className = "result-box";
      block.innerHTML = `
        <strong>${formatUTCtoLocal(entry.date)}</strong><br/>
        N=${entry.inputs.N}, P=${entry.inputs.P}, K=${entry.inputs.K},
        Temp=${entry.inputs.temperature}°C, Humidity=${entry.inputs.humidity}%,
        pH=${entry.inputs.ph}, Rainfall=${entry.inputs.rainfall} mm
      `;
      historyDiv.appendChild(block);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("history")) {
    showLocalStorageHistory();
  }
});

