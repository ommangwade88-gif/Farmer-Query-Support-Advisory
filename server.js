const express = require("express");
const path = require("path");
const cors = require("cors");
const { createProxyMiddleware } = require("http-proxy-middleware");

/**
 * Re-send JSON/urlencoded bodies after express.json() consumed the stream.
 * The stock fixRequestBody skips when `req.readableLength !== 0`; on many Node
 * versions readableLength is `undefined` after parsing, so `undefined !== 0`
 * is true and the proxy forwards an empty body (Flask then returns 400).
 */
function safeFixProxyBody(proxyReq, req) {
  const rl = req.readableLength;
  if (typeof rl === "number" && rl > 0) {
    return;
  }
  const requestBody = req.body;
  if (requestBody == null || typeof requestBody !== "object") {
    return;
  }
  const headerCt = proxyReq.getHeader("Content-Type") || req.headers["content-type"] || "";
  const ct = Array.isArray(headerCt) ? headerCt[0] : String(headerCt);
  const lower = ct.toLowerCase();

  if (lower.includes("multipart/form-data")) {
    return;
  }

  const writeJson = () => {
    const bodyData = JSON.stringify(requestBody);
    if (!proxyReq.getHeader("Content-Type")) {
      proxyReq.setHeader("Content-Type", "application/json; charset=utf-8");
    }
    proxyReq.setHeader("Content-Length", Buffer.byteLength(bodyData));
    proxyReq.write(bodyData);
  };

  if (lower.includes("application/json") || lower.includes("+json")) {
    writeJson();
    return;
  }

  if (req.method === "POST" && Object.keys(requestBody).length > 0) {
    writeJson();
  }
}

const PYTHON_URL = process.env.PYTHON_SERVICE_URL || "http://127.0.0.1:8000";
const PORT = Number(process.env.PORT) || 3000;

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(express.static(path.join(__dirname, "public")));

function advisoryAnswer(question) {
  const q = (question || "").toLowerCase();
  const tips = [];

  if (/rice|paddy|wheat|maize|corn|soy|cotton|pulse|millet|barley/.test(q)) {
    tips.push(
      "Match crop choice to soil pH, water availability, and the local sowing calendar. Use the Crop Recommendation tool for a data-backed shortlist."
    );
  }
  if (/pest|disease|yellow|spot|wilt|blight|fungus|insect/.test(q)) {
    tips.push(
      "Capture clear photos in natural light and use Crop Health for a quick visual check, then confirm with your local extension officer if symptoms persist."
    );
  }
  if (/rain|weather|drought|frost|temperature|humid/.test(q)) {
    tips.push(
      "Check the Local Weather panel before irrigation or spraying; avoid applying chemicals right before heavy rain."
    );
  }
  if (/yield|harvest|ton|quintal|production|output/.test(q)) {
    tips.push(
      "Yield depends on variety, spacing, nutrition, and water stress. Use Yield Prediction after you enter your field details for a planning estimate."
    );
  }
  if (/tool|equipment|tractor|tiller|sprayer|drip|mulch/.test(q)) {
    tips.push(
      "Tools Recommendation suggests implements that fit your crop and task—start there before buying new equipment."
    );
  }
  if (/soil|ph|nutrient|nitrogen|organic|compost|manure/.test(q)) {
    tips.push(
      "Test soil every season or two; balanced organic matter often improves both water retention and nutrient availability."
    );
  }
  if (!tips.length) {
    tips.push(
      "Describe your crop, location, soil type, and the problem (pests, weather, irrigation, or planning). The modules below can give targeted guidance."
    );
  }

  return {
    summary:
      "Here is practical guidance based on your question. This assistant uses rules and agronomy heuristics—not a live agronomist.",
    tips,
  };
}

app.post("/api/advisory", (req, res) => {
  const { question } = req.body || {};
  if (!question || typeof question !== "string") {
    return res.status(400).json({ error: "Field 'question' (string) is required." });
  }
  res.json(advisoryAnswer(question.trim()));
});

const pythonPaths = (pathname) =>
  pathname.startsWith("/api/crop-recommendation") ||
  pathname.startsWith("/api/yield-prediction") ||
  pathname.startsWith("/api/crop-health") ||
  pathname.startsWith("/api/tools-recommendation") ||
  pathname.startsWith("/api/weather");

app.use(
  createProxyMiddleware({
    target: PYTHON_URL,
    changeOrigin: true,
    filter: (pathname) => pythonPaths(pathname),
    on: {
      proxyReq: safeFixProxyBody,
      error: (err, _req, res) => {
        console.error("Python proxy error:", err.message);
        if (!res.headersSent) {
          res.status(502).json({
            error:
              "Python service is unreachable. In a terminal run: cd python-service && python main.py",
          });
        }
      },
    },
  })
);

app.get("*", (req, res) => {
  if (req.path.startsWith("/api")) {
    return res.status(404).json({ error: "Unknown API route." });
  }
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, () => {
  console.log(`Farmer Advisory UI: http://localhost:${PORT}`);
  console.log(`Proxying ML APIs to ${PYTHON_URL}`);
});
