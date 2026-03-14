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
// Layer 1: Hard stop — absolute dataset bounds
const THRESHOLDS = {
  N:           { min: 0,   max: 140 },
  P:           { min: 0,   max: 145 },
  K:           { min: 0,   max: 205 },
  temperature: { min: 5,   max: 45  },
  humidity:    { min: 20,  max: 100 },
  ph:          { min: 3.5, max: 9.0 },
  rainfall:    { min: 20,  max: 300 }
};

function validateSoilInput(data) {
  const errors   = [];
  const warnings = [];

  for (const key in THRESHOLDS) {
    const value    = Number(data[key]);
    const { min, max } = THRESHOLDS[key];

    if (isNaN(value)) {
      errors.push(`${key} is not a valid number`);
      continue;
    }
    if (value < min || value > max) {
      errors.push(`${key} must be between ${min} and ${max} (got ${value})`);
    } else {
      // warn if within 10% of boundary
      const range = max - min;
      if (value < min + range * 0.1 || value > max - range * 0.1) {
        warnings.push(`${key} (${value}) is near its acceptable limit`);
      }
    }
  }

  return { errors, warnings };
}

// ================= Menu Functionality =================
const menuIcon = document.getElementById("menu-icon");
const sidebar  = document.getElementById("sidebar");
const overlay  = document.getElementById("overlay");
const main     = document.querySelector(".main");

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
if (overlay)  overlay.addEventListener("click", closeMenu);
if (sidebar)  sidebar.querySelectorAll("a").forEach(l => l.addEventListener("click", closeMenu));

// ================= Render Threshold Warnings =================
function renderThresholdWarnings(pred) {
  // Remove any previous warning box
  const old = document.getElementById("thresholdWarningBox");
  if (old) old.remove();

  if (!pred.threshold_warnings || pred.threshold_warnings.length === 0) return;

  const box = document.createElement("div");
  box.id = "thresholdWarningBox";
  box.style.cssText = `
    background:#fff8e1; border:1px solid #f9a825; border-radius:10px;
    padding:12px 18px; margin-bottom:16px; color:#7a5400;
  `;
  box.innerHTML = `
    <strong>⚠️ Input Warning (${pred.threshold_warnings.length} issue${pred.threshold_warnings.length > 1 ? 's' : ''})</strong>
    <ul style="margin:8px 0 0 18px; font-size:14px;">
      ${pred.threshold_warnings.map(w => `<li>${w}</li>`).join("")}
    </ul>
    <small>Confidence penalty applied: −${pred.confidence_penalty || 0}%</small>
  `;

  const results = document.getElementById("results");
  if (results) results.insertAdjacentElement("beforebegin", box);
}

