const toastEl = document.getElementById("toast");

function showToast(message, isError = false) {
  toastEl.textContent = message;
  toastEl.classList.toggle("hidden", false);
  toastEl.style.background = isError ? "#7f1d1d" : "#0f172a";
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toastEl.classList.add("hidden"), 4200);
}

function setResult(box, html) {
  box.innerHTML = html;
  box.classList.remove("hidden");
}

function escapeHtml(str) {
  return str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderJson(obj) {
  return `<pre>${escapeHtml(JSON.stringify(obj, null, 2))}</pre>`;
}

function renderYield(data) {
  if (!data || typeof data !== "object") return renderJson(data);
  const perAcre = data.estimated_yield_quintals_per_acre;
  const totalQ = data.estimated_total_quintals;
  const totalT = data.estimated_total_metric_tonnes;
  const disc = data.disclaimer || "";
  return `<p><strong>${escapeHtml(String(perAcre ?? "—"))}</strong> quintals per acre (planning estimate)</p>
    <p>Total: <strong>${escapeHtml(String(totalQ ?? "—"))}</strong> quintals (~<strong>${escapeHtml(
      String(totalT ?? "—")
    )}</strong> metric tonnes)</p>
    <p class="muted small">${escapeHtml(disc)}</p>
    <details class="muted small" style="margin-top:0.5rem"><summary>Raw JSON</summary>${renderJson(data)}</details>`;
}

function renderCropList(rows) {
  if (!Array.isArray(rows)) return renderJson(rows);
  const items = rows
    .map(
      (r) =>
        `<li><strong>${escapeHtml(r.crop)}</strong> — score ${escapeHtml(
          String(r.score)
        )}<br/><span class="muted small">${escapeHtml(r.rationale)}</span></li>`
    )
    .join("");
  return `<ol class="stack tight" style="margin:0;padding-left:1.1rem">${items}</ol>`;
}

function renderTools(data) {
  const list = (data.recommended_tools || [])
    .map((t) => `<li>${escapeHtml(t)}</li>`)
    .join("");
  return `<p class="muted small">${escapeHtml(data.crop)} · ${escapeHtml(
    data.primary_task
  )}</p><ul style="margin:0.35rem 0 0;padding-left:1.1rem">${list}</ul>`;
}

function renderWeather(data) {
  const rows = (data.daily || [])
    .map(
      (d) =>
        `<tr><td>${escapeHtml(d.date || "")}</td><td>${escapeHtml(
          d.temp_min_c != null ? `${d.temp_min_c}–${d.temp_max_c} °C` : "—"
        )}</td><td>${escapeHtml(
          d.precipitation_mm != null ? `${d.precipitation_mm} mm` : "—"
        )}</td><td>${escapeHtml(
          d.precip_probability_pct != null ? `${d.precip_probability_pct}%` : "—"
        )}</td></tr>`
    )
    .join("");
  return `<p class="muted small">${escapeHtml(data.source || "")}</p>
    <table class="weather-table"><thead><tr><th>Date</th><th>Temp</th><th>Rain</th><th>Rain prob.</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderHealth(data) {
  const notes = (data.notes || []).map((n) => `<li>${escapeHtml(n)}</li>`).join("");
  const m = data.metrics || {};
  return `<p><strong>${escapeHtml(data.verdict || "")}</strong> (score ${escapeHtml(
    String(data.health_score ?? "")
  )})</p>
    <ul style="margin:0.35rem 0 0;padding-left:1.1rem">${notes}</ul>
    <p class="muted small" style="margin-top:0.5rem">Metrics: greenness ${escapeHtml(
      String(m.greenness_index ?? "")
    )}, stress ${escapeHtml(String(m.stress_red_index ?? ""))}, brightness ${escapeHtml(
    String(m.mean_brightness ?? "")
  )}, contrast ${escapeHtml(String(m.texture_contrast ?? ""))}</p>`;
}

function renderAdvisory(data) {
  const tips = (data.tips || []).map((t) => `<li>${escapeHtml(t)}</li>`).join("");
  return `<p>${escapeHtml(data.summary || "")}</p><ul style="margin:0.5rem 0 0;padding-left:1.1rem">${tips}</ul>`;
}

function apiErrorMessage(data, fallback) {
  const detail = data.detail;
  const detailMsg =
    typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((d) => d.msg || d.message || JSON.stringify(d)).join("; ")
        : "";
  return detailMsg || data.error || fallback;
}

document.getElementById("query-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const textarea = document.getElementById("query-text");
  const box = document.getElementById("query-result");
  const question = textarea.value.trim();
  try {
    const res = await fetch("/api/advisory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(apiErrorMessage(data, res.statusText));
    setResult(box, renderAdvisory(data));
  } catch (err) {
    showToast(err.message || "Advisory request failed", true);
  }
});

const STRING_FORM_FIELDS = new Set([
  "crop",
  "soil_type",
  "season",
  "irrigation",
  "fertilizer_level",
  "primary_task",
  "region_hint",
]);

function formDataToJson(form) {
  const obj = {};
  const fd = new FormData(form);
  for (const [k, v] of fd.entries()) {
    if (v === "") continue;
    if (typeof v !== "string") continue;
    if (STRING_FORM_FIELDS.has(k)) {
      obj[k] = v;
      continue;
    }
    const num = Number(v);
    obj[k] = Number.isFinite(num) && String(v).trim() !== "" ? num : v;
  }
  return obj;
}

document.querySelectorAll("form[data-endpoint]").forEach((form) => {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const endpoint = form.getAttribute("data-endpoint");
    const multipart = form.hasAttribute("data-multipart");
    const box = form.parentElement?.querySelector("[data-result]");
    if (!box) return;

    try {
      let res;
      if (multipart) {
        const fd = new FormData();
        const fileInput = form.querySelector('input[type="file"]');
        if (!fileInput?.files?.length) {
          showToast("Choose an image first.", true);
          return;
        }
        fd.append("file", fileInput.files[0]);
        res = await fetch(endpoint, { method: "POST", body: fd });
      } else {
        const payload = formDataToJson(form);
        res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(apiErrorMessage(data, res.statusText));

      if (endpoint.includes("crop-recommendation")) setResult(box, renderCropList(data));
      else if (endpoint.includes("yield-prediction")) setResult(box, renderYield(data));
      else if (endpoint.includes("tools-recommendation")) setResult(box, renderTools(data));
      else if (endpoint.includes("weather")) setResult(box, renderWeather(data));
      else if (endpoint.includes("crop-health")) setResult(box, renderHealth(data));
      else setResult(box, renderJson(data));

      showToast("Updated");
    } catch (err) {
      showToast(err.message || "Request failed", true);
    }
  });
});
