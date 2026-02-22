// chart.js — complete file
// Handles calling /predict, rendering the model-votes chart,
// soil input chart, raw predictions table, and the Best Model card.

// ---------- Helper: humanize model key ----------
function formatModelName(key) {
  if (!key) return '';
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}


// ---------- Soil input validation ----------
function validateSoilInput(data) {
  const errors = [];
  const warnings = [];

  if (isNaN(data.N) || data.N < 0 || data.N > 200)
    errors.push('Nitrogen (N) must be between 0 and 200');
  if (isNaN(data.P) || data.P < 0 || data.P > 200)
    errors.push('Phosphorus (P) must be between 0 and 200');
  if (isNaN(data.K) || data.K < 0 || data.K > 200)
    errors.push('Potassium (K) must be between 0 and 200');
  if (isNaN(data.temperature) || data.temperature < -20 || data.temperature > 60)
    errors.push('Temperature must be between -20 and 60°C');
  if (isNaN(data.humidity) || data.humidity < 0 || data.humidity > 100)
    errors.push('Humidity must be between 0 and 100%');
  if (isNaN(data.ph) || data.ph < 0 || data.ph > 14)
    errors.push('pH must be between 0 and 14');
  if (isNaN(data.rainfall) || data.rainfall < 0 || data.rainfall > 500)
    errors.push('Rainfall must be between 0 and 500 mm');

  return { errors, warnings };
}

