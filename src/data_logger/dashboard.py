DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Data Logger Dashboard</title>
  <style>
    :root {
      color-scheme: light dark;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    body {
      margin: 0;
      background: #101827;
      color: #eef2ff;
    }

    main {
      box-sizing: border-box;
      display: grid;
      gap: 1rem;
      margin: 0 auto;
      max-width: 1200px;
      min-height: 100vh;
      padding: 1.5rem;
    }

    header,
    section {
      background: #172033;
      border: 1px solid #28364f;
      border-radius: 16px;
      box-shadow: 0 16px 50px rgb(0 0 0 / 24%);
      padding: 1rem;
    }

    h1 {
      margin: 0 0 0.25rem;
    }

    p {
      color: #b8c4dd;
      margin: 0;
    }

    .controls {
      align-items: end;
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-top: 1rem;
    }

    label {
      display: grid;
      gap: 0.35rem;
      min-width: 12rem;
    }

    select,
    button {
      background: #0d1424;
      border: 1px solid #3a4b6a;
      border-radius: 10px;
      color: #eef2ff;
      font: inherit;
      padding: 0.6rem 0.75rem;
    }

    button {
      cursor: pointer;
    }

    button:hover {
      border-color: #7aa2ff;
    }

    canvas {
      background: #0d1424;
      border-radius: 12px;
      display: block;
      height: 520px;
      width: 100%;
    }

    .status {
      color: #b8c4dd;
      min-height: 1.5rem;
    }

    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-top: 0.75rem;
    }

    .legend-item {
      align-items: center;
      color: #d8e0f5;
      display: inline-flex;
      gap: 0.35rem;
    }

    .swatch {
      border-radius: 999px;
      display: inline-block;
      height: 0.75rem;
      width: 0.75rem;
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Data Logger Dashboard</h1>
      <p>Plotting measurements over time for every sensor in a selected source.</p>
      <div class="controls">
        <label>
          Source
          <select id="sourceSelect"></select>
        </label>
        <label>
          Value
          <select id="metricSelect">
            <option value="v_out" selected>Voltage (v_out)</option>
            <option value="adc">ADC</option>
          </select>
        </label>
        <label>
          Time range
          <select id="rangeSelect">
            <option value="1h">1 hour</option>
            <option value="1d">1 day</option>
            <option value="1w">1 week</option>
            <option value="1m">1 month</option>
          </select>
        </label>
        <button id="refreshButton" type="button">Refresh</button>
      </div>
    </header>
    <section>
      <div id="status" class="status">Loading sources…</div>
      <canvas id="chart" width="1100" height="520"></canvas>
      <div id="legend" class="legend"></div>
    </section>
  </main>

  <script>
    const sourceSelect = document.querySelector("#sourceSelect");
    const metricSelect = document.querySelector("#metricSelect");
    const rangeSelect = document.querySelector("#rangeSelect");
    const refreshButton = document.querySelector("#refreshButton");
    const statusEl = document.querySelector("#status");
    const legendEl = document.querySelector("#legend");
    const canvas = document.querySelector("#chart");
    const ctx = canvas.getContext("2d");
    const colors = ["#7aa2ff", "#7ef0c1", "#f7c66f", "#f08ab3", "#b69cff", "#ff8f70"];

    async function fetchJson(url) {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      return response.json();
    }

    function groupBySensor(measurements) {
      return measurements.reduce((groups, measurement) => {
        groups[measurement.sensor] ??= [];
        groups[measurement.sensor].push(measurement);
        return groups;
      }, {});
    }

    function formatTime(unixtimeMs) {
      return new Date(unixtimeMs).toLocaleString();
    }

    function drawEmpty(message) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#b8c4dd";
      ctx.font = "18px system-ui";
      ctx.fillText(message, 32, 56);
      legendEl.replaceChildren();
    }

    function getMetricLabel(metric) {
      return metric === "adc" ? "ADC" : "v_out";
    }

    function drawChart(measurements) {
      const metric = metricSelect.value;
      if (measurements.length === 0) {
        drawEmpty("No measurements found for this source and time range.");
        return;
      }

      const grouped = groupBySensor(measurements);
      const allTimes = measurements.map((measurement) => measurement.unixtime_ms);
      const allValues = measurements.map((measurement) => measurement[metric]);
      const minTime = Math.min(...allTimes);
      const maxTime = Math.max(...allTimes);
      const minValue = Math.min(...allValues);
      const maxValue = Math.max(...allValues);
      const timeSpan = Math.max(maxTime - minTime, 1);
      const valueSpan = Math.max(maxValue - minValue, 1);
      const padding = { top: 24, right: 28, bottom: 64, left: 72 };
      const width = canvas.width - padding.left - padding.right;
      const height = canvas.height - padding.top - padding.bottom;

      const xFor = (unixtimeMs) => padding.left + ((unixtimeMs - minTime) / timeSpan) * width;
      const yFor = (value) => padding.top + height - ((value - minValue) / valueSpan) * height;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "#33435f";
      ctx.fillStyle = "#b8c4dd";
      ctx.lineWidth = 1;
      ctx.font = "13px system-ui";

      for (let index = 0; index <= 4; index += 1) {
        const y = padding.top + (height / 4) * index;
        const value = maxValue - (valueSpan / 4) * index;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + width, y);
        ctx.stroke();
        ctx.fillText(metric === "adc" ? value.toFixed(0) : value.toFixed(3), 12, y + 4);
      }

      ctx.strokeStyle = "#7282a3";
      ctx.beginPath();
      ctx.moveTo(padding.left, padding.top);
      ctx.lineTo(padding.left, padding.top + height);
      ctx.lineTo(padding.left + width, padding.top + height);
      ctx.stroke();

      ctx.fillText(formatTime(minTime), padding.left, canvas.height - 24);
      ctx.fillText(formatTime(maxTime), Math.max(padding.left, canvas.width - 260), canvas.height - 24);
      ctx.fillText(getMetricLabel(metric), 12, 20);

      Object.entries(grouped).forEach(([sensor, points], index) => {
        const color = colors[index % colors.length];
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();

        points.forEach((point, pointIndex) => {
          const x = xFor(point.unixtime_ms);
          const y = yFor(point[metric]);
          if (pointIndex === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        });

        ctx.stroke();

        points.forEach((point) => {
          ctx.beginPath();
          ctx.arc(xFor(point.unixtime_ms), yFor(point[metric]), 3, 0, Math.PI * 2);
          ctx.fill();
        });
      });

      legendEl.replaceChildren(
        ...Object.keys(grouped).map((sensor, index) => {
          const item = document.createElement("span");
          const swatch = document.createElement("span");
          swatch.className = "swatch";
          swatch.style.background = colors[index % colors.length];
          item.className = "legend-item";
          item.append(swatch, sensor);
          return item;
        })
      );
    }

    async function loadSources() {
      const sources = await fetchJson("/api/sources");
      sourceSelect.replaceChildren(
        ...sources.map((source) => {
          const option = document.createElement("option");
          option.value = source;
          option.textContent = source;
          return option;
        })
      );

      if (sources.length === 0) {
        drawEmpty("No sources yet. POST measurements first, then refresh.");
        statusEl.textContent = "No sources found.";
        return;
      }

      await loadMeasurements();
    }

    async function loadMeasurements() {
      const source = sourceSelect.value;
      const range = rangeSelect.value;
      if (!source) {
        return;
      }

      statusEl.textContent = "Loading measurements…";
      const params = new URLSearchParams({ source, range });
      const measurements = await fetchJson(`/api/measurements?${params}`);
      drawChart(measurements);
      statusEl.textContent = `${measurements.length} measurements loaded.`;
    }

    refreshButton.addEventListener("click", () => loadMeasurements().catch(showError));
    sourceSelect.addEventListener("change", () => loadMeasurements().catch(showError));
    metricSelect.addEventListener("change", () => loadMeasurements().catch(showError));
    rangeSelect.addEventListener("change", () => loadMeasurements().catch(showError));

    function showError(error) {
      console.error(error);
      statusEl.textContent = "Something went wrong loading measurements.";
      drawEmpty("Could not load data. Check the API logs.");
    }

    loadSources().catch(showError);
  </script>
</body>
</html>
"""