// ================= Render Top-3 Crop Alternatives =================
function renderTop3Crops(pred) {
  const top3 = pred.top3_crops;
  if (!top3 || top3.length === 0) return "";

  return `
    <div style="margin-top:18px;">
      <h4 style="color:#0b7c43; margin-bottom:10px;">🌾 Top 3 Crop Alternatives (Random Forest)</h4>
      <div style="display:flex; gap:12px; flex-wrap:wrap;">
        ${top3.map((c, i) => `
          <div style="
            flex:1; min-width:140px; background:${i === 0 ? '#e8f5e9' : '#f5f5f5'};
            border-radius:10px; padding:14px; text-align:center;
            border: 1px solid ${i === 0 ? '#a5d6a7' : '#e0e0e0'};
          ">
            <div style="font-size:22px;">${i === 0 ? '🥇' : i === 1 ? '🥈' : '🥉'}</div>
            <div style="font-weight:700; font-size:16px; margin-top:6px;">${c.crop.toUpperCase()}</div>
            <div style="font-size:13px; color:#555; margin-top:4px;">Confidence: <strong>${c.probability}%</strong></div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

// ================= Render Confidence Scores Column =================
function buildResultsTable(pred) {
  const rows = [
    ["Random Forest",      "random_forest"],
    ["Decision Tree",      "decision_tree"],
    ["SVM",                "svm"],
    ["Logistic Regression","logistic_regression"],
    ["KNN",                "knn"],
    ["Naive Bayes",        "naive_bayes"],
    ["Gradient Boost",     "gradient_boost"],
    ["AdaBoost",           "adaboost"],
  ];

  const tbody = rows.map(([label, key]) => {
    const crop       = pred.predictions[key] || "—";
    const accuracy   = pred.accuracies[key]  || "—";
    const confidence = pred.confidence_scores && pred.confidence_scores[key] != null
      ? pred.confidence_scores[key] + "%"
      : "—";
    const isBest = key === pred.best_model;

    return `<tr style="${isBest ? 'background:#e8f5e9; font-weight:700;' : ''}">
      <td>${label} ${isBest ? '⭐' : ''}</td>
      <td>${crop}</td>
      <td>${accuracy}%</td>
      <td>${confidence}</td>
    </tr>`;
  }).join("");

  return `
    <h3>Recommended Crops</h3>
    <table class="results-table">
      <thead>
        <tr>
          <th>Model</th>
          <th>Prediction</th>
          <th>Accuracy (%)</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>${tbody}</tbody>
    </table>

    <div class="best-box" style="margin-top:16px; padding:14px; background:#e8f5e9; border-radius:10px;">
      <strong>✅ Recommended (Best Model: ${pred.best_model.replace(/_/g, " ")})</strong>:
      ${pred.recommended_crop.toUpperCase()}
      ${pred.confidence_scores && pred.confidence_scores[pred.best_model] != null
        ? ` — <span style="color:#0b7c43;">${pred.confidence_scores[pred.best_model]}% confident</span>`
        : ""}
    </div>

    ${renderTop3Crops(pred)}
  `;
}

// ================= Crop Estimation Form =================
const soilForm = document.getElementById("soilForm");

if (soilForm) {
  soilForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const data = {
      N:           parseFloat(document.getElementById("N").value),
      P:           parseFloat(document.getElementById("P").value),
      K:           parseFloat(document.getElementById("K").value),
      temperature: parseFloat(document.getElementById("temperature").value),
      humidity:    parseFloat(document.getElementById("humidity").value),
      ph:          parseFloat(document.getElementById("ph").value),
      rainfall:    parseFloat(document.getElementById("rainfall").value),
    };

    // ⛔ Layer 1: Frontend hard-stop validation
    const { errors, warnings } = validateSoilInput(data);

    if (errors.length) {
      alert("❌ Invalid input:\n\n" + errors.join("\n"));
      return;
    }

    if (warnings.length) {
      console.warn("Input warnings:", warnings.join("\n"));
      // Non-blocking: show in console only (backend will also warn)
    }

    // ✅ Send to backend
    fetch("http://127.0.0.1:5000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then(res => {
        if (!res.ok) throw new Error("Prediction request failed");
        return res.json();
      })
      .then(pred => {
        const results = document.getElementById("results");

        // Render threshold warnings (Layer 2 feedback)
        renderThresholdWarnings(pred);

        // Render results table with confidence column + top-3
        results.innerHTML = buildResultsTable(pred);

        // Save to localStorage history
        let history = JSON.parse(localStorage.getItem("cropHistory")) || [];
        history.push({
          date: new Date().toISOString(),
          inputs: data,
          predictions: pred,
        });
        localStorage.setItem("cropHistory", JSON.stringify(history));
      })
      .catch(err => {
        alert("❌ Prediction failed: " + err.message);
        console.error(err);
      });
  });
}

// ================= Local Prediction History =================
function showLocalStorageHistory() {
  const historyData = JSON.parse(localStorage.getItem("cropHistory")) || [];
  const historyDiv  = document.getElementById("history");
  if (!historyDiv) return;

  historyDiv.innerHTML = "<h3>Prediction History</h3>";
  if (historyData.length === 0) {
    historyDiv.innerHTML += "<div>No history available.</div>";
    return;
  }

  historyData
    .slice(-10)
    .reverse()
    .forEach(entry => {
      const block = document.createElement("div");
      block.className = "result-box";
      const rec = entry.predictions?.recommended_crop || "—";
      block.innerHTML = `
        <strong>${formatUTCtoLocal(entry.date)}</strong><br/>
        N=${entry.inputs.N}, P=${entry.inputs.P}, K=${entry.inputs.K},
        Temp=${entry.inputs.temperature}°C, Humidity=${entry.inputs.humidity}%,
        pH=${entry.inputs.ph}, Rainfall=${entry.inputs.rainfall} mm
        <br/><em>→ Recommended: <strong>${rec.toUpperCase()}</strong></em>
      `;
      historyDiv.appendChild(block);
    });
}

if (window.location.pathname.includes("history.html")) {
  showLocalStorageHistory();
}