// ---------- Render raw predictions, charts ----------
function renderPredictionResults(resp) {
  if (!resp) return;

  // 1) Raw predictions table
  const tbody = document.querySelector('#predictionsTable tbody');
  if (tbody) {
    tbody.innerHTML = '';
    const predictions = resp.predictions || {};
    for (const [model, pred] of Object.entries(predictions)) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td style="padding:6px">${model}</td><td style="padding:6px">${pred}</td>`;
      tbody.appendChild(tr);
    }
  }

  // 2) Majority/recommended crop
  const majorityEl = document.getElementById('majorityResult');
  const majority = resp.recommended_crop || resp.best_crop || resp.bestCrop || resp.majority_crop || null;
  if (majorityEl) majorityEl.textContent = majority ? majority.toString().toUpperCase() : 'No consensus';

  // 3) Votes for crops (either resp.votes or compute from predictions)
  const votes = resp.votes ? { ...resp.votes } : {};
  if (!resp.votes) {
    const preds = resp.predictions || {};
    Object.values(preds).forEach(p => {
      if (!p || p === 'error') return;
      votes[p] = (votes[p] || 0) + 1;
    });
  }

  const cropLabels = Object.keys(votes);
  const cropValues = cropLabels.map(c => votes[c]);

  if (window.modelComparisonChartInstance) window.modelComparisonChartInstance.destroy();
  const cmpCanvas = document.getElementById('modelComparisonChart');
  if (cmpCanvas) {
    const ctx = cmpCanvas.getContext('2d');
    window.modelComparisonChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: cropLabels,
        datasets: [{
          label: 'Model votes',
          data: cropValues
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, precision: 0 } }
      }
    });
  }

  // 4) Soil data chart: use resp.input if provided, else read form fields
  let soilInput = resp.input || null;
  if (!soilInput) {
    soilInput = {
      N: Number(document.getElementById('N').value || 0),
      P: Number(document.getElementById('P').value || 0),
      K: Number(document.getElementById('K').value || 0),
      temperature: Number(document.getElementById('temperature').value || 0),
      humidity: Number(document.getElementById('humidity').value || 0),
      ph: Number(document.getElementById('ph').value || 0),
      rainfall: Number(document.getElementById('rainfall').value || 0)
    };
  }

  const soilLabels = Object.keys(soilInput || {});
  const soilVals = soilLabels.map(k => Number(soilInput[k] || 0));

  if (window.soilDataChartInstance) window.soilDataChartInstance.destroy();
  const soilCanvas = document.getElementById('soilDataChart');
  if (soilCanvas && soilLabels.length) {
    const ctx2 = soilCanvas.getContext('2d');
    window.soilDataChartInstance = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: soilLabels,
        datasets: [{
          label: 'Soil values',
          data: soilVals
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  // update summary results area if present
  const resultsDiv = document.getElementById('results');
  if (resultsDiv) {
    const rec = majority || (resp.recommended_crop || resp.best_crop || '—');
    resultsDiv.innerHTML = `<p>Recommended crop (majority vote): <strong>${(rec || '—').toString().toUpperCase()}</strong></p>`;
  }
}

// ---------- Best-model card rendering ----------
function renderBestModelCard(resp) {
  // best model reported by backend (string key), and recommended crop
  const bestModelKey = resp.best_model || resp.bestModel || resp.best_model_name || Object.keys(resp.predictions || {})[0];
  const recommendedCrop = resp.recommended_crop || resp.best_crop || resp.recommended || '—';

  // Pick percent from model_metrics or accuracies if available
  let percent = null;
  if (resp.model_metrics && resp.model_metrics[bestModelKey] && resp.model_metrics[bestModelKey].accuracy) {
    percent = Number(resp.model_metrics[bestModelKey].accuracy);
  } else if (resp.accuracies && resp.accuracies[bestModelKey]) {
    percent = Number(resp.accuracies[bestModelKey]);
  } else if (resp.accuracy && typeof resp.accuracy === 'number') {
    percent = Number(resp.accuracy);
  }

  if (percent === null || Number.isNaN(percent)) percent = 0;

  const pEl = document.getElementById('best-percent');
  const nameEl = document.getElementById('best-model-name');
  const srcEl = document.getElementById('best-model-source');

  if (pEl) pEl.textContent = `${percent.toFixed(0)}%`;
  if (nameEl) nameEl.textContent = (recommendedCrop || '—').toString().toUpperCase();
  if (srcEl) srcEl.textContent = formatModelName(bestModelKey || '—');

  const badge = document.getElementById('best-model-badge');
  if (badge) {
    badge.style.borderColor = percent >= 90 ? '#1b6a3e44' : '#2b7a4b33';
  }
}

// ---------- Toggle and button handlers (robust to different DOM layouts) ----------
document.addEventListener('click', function (e) {
  if (e.target && e.target.id === 'moreInfoBtn') {
    // Try to find a recommended crops container; fallback to predictions table parent
    let box = document.querySelector('#recommendedSection') || document.querySelector('.recommended-table-wrapper') || document.querySelector('#recommended-crops') || document.querySelector('.recommended-table');

    if (!box) {
      // find the green table by heading name "Recommended" and toggle the next element after heading
      const hdrs = Array.from(document.querySelectorAll('h3, h4'));
      const heading = hdrs.find(h => h.textContent && h.textContent.toLowerCase().includes('recommended'));
      if (heading) box = heading.nextElementSibling;
    }

    if (box) {
      box.classList.toggle('hidden');
      e.target.textContent = box.classList.contains('hidden') ? 'More info' : 'Less info';
    } else {
      // fallback: toggle the raw predictions table visibility
      const t = document.getElementById('predictionsTable');
      if (t) {
        t.parentElement.classList.toggle('hidden');
        e.target.textContent = t.parentElement.classList.contains('hidden') ? 'More info' : 'Less info';
      }
    }
  }

  if (e.target && e.target.id === 'compareBtn') {
    // placeholder/hook for future per-model probability compare
    alert('Compare: will show per-model confidence/probability (coming soon).');
  }
});

// ---------- Send predict request ----------
async function sendPredictRequest(body) {
  try {
    const res = await apiFetch('http://127.0.0.1:5000/predict', {
      method: 'POST',
      body: JSON.stringify(body)
    });

    const json = await res.json();
    json.input = body;

    renderPredictionResults(json);
    renderBestModelCard(json);

  } catch (err) {
    console.error('Network error predicting', err);
  }
}

// ---------- Hook the soil form submit ----------
document.addEventListener('DOMContentLoaded', function () {
  const soilForm = document.getElementById('soilForm');
  if (soilForm) {
    soilForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const body = {
        N: Number(document.getElementById('N').value),
        P: Number(document.getElementById('P').value),
        K: Number(document.getElementById('K').value),
        temperature: Number(document.getElementById('temperature').value),
        humidity: Number(document.getElementById('humidity').value),
        ph: Number(document.getElementById('ph').value),
        rainfall: Number(document.getElementById('rainfall').value)
      };
      const { errors, warnings } = validateSoilInput(body);

      if (errors.length > 0) {
        alert(
          "Invalid input:\n" + errors.join("\n")
        );
        return; // ⛔ STOP here, no ML call
      }

      if (warnings.length > 0) {
        console.warn("Threshold warnings:", warnings);
        // Optional UI message
        alert(
          "Warning:\n" + warnings.join("\n") +
          "\n\nPrediction will continue for analysis."
        );
      }

      // ✅ Safe to predict
      sendPredictRequest(body);

    });
  }
});