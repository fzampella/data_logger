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
    input,
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

    .danger {
      border-color: #7f3348;
    }

    .danger h2 {
      margin: 0 0 0.25rem;
    }

    .danger button {
      border-color: #b9475f;
      color: #ffd7df;
    }

    .danger button:hover {
      border-color: #ff6f8f;
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

    .sensor-filter {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin: 0.75rem 0;
    }

    .sensor-filter label {
      align-items: center;
      background: #0d1424;
      border: 1px solid #3a4b6a;
      border-radius: 999px;
      display: inline-flex;
      gap: 0.4rem;
      min-width: 0;
      padding: 0.35rem 0.7rem;
    }

    .sensor-filter input {
      margin: 0;
      padding: 0;
    }

    .chart-wrap {
      position: relative;
    }

    .tooltip {
      background: rgb(13 20 36 / 94%);
      border: 1px solid #7aa2ff;
      border-radius: 10px;
      box-shadow: 0 12px 32px rgb(0 0 0 / 35%);
      color: #eef2ff;
      display: none;
      font-size: 0.85rem;
      line-height: 1.35;
      max-width: 18rem;
      padding: 0.6rem 0.7rem;
      pointer-events: none;
      position: absolute;
      z-index: 2;
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
      <div id="sensorFilter" class="sensor-filter"></div>
      <div class="chart-wrap">
        <canvas id="chart" width="1100" height="520"></canvas>
        <div id="tooltip" class="tooltip"></div>
      </div>
      <div id="legend" class="legend"></div>
    </section>
    <section class="danger">
      <h2>Delete Measurements</h2>
      <p>Delete one sensor from the selected source over a time period. This cannot be undone.</p>
      <div class="controls">
        <label>
          Sensor
          <select id="deleteSensorSelect"></select>
        </label>
        <label>
          Start time
          <input id="deleteStartInput" type="datetime-local">
        </label>
        <label>
          End time
          <input id="deleteEndInput" type="datetime-local">
        </label>
        <label>
          Delete password
          <input id="deletePasswordInput" type="password" autocomplete="current-password">
        </label>
        <button id="deleteButton" type="button">Delete Data</button>
      </div>
    </section>
  </main>

  <script>
    const sourceSelect = document.querySelector("#sourceSelect");
    const metricSelect = document.querySelector("#metricSelect");
    const rangeSelect = document.querySelector("#rangeSelect");
    const refreshButton = document.querySelector("#refreshButton");
    const deleteSensorSelect = document.querySelector("#deleteSensorSelect");
    const deleteStartInput = document.querySelector("#deleteStartInput");
    const deleteEndInput = document.querySelector("#deleteEndInput");
    const deletePasswordInput = document.querySelector("#deletePasswordInput");
    const deleteButton = document.querySelector("#deleteButton");
    const statusEl = document.querySelector("#status");
    const sensorFilterEl = document.querySelector("#sensorFilter");
    const legendEl = document.querySelector("#legend");
    const canvas = document.querySelector("#chart");
    const tooltipEl = document.querySelector("#tooltip");
    const ctx = canvas.getContext("2d");
    const colors = ["#7aa2ff", "#7ef0c1", "#f7c66f", "#f08ab3", "#b69cff", "#ff8f70"];
    let currentMeasurements = [];
    let selectedSensors = new Set();
    let chartPoints = [];

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

    function toDateTimeLocalValue(unixtimeMs) {
      const date = new Date(unixtimeMs);
      const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
      return localDate.toISOString().slice(0, 16);
    }

    function fromDateTimeLocalValue(value) {
      return new Date(value).getTime();
    }

    function drawEmpty(message) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#b8c4dd";
      ctx.font = "18px system-ui";
      ctx.fillText(message, 32, 56);
      legendEl.replaceChildren();
      chartPoints = [];
      hideTooltip();
    }

    function getSensors(measurements) {
      return [...new Set(measurements.map((measurement) => measurement.sensor))].sort();
    }

    function getSelectedMeasurements() {
      return currentMeasurements.filter((measurement) => selectedSensors.has(measurement.sensor));
    }

    function updateSensorFilter(measurements) {
      const sensors = getSensors(measurements);
      const previousSelection = selectedSensors;
      selectedSensors = new Set(
        sensors.filter((sensor) => previousSelection.size === 0 || previousSelection.has(sensor))
      );

      if (selectedSensors.size === 0 && sensors.length > 0) {
        selectedSensors = new Set(sensors);
      }

      sensorFilterEl.replaceChildren(
        ...sensors.map((sensor) => {
          const label = document.createElement("label");
          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.value = sensor;
          checkbox.checked = selectedSensors.has(sensor);
          checkbox.addEventListener("change", () => {
            if (checkbox.checked) {
              selectedSensors.add(sensor);
            } else {
              selectedSensors.delete(sensor);
            }
            drawChart(getSelectedMeasurements());
            statusEl.textContent = `${getSelectedMeasurements().length} of ${currentMeasurements.length} measurements displayed.`;
          });
          label.append(checkbox, sensor);
          return label;
        })
      );
    }

    function updateDeleteControls(measurements) {
      const sensors = getSensors(measurements);
      deleteSensorSelect.replaceChildren(
        ...sensors.map((sensor) => {
          const option = document.createElement("option");
          option.value = sensor;
          option.textContent = sensor;
          return option;
        })
      );

      deleteButton.disabled = sensors.length === 0;

      if (measurements.length === 0) {
        deleteStartInput.value = "";
        deleteEndInput.value = "";
        return;
      }

      const times = measurements.map((measurement) => measurement.unixtime_ms);
      deleteStartInput.value = toDateTimeLocalValue(Math.min(...times));
      deleteEndInput.value = toDateTimeLocalValue(Math.max(...times));
    }

    function getMetricLabel(metric) {
      return metric === "adc" ? "ADC" : "v_out";
    }

    function getValueBounds(values) {
      const rawMin = Math.min(...values);
      const rawMax = Math.max(...values);

      if (rawMin === rawMax) {
        const padding = rawMin === 0 ? 1 : Math.abs(rawMin) * 0.05;
        return {
          min: rawMin - padding,
          max: rawMax + padding,
        };
      }

      const padding = (rawMax - rawMin) * 0.05;
      return {
        min: rawMin - padding,
        max: rawMax + padding,
      };
    }

    function chooseYTickStep(range, metric) {
      if (metric === "v_out") {
        if (range <= 0.12) {
          return 0.01;
        }
        if (range <= 1.2) {
          return 0.1;
        }
        return 1;
      }

      const targetStep = Math.max(range / 6, 1);
      const magnitude = 10 ** Math.floor(Math.log10(targetStep));
      for (const multiplier of [1, 2, 5, 10]) {
        const step = multiplier * magnitude;
        if (range / step <= 8) {
          return step;
        }
      }
      return 10 * magnitude;
    }

    function countDecimals(value) {
      if (Number.isInteger(value)) {
        return 0;
      }
      return value.toString().split(".")[1]?.length ?? 0;
    }

    function getYTicks(values, metric) {
      const rawMin = Math.min(...values);
      const rawMax = Math.max(...values);
      const rawRange = Math.max(rawMax - rawMin, metric === "v_out" ? 0.01 : 1);
      const step = chooseYTickStep(rawRange, metric);
      const decimals = metric === "v_out" ? countDecimals(step) : 0;
      let min = Math.floor(rawMin / step) * step;
      let max = Math.ceil(rawMax / step) * step;

      if (min === max) {
        min -= step;
        max += step;
      }

      const ticks = [];
      for (let value = min; value <= max + step / 2; value += step) {
        ticks.push(Number(value.toFixed(decimals)));
      }

      return { ticks, min, max, decimals };
    }

    function formatYTick(value, metric, decimals) {
      return metric === "adc" ? value.toFixed(0) : value.toFixed(decimals);
    }

    function getXTickConfig() {
      switch (rangeSelect.value) {
        case "1h":
          return { stepMs: 5 * 60 * 1000, mode: "time" };
        case "1d":
          return { stepMs: 60 * 60 * 1000, mode: "time" };
        case "1w":
        case "1m":
          return { stepMs: 24 * 60 * 60 * 1000, mode: "day" };
        default:
          return { stepMs: 60 * 60 * 1000, mode: "time" };
      }
    }

    function alignToNextTick(unixtimeMs, stepMs) {
      return Math.ceil(unixtimeMs / stepMs) * stepMs;
    }

    function getXTicks(minTime, maxTime) {
      const config = getXTickConfig();
      const ticks = [];
      const firstTick = alignToNextTick(minTime, config.stepMs);

      for (let tick = firstTick; tick <= maxTime; tick += config.stepMs) {
        ticks.push(tick);
      }

      return { ticks, mode: config.mode };
    }

    function formatXTick(unixtimeMs, mode) {
      const date = new Date(unixtimeMs);
      if (mode === "day") {
        return date.toLocaleDateString([], { day: "2-digit", month: "short" });
      }
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function drawChart(measurements) {
      const metric = metricSelect.value;
      if (measurements.length === 0) {
        drawEmpty("No selected measurements found for this source and time range.");
        return;
      }

      const grouped = groupBySensor(measurements);
      const allTimes = measurements.map((measurement) => measurement.unixtime_ms);
      const allValues = measurements.map((measurement) => measurement[metric]);
      const minTime = Math.min(...allTimes);
      const maxTime = Math.max(...allTimes);
      const yTicks = getYTicks(allValues, metric);
      const minValue = yTicks.min;
      const maxValue = yTicks.max;
      const timeSpan = Math.max(maxTime - minTime, 1);
      const valueSpan = maxValue - minValue;
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
      chartPoints = [];
      hideTooltip();

      for (const value of yTicks.ticks) {
        const y = yFor(value);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + width, y);
        ctx.stroke();
        ctx.fillText(formatYTick(value, metric, yTicks.decimals), 12, y + 4);
      }

      const xTicks = getXTicks(minTime, maxTime);
      for (const tick of xTicks.ticks) {
        const x = xFor(tick);
        ctx.beginPath();
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, padding.top + height);
        ctx.stroke();
        ctx.fillText(formatXTick(tick, xTicks.mode), x - 18, canvas.height - 24);
      }

      ctx.strokeStyle = "#7282a3";
      ctx.beginPath();
      ctx.moveTo(padding.left, padding.top);
      ctx.lineTo(padding.left, padding.top + height);
      ctx.lineTo(padding.left + width, padding.top + height);
      ctx.stroke();

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
          const x = xFor(point.unixtime_ms);
          const y = yFor(point[metric]);
          ctx.beginPath();
          ctx.arc(x, y, 3, 0, Math.PI * 2);
          ctx.fill();
          chartPoints.push({
            x,
            y,
            color,
            metric,
            point,
          });
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

    function formatMetricValue(point, metric) {
      return metric === "adc" ? point.adc.toFixed(0) : point.v_out.toFixed(4);
    }

    function hideTooltip() {
      tooltipEl.style.display = "none";
    }

    function findNearestPoint(mouseX, mouseY) {
      let nearest = null;
      let nearestDistanceSquared = Infinity;
      const maxDistanceSquared = 14 * 14;

      for (const chartPoint of chartPoints) {
        const dx = chartPoint.x - mouseX;
        const dy = chartPoint.y - mouseY;
        const distanceSquared = dx * dx + dy * dy;
        if (distanceSquared < nearestDistanceSquared) {
          nearest = chartPoint;
          nearestDistanceSquared = distanceSquared;
        }
      }

      return nearestDistanceSquared <= maxDistanceSquared ? nearest : null;
    }

    function showTooltip(chartPoint, clientX, clientY) {
      const point = chartPoint.point;
      const canvasRect = canvas.getBoundingClientRect();
      const containerRect = canvas.parentElement.getBoundingClientRect();
      const left = clientX - containerRect.left + 14;
      const top = clientY - containerRect.top + 14;

      tooltipEl.innerHTML = `
        <strong>${point.sensor}</strong><br>
        source: ${point.source}<br>
        time: ${formatTime(point.unixtime_ms)}<br>
        ${getMetricLabel(chartPoint.metric)}: ${formatMetricValue(point, chartPoint.metric)}<br>
        adc: ${point.adc}<br>
        v_out: ${point.v_out.toFixed(4)}
      `;
      tooltipEl.style.borderColor = chartPoint.color;
      tooltipEl.style.left = `${Math.min(left, canvasRect.width - 260)}px`;
      tooltipEl.style.top = `${Math.min(top, canvasRect.height - 130)}px`;
      tooltipEl.style.display = "block";
    }

    function handleChartHover(event) {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const mouseX = (event.clientX - rect.left) * scaleX;
      const mouseY = (event.clientY - rect.top) * scaleY;
      const nearest = findNearestPoint(mouseX, mouseY);

      if (!nearest) {
        hideTooltip();
        return;
      }

      showTooltip(nearest, event.clientX, event.clientY);
    }

    async function loadSources() {
      const sources = await fetchJson("/api/sources");
      const preferredSources = ["pico_w"];
      const orderedSources = [
        ...preferredSources.filter((source) => sources.includes(source)),
        ...sources.filter((source) => !preferredSources.includes(source)),
      ];
      sourceSelect.replaceChildren(
        ...orderedSources.map((source) => {
          const option = document.createElement("option");
          option.value = source;
          option.textContent = source;
          return option;
        })
      );

      if (orderedSources.length === 0) {
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
      currentMeasurements = measurements;
      updateSensorFilter(measurements);
      drawChart(getSelectedMeasurements());
      updateDeleteControls(measurements);
      statusEl.textContent = `${getSelectedMeasurements().length} of ${measurements.length} measurements displayed.`;
    }

    async function deleteMeasurements() {
      const source = sourceSelect.value;
      const sensor = deleteSensorSelect.value;
      const password = deletePasswordInput.value;
      const startUnixtimeMs = fromDateTimeLocalValue(deleteStartInput.value);
      const endUnixtimeMs = fromDateTimeLocalValue(deleteEndInput.value);

      if (!source || !sensor) {
        statusEl.textContent = "Select a source and sensor before deleting.";
        return;
      }

      if (!Number.isFinite(startUnixtimeMs) || !Number.isFinite(endUnixtimeMs)) {
        statusEl.textContent = "Select a valid delete time period.";
        return;
      }

      if (!password) {
        statusEl.textContent = "Enter the delete password.";
        return;
      }

      const confirmed = confirm(
        `Delete ${sensor} measurements from ${source} between ` +
        `${deleteStartInput.value} and ${deleteEndInput.value}?`
      );
      if (!confirmed) {
        return;
      }

      const params = new URLSearchParams({
        source,
        sensor,
        start_unixtime_ms: String(startUnixtimeMs),
        end_unixtime_ms: String(endUnixtimeMs),
      });
      const response = await fetch(`/measurements?${params}`, {
        method: "DELETE",
        headers: { "X-Delete-Password": password },
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const result = await response.json();
      statusEl.textContent = `${result.deleted_rows} measurements deleted.`;
      deletePasswordInput.value = "";
      await loadMeasurements();
    }

    refreshButton.addEventListener("click", () => loadMeasurements().catch(showError));
    sourceSelect.addEventListener("change", () => loadMeasurements().catch(showError));
    metricSelect.addEventListener("change", () => drawChart(getSelectedMeasurements()));
    rangeSelect.addEventListener("change", () => loadMeasurements().catch(showError));
    deleteButton.addEventListener("click", () => deleteMeasurements().catch(showError));
    canvas.addEventListener("mousemove", handleChartHover);
    canvas.addEventListener("mouseleave", hideTooltip);

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
