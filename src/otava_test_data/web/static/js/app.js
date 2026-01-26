/**
 * Otava Test Data Visualizer - Frontend Application
 * With Otava change point detection integration
 */

// State
let stackedCharts = [];  // Array of chart instances for stacked view
let miniCharts = [];
let generators = {};
let selectedGenerator = null;
let generatorTileCharts = {};  // Mini charts for generator tiles

// DOM Elements - Data Generation
const generatorGrid = document.getElementById('generator-grid');
const lengthSlider = document.getElementById('length-slider');
const lengthInput = document.getElementById('length-input');
const lengthMin = document.getElementById('length-min');
const lengthMax = document.getElementById('length-max');
const seedInput = document.getElementById('seed-input');
const dynamicParams = document.getElementById('dynamic-params');

// DOM Elements - Otava Controls
const runOtavaCheckbox = document.getElementById('run-otava-checkbox');
const windowLenInput = document.getElementById('window-len-input');
const maxPvalueInput = document.getElementById('max-pvalue-input');
const yMinInput = document.getElementById('y-min-input');
const yMaxInput = document.getElementById('y-max-input');
const yMinSlider = document.getElementById('y-min-slider');
const yMaxSlider = document.getElementById('y-max-slider');
const yMinBoundMin = document.getElementById('y-min-bound-min');
const yMinBoundMax = document.getElementById('y-min-bound-max');
const yMaxBoundMin = document.getElementById('y-max-bound-min');
const yMaxBoundMax = document.getElementById('y-max-bound-max');

// DOM Elements - Moving Average Controls
const runMaCheckbox = document.getElementById('run-ma-checkbox');
const maWindowInput = document.getElementById('ma-window-input');
const maThresholdInput = document.getElementById('ma-threshold-input');

// DOM Elements - Boundary Controls
const runBoundaryCheckbox = document.getElementById('run-boundary-checkbox');
const boundaryUpperInput = document.getElementById('boundary-upper-input');
const boundaryLowerInput = document.getElementById('boundary-lower-input');

// DOM Elements - Threshold Alert Controls
const runThresholdCheckbox = document.getElementById('run-threshold-checkbox');
const thresholdPercentInput = document.getElementById('threshold-percent-input');
const thresholdOffsetInput = document.getElementById('threshold-offset-input');

// DOM Elements - Sliding Window Controls
const runSlidingWindowCheckbox = document.getElementById('run-sliding-window-checkbox');
const slidingWindowSizeInput = document.getElementById('sliding-window-size-input');
const slidingWindowOffsetInput = document.getElementById('sliding-window-offset-input');
const slidingWindowThresholdInput = document.getElementById('sliding-window-threshold-input');

// DOM Elements - Std Dev Controls
const runStdDevCheckbox = document.getElementById('run-stddev-checkbox');
const stdDevWindowInput = document.getElementById('stddev-window-input');
const stdDevNumInput = document.getElementById('stddev-num-input');

// Default match tolerance for comparing detected vs ground truth change points
const DEFAULT_TOLERANCE = 0;  // Exact match for True Positive
const CLOSE_MATCH_TOLERANCE = 5;  // Within 5 points for Close Match

// DOM Elements - Actions
const generateBtn = document.getElementById('generate-btn');
const showAllBtn = document.getElementById('show-all-btn');

// DOM Elements - Info Display
const generatorTitle = document.getElementById('generator-title');
const generatorDescription = document.getElementById('generator-description');
const changePointInfo = document.getElementById('change-point-info');
const stackedChartsContainer = document.getElementById('stacked-charts-container');

// DOM Elements - Stats
const statsSection = document.getElementById('stats');
const statLength = document.getElementById('stat-length');
const statMean = document.getElementById('stat-mean');
const statStd = document.getElementById('stat-std');
const statCpTruth = document.getElementById('stat-cp-truth');
const statCpDetected = document.getElementById('stat-cp-detected');

// DOM Elements - Accuracy Metrics
const accuracyMetrics = document.getElementById('accuracy-metrics');
const metricPrecision = document.getElementById('metric-precision');
const metricRecall = document.getElementById('metric-recall');
const metricF1 = document.getElementById('metric-f1');
const metricTp = document.getElementById('metric-tp');
const metricFp = document.getElementById('metric-fp');
const metricFn = document.getElementById('metric-fn');

// DOM Elements - Tables
const cpDetail = document.getElementById('change-points-detail');
const truthTableBody = document.getElementById('truth-table-body');
const detectedTableBody = document.getElementById('detected-table-body');

// DOM Elements - Multi-chart
const multiChartContainer = document.getElementById('multi-chart-container');
const chartGrid = document.getElementById('chart-grid');
const summaryStats = document.getElementById('summary-stats');

// DOM Elements - Settings Dialog
const settingsBtn = document.getElementById('settings-btn');
const settingsDialog = document.getElementById('settings-dialog');
const settingsCloseBtn = document.getElementById('settings-close-btn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadGenerators();
    await populateGeneratorGrid();
    setupEventListeners();
    updateGeneratorInfo();
    await generateData();
});

// Load generator metadata
async function loadGenerators() {
    try {
        const response = await fetch('/api/generators');
        generators = await response.json();
        // Set default selected generator
        selectedGenerator = Object.keys(generators)[0];
    } catch (error) {
        console.error('Failed to load generators:', error);
    }
}

// Populate generator grid with tiles
async function populateGeneratorGrid() {
    generatorGrid.innerHTML = '';

    // Fetch preview data for all generators
    const previewPromises = Object.keys(generators).map(async (name) => {
        try {
            const response = await fetch(`/api/generate/${name}?length=100&seed=42`);
            return { name, data: await response.json() };
        } catch (error) {
            console.error(`Failed to load preview for ${name}:`, error);
            return { name, data: null };
        }
    });

    const previews = await Promise.all(previewPromises);
    const previewData = {};
    previews.forEach(p => { previewData[p.name] = p.data; });

    // Custom ordering with four rows:
    // Row 1: Clean single patterns
    // Row 2: Clean multiple patterns (with placeholder for Constant)
    // Row 3: Normal noise single patterns
    // Row 4: Uniform noise single patterns
    const generatorNames = Object.keys(generators);
    const orderedNames = [];

    // Row 1 - single clean patterns
    const row1Order = [
        'constant',
        'outlier_clean',
        'step_function_clean',
        'regression_fix_clean',
        'variance_change_clean',
        'phase_change_clean',
        'banding_clean'
    ];
    const row1Names = row1Order.filter(name => generatorNames.includes(name));
    orderedNames.push(...row1Names);

    // Row 2 - multiple clean patterns (with placeholder)
    const row2Order = [
        '__placeholder__',
        'multiple_outliers_clean',
        'multiple_changes_clean',
        'multiple_regression_fix_clean',
        'multiple_variance_changes_clean',
        'multiple_phase_changes_clean',
        'multiple_banding_clean'
    ];
    const row2Names = row2Order.filter(name =>
        name === '__placeholder__' || generatorNames.includes(name)
    );
    orderedNames.push(...row2Names);

    // Row 3 - normal noise single patterns
    const row3Order = [
        'noise_normal',
        'outlier',
        'step_function',
        'regression_fix',
        'variance_change',
        'phase_change',
        'banding'
    ];
    const row3Names = row3Order.filter(name => generatorNames.includes(name));
    orderedNames.push(...row3Names);

    // Row 4 - uniform noise single patterns
    const row4Order = [
        'noise_uniform',
        'outlier_uniform',
        'step_function_uniform',
        'regression_fix_uniform',
        'variance_change_uniform',
        'phase_change_uniform',
        'banding_uniform'
    ];
    const row4Names = row4Order.filter(name => generatorNames.includes(name));
    orderedNames.push(...row4Names);

    // Track line break positions
    const row1EndIndex = row1Names.length;
    const row2EndIndex = row1Names.length + row2Names.length;
    const row3EndIndex = row1Names.length + row2Names.length + row3Names.length;
    const row4EndIndex = row1Names.length + row2Names.length + row3Names.length + row4Names.length;

    // Create tiles for each generator in order
    let tileIndex = 0;
    for (const name of orderedNames) {
        tileIndex++;

        // Handle placeholder tile (empty space for alignment)
        if (name === '__placeholder__') {
            const placeholder = document.createElement('div');
            placeholder.className = 'generator-tile placeholder';
            generatorGrid.appendChild(placeholder);
            continue;
        }

        const info = generators[name];
        const tile = document.createElement('div');
        tile.className = 'generator-tile' + (name === selectedGenerator ? ' selected' : '');
        tile.dataset.generator = name;

        // Preview container
        const preview = document.createElement('div');
        preview.className = 'generator-tile-preview';
        const canvas = document.createElement('canvas');
        canvas.id = `preview-${name}`;
        preview.appendChild(canvas);

        // Name label
        const label = document.createElement('div');
        label.className = 'generator-tile-name';
        label.textContent = info.name;

        tile.appendChild(preview);
        tile.appendChild(label);
        generatorGrid.appendChild(tile);

        // Add line breaks after each row
        if (tileIndex === row1EndIndex || tileIndex === row2EndIndex ||
            tileIndex === row3EndIndex || tileIndex === row4EndIndex) {
            const lineBreak = document.createElement('div');
            lineBreak.className = 'generator-grid-break';
            generatorGrid.appendChild(lineBreak);
        }

        // Click handler
        tile.addEventListener('click', () => selectGenerator(name));

        // Create mini chart
        if (previewData[name] && previewData[name].data) {
            createTileChart(canvas, previewData[name].data, name === selectedGenerator);
        }
    }
}

// Create a mini chart for a generator tile
function createTileChart(canvas, data, isSelected) {
    const ctx = canvas.getContext('2d');
    const name = canvas.id.replace('preview-', '');

    // Destroy existing chart if any
    if (generatorTileCharts[name]) {
        generatorTileCharts[name].destroy();
    }

    generatorTileCharts[name] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map((_, i) => i),
            datasets: [{
                data: data,
                borderColor: isSelected ? '#60a5fa' : '#94a3b8',
                borderWidth: 1,
                fill: false,
                tension: 0,
                pointRadius: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false }
            },
            interaction: { enabled: false },
            animation: false,
        }
    });
}

// Select a generator from the grid
function selectGenerator(name) {
    // Update selection state
    const previousSelected = selectedGenerator;
    selectedGenerator = name;

    // Update tile visual state
    document.querySelectorAll('.generator-tile').forEach(tile => {
        const isSelected = tile.dataset.generator === name;
        tile.classList.toggle('selected', isSelected);

        // Update chart color
        const tileName = tile.dataset.generator;
        if (generatorTileCharts[tileName]) {
            generatorTileCharts[tileName].data.datasets[0].borderColor = isSelected ? '#60a5fa' : '#94a3b8';
            generatorTileCharts[tileName].update('none');
        }
    });

    // Trigger UI updates
    updateGeneratorInfo();
    updateDynamicParams();
    generateData();
}

// Helper function to setup a slider with configurable bounds
function setupSliderWithBounds(slider, valueInput, minBoundInput, maxBoundInput, onChange) {
    // Sync slider to value input
    slider.addEventListener('input', () => {
        valueInput.value = slider.value;
    });
    slider.addEventListener('change', onChange);

    // Sync value input to slider
    valueInput.addEventListener('input', () => {
        const val = parseFloat(valueInput.value);
        const min = parseFloat(slider.min);
        const max = parseFloat(slider.max);
        if (val >= min && val <= max) {
            slider.value = val;
        }
    });
    valueInput.addEventListener('change', () => {
        // Clamp value to bounds
        const val = parseFloat(valueInput.value);
        const min = parseFloat(slider.min);
        const max = parseFloat(slider.max);
        valueInput.value = Math.max(min, Math.min(max, val));
        slider.value = valueInput.value;
        onChange();
    });

    // Update slider bounds when min/max inputs change
    minBoundInput.addEventListener('change', () => {
        const newMin = parseFloat(minBoundInput.value);
        const currentMax = parseFloat(maxBoundInput.value);
        if (newMin < currentMax) {
            slider.min = newMin;
            valueInput.min = newMin;
            // Adjust current value if needed
            if (parseFloat(valueInput.value) < newMin) {
                valueInput.value = newMin;
                slider.value = newMin;
            }
            onChange();
        } else {
            // Reset to previous valid value
            minBoundInput.value = slider.min;
        }
    });

    maxBoundInput.addEventListener('change', () => {
        const newMax = parseFloat(maxBoundInput.value);
        const currentMin = parseFloat(minBoundInput.value);
        if (newMax > currentMin) {
            slider.max = newMax;
            valueInput.max = newMax;
            // Adjust current value if needed
            if (parseFloat(valueInput.value) > newMax) {
                valueInput.value = newMax;
                slider.value = newMax;
            }
            onChange();
        } else {
            // Reset to previous valid value
            maxBoundInput.value = slider.max;
        }
    });
}

// Setup event listeners
function setupEventListeners() {
    // Generator selection is now handled by tile click in selectGenerator()

    // Settings dialog
    settingsBtn.addEventListener('click', () => {
        settingsDialog.classList.remove('hidden');
    });

    settingsCloseBtn.addEventListener('click', () => {
        settingsDialog.classList.add('hidden');
    });

    // Close dialog when clicking outside
    settingsDialog.addEventListener('click', (e) => {
        if (e.target === settingsDialog) {
            settingsDialog.classList.add('hidden');
        }
    });

    // Close dialog on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !settingsDialog.classList.contains('hidden')) {
            settingsDialog.classList.add('hidden');
        }
    });

    // Length slider with bounds
    setupSliderWithBounds(lengthSlider, lengthInput, lengthMin, lengthMax, generateData);

    seedInput.addEventListener('change', generateData);
    generateBtn.addEventListener('click', generateData);
    showAllBtn.addEventListener('click', showAllPatterns);

    // Otava controls
    runOtavaCheckbox.addEventListener('change', generateData);
    windowLenInput.addEventListener('change', generateData);
    maxPvalueInput.addEventListener('change', generateData);

    // Y-Axis Min slider with bounds
    setupSliderWithBounds(yMinSlider, yMinInput, yMinBoundMin, yMinBoundMax, generateData);

    // Y-Axis Max slider with bounds
    setupSliderWithBounds(yMaxSlider, yMaxInput, yMaxBoundMin, yMaxBoundMax, generateData);

    // Moving Average controls
    runMaCheckbox.addEventListener('change', generateData);
    maWindowInput.addEventListener('change', generateData);
    maThresholdInput.addEventListener('change', generateData);

    // Boundary controls
    runBoundaryCheckbox.addEventListener('change', generateData);
    boundaryUpperInput.addEventListener('change', generateData);
    boundaryLowerInput.addEventListener('change', generateData);

    // Threshold Alert controls
    runThresholdCheckbox.addEventListener('change', generateData);
    thresholdPercentInput.addEventListener('change', generateData);
    thresholdOffsetInput.addEventListener('change', generateData);

    // Sliding Window controls
    runSlidingWindowCheckbox.addEventListener('change', generateData);
    slidingWindowSizeInput.addEventListener('change', generateData);
    slidingWindowOffsetInput.addEventListener('change', generateData);
    slidingWindowThresholdInput.addEventListener('change', generateData);

    // Std Dev controls
    runStdDevCheckbox.addEventListener('change', generateData);
    stdDevWindowInput.addEventListener('change', generateData);
    stdDevNumInput.addEventListener('change', generateData);
}

// Update generator info display
function updateGeneratorInfo() {
    const name = selectedGenerator;
    const info = generators[name];

    if (info) {
        generatorTitle.textContent = info.name;
        generatorDescription.textContent = info.description;

        if (info.has_change_points) {
            changePointInfo.classList.remove('hidden');
        } else {
            changePointInfo.classList.add('hidden');
        }
    }
}

// Update dynamic parameter inputs
function updateDynamicParams() {
    const name = selectedGenerator;
    const info = generators[name];

    dynamicParams.innerHTML = '';

    if (info && info.params) {
        for (const [paramName, paramInfo] of Object.entries(info.params)) {
            const div = document.createElement('div');
            div.className = 'param-group';

            const label = document.createElement('label');
            label.textContent = formatParamName(paramName);
            label.htmlFor = `param-${paramName}`;

            const input = document.createElement('input');
            input.type = 'number';
            input.id = `param-${paramName}`;
            input.name = paramName;
            input.value = paramInfo.default;
            input.min = paramInfo.min;
            input.max = paramInfo.max;
            input.step = paramInfo.step || 1;
            input.addEventListener('change', generateData);

            div.appendChild(label);
            div.appendChild(input);
            dynamicParams.appendChild(div);
        }
    }
}

// Format parameter name for display
function formatParamName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Moving Average Change Point Detection
 * Detects change points by comparing non-overlapping windows before and after each point
 * A change point is detected when the difference between window means exceeds threshold * local_std
 */
function detectChangePointsMA(data, windowSize, threshold) {
    const n = data.length;
    if (n < windowSize * 2) {
        return { indices: [], details: [] };
    }

    // For each potential change point, compare the window before vs window after
    const candidates = [];

    for (let i = windowSize; i < n - windowSize; i++) {
        // Window before: data[i-windowSize : i]
        const windowBefore = data.slice(i - windowSize, i);
        // Window after: data[i : i+windowSize]
        const windowAfter = data.slice(i, i + windowSize);

        const meanBefore = windowBefore.reduce((a, b) => a + b, 0) / windowSize;
        const meanAfter = windowAfter.reduce((a, b) => a + b, 0) / windowSize;

        // Compute standard deviation separately for each window (avoids inflation from step)
        const stdBefore = Math.sqrt(
            windowBefore.reduce((acc, val) => acc + Math.pow(val - meanBefore, 2), 0) / windowSize
        );
        const stdAfter = Math.sqrt(
            windowAfter.reduce((acc, val) => acc + Math.pow(val - meanAfter, 2), 0) / windowSize
        );
        // Use average of the two stds (not affected by the step change)
        const localStd = (stdBefore + stdAfter) / 2;

        const diff = Math.abs(meanAfter - meanBefore);
        const effectiveThreshold = threshold * Math.max(localStd, 1); // Avoid division by zero for clean data

        if (diff > effectiveThreshold) {
            candidates.push({
                index: i,
                diff: diff,
                meanBefore: meanBefore,
                meanAfter: meanAfter,
                localStd: localStd,
                threshold: effectiveThreshold
            });
        }
    }

    // Find local maxima of diff (peak detection)
    const indices = [];
    const details = [];

    for (let c = 0; c < candidates.length; c++) {
        const candidate = candidates[c];
        let isLocalMax = true;

        // Check if this is a local maximum within windowSize range
        for (let j = 0; j < candidates.length; j++) {
            if (j !== c && Math.abs(candidates[j].index - candidate.index) < windowSize) {
                if (candidates[j].diff > candidate.diff) {
                    isLocalMax = false;
                    break;
                }
            }
        }

        // Also ensure minimum distance from previously selected points
        if (isLocalMax && (indices.length === 0 || candidate.index - indices[indices.length - 1] >= windowSize)) {
            indices.push(candidate.index);
            details.push({
                index: candidate.index,
                maBefore: candidate.meanBefore.toFixed(2),
                maAfter: candidate.meanAfter.toFixed(2),
                diff: candidate.diff.toFixed(2),
                threshold: candidate.threshold.toFixed(2)
            });
        }
    }

    return { indices, details };
}

/**
 * Threshold Based Alert Detection
 * Detects points where the value changed by more than a threshold percentage
 * compared to a previous point (configurable offset)
 * @param {number[]} data - The time series data
 * @param {number} threshold - Percentage threshold (e.g., 5 for 5%)
 * @param {number} offset - How far back to look for comparison (1 = previous point, 2 = two points back, etc.)
 */
function detectChangePointsThreshold(data, threshold, offset = 1) {
    const indices = [];
    const details = [];

    // Start from the offset index (need at least 'offset' prior points)
    for (let i = offset; i < data.length; i++) {
        const currentValue = data[i];
        const referenceValue = data[i - offset];

        // Avoid division by zero
        if (referenceValue === 0) {
            continue;
        }

        // Calculate percentage change
        const percentChange = ((currentValue - referenceValue) / Math.abs(referenceValue)) * 100;
        const absPercentChange = Math.abs(percentChange);

        if (absPercentChange > threshold) {
            indices.push(i);
            details.push({
                index: i,
                currentValue: currentValue.toFixed(2),
                referenceValue: referenceValue.toFixed(2),
                referenceIndex: i - offset,
                percentChange: percentChange.toFixed(2),
                direction: percentChange > 0 ? 'increase' : 'decrease'
            });
        }
    }

    return { indices, details };
}

/**
 * Sliding Window Change Point Detection
 * Compares average of current window with average of reference window (offset back by M points)
 * Detects change when percentage difference exceeds threshold
 * @param {number[]} data - The time series data
 * @param {number} windowSize - Number of points in each window (N)
 * @param {number} offset - How far back the reference window is (M)
 * @param {number} threshold - Percentage threshold for detection
 */
function detectChangePointsSlidingWindow(data, windowSize, offset, threshold) {
    const indices = [];
    const details = [];
    const halfWindow = Math.floor(windowSize / 2);

    // Need enough points for both windows
    const startIdx = halfWindow + offset + halfWindow;

    for (let i = startIdx; i < data.length - halfWindow; i++) {
        // Current window: centered around point i
        const currentStart = i - halfWindow;
        const currentEnd = i + halfWindow + 1;
        const currentWindow = data.slice(currentStart, currentEnd);
        const currentAvg = currentWindow.reduce((a, b) => a + b, 0) / currentWindow.length;

        // Reference window: centered around point (i - offset)
        const refCenter = i - offset;
        const refStart = refCenter - halfWindow;
        const refEnd = refCenter + halfWindow + 1;
        const refWindow = data.slice(refStart, refEnd);
        const refAvg = refWindow.reduce((a, b) => a + b, 0) / refWindow.length;

        // Avoid division by zero
        if (refAvg === 0) continue;

        // Calculate percentage change
        const percentChange = ((currentAvg - refAvg) / Math.abs(refAvg)) * 100;
        const absPercentChange = Math.abs(percentChange);

        if (absPercentChange > threshold) {
            // Avoid duplicate detections within window size
            if (indices.length === 0 || i - indices[indices.length - 1] >= windowSize) {
                indices.push(i);
                details.push({
                    index: i,
                    currentAvg: currentAvg.toFixed(2),
                    refAvg: refAvg.toFixed(2),
                    percentChange: percentChange.toFixed(2),
                    direction: percentChange > 0 ? 'increase' : 'decrease'
                });
            }
        }
    }

    return { indices, details };
}

/**
 * Standard Deviation Based Change Point Detection
 * For each point P, compare it to mean ± K standard deviations of M previous points
 * If P is outside this range, trigger an alert
 * @param {number[]} data - The time series data
 * @param {number} windowSize - Number of previous points to use (M)
 * @param {number} numStdDevs - Number of standard deviations (K)
 */
function detectChangePointsStdDev(data, windowSize, numStdDevs) {
    const indices = [];
    const details = [];

    // Need at least windowSize points before we can start
    for (let i = windowSize; i < data.length; i++) {
        // Get the M previous points (not including current point)
        const window = data.slice(i - windowSize, i);

        // Compute mean and standard deviation
        const mean = window.reduce((a, b) => a + b, 0) / windowSize;
        const variance = window.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / windowSize;
        const stdDev = Math.sqrt(variance);

        // Current point
        const value = data[i];

        // Check if outside mean ± K std devs
        const upperBound = mean + numStdDevs * stdDev;
        const lowerBound = mean - numStdDevs * stdDev;
        const zScore = stdDev > 0 ? (value - mean) / stdDev : 0;

        if (value > upperBound || value < lowerBound) {
            indices.push(i);
            details.push({
                index: i,
                value: value.toFixed(2),
                mean: mean.toFixed(2),
                stdDev: stdDev.toFixed(2),
                zScore: zScore.toFixed(2),
                direction: value > upperBound ? 'above' : 'below'
            });
        }
    }

    return { indices, details };
}

/**
 * Boundary/Threshold Change Point Detection
 * Detects change points when values cross upper or lower boundaries
 * Only triggers once per boundary crossing (not for every point outside bounds)
 */
function detectChangePointsBoundary(data, upperBound, lowerBound) {
    const indices = [];
    const details = [];
    let wasAboveUpper = false;
    let wasBelowLower = false;

    for (let i = 0; i < data.length; i++) {
        const value = data[i];

        // Check upper boundary crossing
        if (value > upperBound && !wasAboveUpper) {
            indices.push(i);
            details.push({
                index: i,
                value: value.toFixed(2),
                boundary: 'upper',
                threshold: upperBound
            });
            wasAboveUpper = true;
        } else if (value <= upperBound) {
            wasAboveUpper = false;
        }

        // Check lower boundary crossing
        if (value < lowerBound && !wasBelowLower) {
            indices.push(i);
            details.push({
                index: i,
                value: value.toFixed(2),
                boundary: 'lower',
                threshold: lowerBound
            });
            wasBelowLower = true;
        } else if (value >= lowerBound) {
            wasBelowLower = false;
        }
    }

    return { indices, details };
}

// Generate data and update chart
async function generateData() {
    const name = selectedGenerator;
    const length = lengthInput.value;
    const seed = seedInput.value;
    const runOtava = runOtavaCheckbox.checked;

    // Build query params
    const params = new URLSearchParams({
        length,
        seed,
        run_otava: runOtava,
        window_len: windowLenInput.value,
        max_pvalue: maxPvalueInput.value,
        tolerance: DEFAULT_TOLERANCE,
    });

    // Add dynamic params
    const paramInputs = dynamicParams.querySelectorAll('input');
    paramInputs.forEach(input => {
        params.append(input.name, input.value);
    });

    try {
        document.body.classList.add('loading');

        const response = await fetch(`/api/generate/${name}?${params}`);
        const data = await response.json();

        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        updateChart(data);
        updateStats(data);
        updateAccuracyMetrics(data);
        updateComparisonTables(data);

        // Hide multi-chart view when generating single
        multiChartContainer.classList.add('hidden');
        document.querySelector('.stacked-charts-container').classList.remove('hidden');
        document.querySelector('.chart-legend').classList.remove('hidden');
        statsSection.classList.remove('hidden');
        accuracyMetrics.classList.remove('hidden');
        cpDetail.classList.remove('hidden');

    } catch (error) {
        console.error('Failed to generate data:', error);
    } finally {
        document.body.classList.remove('loading');
    }
}

/**
 * Classify detected indices into exact matches, close matches, and false positives
 * @param {number[]} detectedIndices - Array of detected change point indices
 * @param {number[]} groundTruthIndices - Array of ground truth change point indices
 * @returns {Object} Object with exactMatches, closeMatches sets and counts
 */
function classifyDetections(detectedIndices, groundTruthIndices) {
    const exactMatches = new Set();
    const closeMatches = new Set();
    const usedGroundTruth = new Set();

    // First pass: find exact matches
    detectedIndices.forEach(dIdx => {
        for (const gtIdx of groundTruthIndices) {
            if (!usedGroundTruth.has(gtIdx) && Math.abs(dIdx - gtIdx) <= DEFAULT_TOLERANCE) {
                exactMatches.add(dIdx);
                usedGroundTruth.add(gtIdx);
                break;
            }
        }
    });

    // Second pass: find close matches (not already exact)
    detectedIndices.forEach(dIdx => {
        if (exactMatches.has(dIdx)) return;
        for (const gtIdx of groundTruthIndices) {
            if (!usedGroundTruth.has(gtIdx) && Math.abs(dIdx - gtIdx) <= CLOSE_MATCH_TOLERANCE) {
                closeMatches.add(dIdx);
                usedGroundTruth.add(gtIdx);
                break;
            }
        }
    });

    const tp = exactMatches.size;
    const cm = closeMatches.size;
    const fp = detectedIndices.length - tp - cm;

    return { exactMatches, closeMatches, tp, cm, fp };
}

// Update the stacked charts - one per enabled analysis method
function updateChart(data) {
    // Destroy existing charts
    stackedCharts.forEach(chart => chart.destroy());
    stackedCharts = [];

    // Clear container
    stackedChartsContainer.innerHTML = '';

    // Prepare data
    const labels = data.data.map((_, i) => i);
    const values = data.data;

    // Get change point indices (exclude outliers - they're anomalies, not change points)
    const allChangePoints = data.ground_truth?.change_points || data.change_points || [];
    const groundTruthIndices = allChangePoints
        .filter(cp => cp.type !== 'outlier')
        .map(cp => cp.index);
    const detectedIndices = data.otava?.detected_indices || [];

    // Run MA detection if enabled
    const runMa = runMaCheckbox.checked;
    const maWindow = parseInt(maWindowInput.value);
    const maThreshold = parseFloat(maThresholdInput.value);
    const maResult = runMa ? detectChangePointsMA(values, maWindow, maThreshold) : { indices: [], details: [] };
    const maDetectedIndices = maResult.indices;

    // Classify Otava detections
    const otavaClassification = classifyDetections(detectedIndices, groundTruthIndices);

    // Classify MA detections
    const maClassification = classifyDetections(maDetectedIndices, groundTruthIndices);

    // Run Boundary detection if enabled
    const runBoundary = runBoundaryCheckbox.checked;
    const upperBound = parseFloat(boundaryUpperInput.value);
    const lowerBound = parseFloat(boundaryLowerInput.value);
    const boundaryResult = runBoundary ? detectChangePointsBoundary(values, upperBound, lowerBound) : { indices: [], details: [] };
    const boundaryDetectedIndices = boundaryResult.indices;

    // Classify Boundary detections
    const boundaryClassification = classifyDetections(boundaryDetectedIndices, groundTruthIndices);

    // Run Threshold Alert detection if enabled
    const runThreshold = runThresholdCheckbox.checked;
    const thresholdPercent = parseFloat(thresholdPercentInput.value);
    const thresholdOffset = parseInt(thresholdOffsetInput.value);
    const thresholdResult = runThreshold ? detectChangePointsThreshold(values, thresholdPercent, thresholdOffset) : { indices: [], details: [] };
    const thresholdDetectedIndices = thresholdResult.indices;

    // Classify Threshold detections
    const thresholdClassification = classifyDetections(thresholdDetectedIndices, groundTruthIndices);

    // Run Sliding Window detection if enabled
    const runSlidingWindow = runSlidingWindowCheckbox.checked;
    const slidingWindowSize = parseInt(slidingWindowSizeInput.value);
    const slidingWindowOffset = parseInt(slidingWindowOffsetInput.value);
    const slidingWindowThreshold = parseFloat(slidingWindowThresholdInput.value);
    const slidingWindowResult = runSlidingWindow ? detectChangePointsSlidingWindow(values, slidingWindowSize, slidingWindowOffset, slidingWindowThreshold) : { indices: [], details: [] };
    const slidingWindowDetectedIndices = slidingWindowResult.indices;

    // Classify Sliding Window detections
    const slidingWindowClassification = classifyDetections(slidingWindowDetectedIndices, groundTruthIndices);

    // Run Std Dev detection if enabled
    const runStdDev = runStdDevCheckbox.checked;
    const stdDevWindow = parseInt(stdDevWindowInput.value);
    const stdDevNum = parseFloat(stdDevNumInput.value);
    const stdDevResult = runStdDev ? detectChangePointsStdDev(values, stdDevWindow, stdDevNum) : { indices: [], details: [] };
    const stdDevDetectedIndices = stdDevResult.indices;

    // Classify Std Dev detections
    const stdDevClassification = classifyDetections(stdDevDetectedIndices, groundTruthIndices);

    // Create ground truth annotations (shared by all charts)
    const createAnnotations = () => {
        const annotations = {};
        groundTruthIndices.forEach((idx, i) => {
            const cp = data.ground_truth?.change_points?.find(cp => cp.index === idx);
            annotations[`groundTruth${i}`] = {
                type: 'line',
                xMin: idx,
                xMax: idx,
                borderColor: '#10b981',
                borderWidth: 2,
                borderDash: [6, 4],
                label: {
                    display: true,
                    content: cp ? `GT: ${cp.type}` : `GT: ${idx}`,
                    position: 'start',
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    color: 'white',
                    font: { size: 10 },
                    padding: 3,
                }
            };
        });
        return annotations;
    };

    // Helper to create a chart container
    const createChartContainer = (id, title, color, tpCount, cmCount, fpCount) => {
        const container = document.createElement('div');
        container.className = 'stacked-chart';
        container.id = `chart-${id}`;

        const header = document.createElement('div');
        header.className = 'stacked-chart-header';
        header.innerHTML = `
            <span class="method-indicator ${id}"></span>
            <h4>${title}</h4>
            <span class="detection-count">
                <strong style="color: #ef4444">${tpCount} TP</strong> /
                <strong style="color: #eab308">${cmCount} CM</strong> /
                <strong style="color: #f97316">${fpCount} FP</strong>
            </span>
        `;

        const canvas = document.createElement('canvas');
        canvas.id = `canvas-${id}`;

        container.appendChild(header);
        container.appendChild(canvas);
        stackedChartsContainer.appendChild(container);

        return canvas;
    };

    // Common chart options
    const getChartOptions = (annotations, showXAxis = false) => ({
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            annotation: { annotations }
        },
        scales: {
            x: {
                display: showXAxis,
                title: { display: showXAxis, text: 'Index' },
                grid: { display: false }
            },
            y: {
                min: parseInt(yMinInput.value),
                max: parseInt(yMaxInput.value),
                title: { display: true, text: 'Value' },
                grid: { color: 'rgba(0, 0, 0, 0.05)' }
            }
        },
        interaction: { intersect: false, mode: 'index' }
    });

    // Track which is the last chart for showing X-axis
    const enabledMethods = [];
    if (runOtavaCheckbox.checked) enabledMethods.push('otava');
    if (runMa) enabledMethods.push('ma');
    if (runBoundary) enabledMethods.push('boundary');
    if (runThreshold) enabledMethods.push('threshold');
    if (runSlidingWindow) enabledMethods.push('slidingWindow');
    if (runStdDev) enabledMethods.push('stdDev');

    // Create Otava chart if enabled
    if (runOtavaCheckbox.checked) {
        const { tp: otavaTp, cm: otavaCm, fp: otavaFp, exactMatches: otavaExact, closeMatches: otavaClose } = otavaClassification;
        const canvas = createChartContainer('otava', 'Otava Analysis', '#2563eb', otavaTp, otavaCm, otavaFp);
        const ctx = canvas.getContext('2d');

        const otavaPointColors = values.map((_, i) => {
            if (detectedIndices.includes(i)) {
                if (otavaExact.has(i)) return '#f87171';  // TP - red
                if (otavaClose.has(i)) return '#fde047';  // CM - yellow
                return '#f97316';  // FP - orange
            }
            return 'transparent';
        });
        const otavaPointBorders = values.map((_, i) => {
            if (detectedIndices.includes(i)) {
                if (otavaExact.has(i)) return '#ef4444';
                if (otavaClose.has(i)) return '#eab308';
                return '#ea580c';
            }
            return 'transparent';
        });
        const otavaPointRadii = values.map((_, i) => detectedIndices.includes(i) ? 6 : 0);
        const otavaPointStyles = values.map((_, i) => {
            if (detectedIndices.includes(i)) {
                if (otavaExact.has(i)) return 'circle';  // TP
                if (otavaClose.has(i)) return 'rectRot';  // CM - diamond
                return 'triangle';  // FP
            }
            return 'circle';
        });

        const isLast = enabledMethods[enabledMethods.length - 1] === 'otava';
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: data.generator,
                    data: values,
                    borderColor: '#94a3b8',
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    borderWidth: 1.5,
                    fill: true,
                    tension: 0,
                    pointBackgroundColor: otavaPointColors,
                    pointBorderColor: otavaPointBorders,
                    pointBorderWidth: 1.5,
                    pointRadius: otavaPointRadii,
                    pointHoverRadius: 8,
                    pointStyle: otavaPointStyles,
                }]
            },
            options: getChartOptions(createAnnotations(), isLast)
        });
        stackedCharts.push(chart);
    }

    // Create MA chart if enabled
    if (runMa) {
        const { tp: maTp, cm: maCm, fp: maFp, exactMatches: maExact, closeMatches: maClose } = maClassification;
        const canvas = createChartContainer('ma', 'Moving Average Analysis', '#8b5cf6', maTp, maCm, maFp);
        const ctx = canvas.getContext('2d');

        const maPointColors = values.map((_, i) => {
            if (maDetectedIndices.includes(i)) {
                if (maExact.has(i)) return '#f87171';
                if (maClose.has(i)) return '#fde047';
                return '#f97316';
            }
            return 'transparent';
        });
        const maPointBorders = values.map((_, i) => {
            if (maDetectedIndices.includes(i)) {
                if (maExact.has(i)) return '#ef4444';
                if (maClose.has(i)) return '#eab308';
                return '#ea580c';
            }
            return 'transparent';
        });
        const maPointRadii = values.map((_, i) => maDetectedIndices.includes(i) ? 6 : 0);
        const maPointStyles = values.map((_, i) => {
            if (maDetectedIndices.includes(i)) {
                if (maExact.has(i)) return 'circle';
                if (maClose.has(i)) return 'rectRot';
                return 'triangle';
            }
            return 'circle';
        });

        const isLast = enabledMethods[enabledMethods.length - 1] === 'ma';
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'MA Detection',
                    data: values,
                    borderColor: '#94a3b8',
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    borderWidth: 1.5,
                    fill: true,
                    tension: 0,
                    pointBackgroundColor: maPointColors,
                    pointBorderColor: maPointBorders,
                    pointBorderWidth: 1.5,
                    pointRadius: maPointRadii,
                    pointHoverRadius: 8,
                    pointStyle: maPointStyles,
                }]
            },
            options: getChartOptions(createAnnotations(), isLast)
        });
        stackedCharts.push(chart);
    }

    // Create Boundary chart if enabled
    if (runBoundary) {
        const { tp: boundaryTp, cm: boundaryCm, fp: boundaryFp, exactMatches: boundaryExact, closeMatches: boundaryClose } = boundaryClassification;
        const canvas = createChartContainer('boundary', 'Boundary Analysis', '#06b6d4', boundaryTp, boundaryCm, boundaryFp);
        const ctx = canvas.getContext('2d');

        const boundaryPointColors = values.map((_, i) => {
            if (boundaryDetectedIndices.includes(i)) {
                if (boundaryExact.has(i)) return '#f87171';
                if (boundaryClose.has(i)) return '#fde047';
                return '#f97316';
            }
            return 'transparent';
        });
        const boundaryPointBorders = values.map((_, i) => {
            if (boundaryDetectedIndices.includes(i)) {
                if (boundaryExact.has(i)) return '#ef4444';
                if (boundaryClose.has(i)) return '#eab308';
                return '#ea580c';
            }
            return 'transparent';
        });
        const boundaryPointRadii = values.map((_, i) => boundaryDetectedIndices.includes(i) ? 6 : 0);
        const boundaryPointStyles = values.map((_, i) => {
            if (boundaryDetectedIndices.includes(i)) {
                if (boundaryExact.has(i)) return 'circle';
                if (boundaryClose.has(i)) return 'rectRot';
                return 'triangle';
            }
            return 'circle';
        });

        // Add boundary line annotations
        const annotations = createAnnotations();
        annotations['upperBound'] = {
            type: 'line',
            yMin: upperBound,
            yMax: upperBound,
            borderColor: '#06b6d4',
            borderWidth: 1,
            borderDash: [4, 4],
            label: {
                display: true,
                content: `Upper: ${upperBound}`,
                position: 'end',
                backgroundColor: 'rgba(6, 182, 212, 0.8)',
                color: 'white',
                font: { size: 9 },
                padding: 2,
            }
        };
        annotations['lowerBound'] = {
            type: 'line',
            yMin: lowerBound,
            yMax: lowerBound,
            borderColor: '#06b6d4',
            borderWidth: 1,
            borderDash: [4, 4],
            label: {
                display: true,
                content: `Lower: ${lowerBound}`,
                position: 'end',
                backgroundColor: 'rgba(6, 182, 212, 0.8)',
                color: 'white',
                font: { size: 9 },
                padding: 2,
            }
        };

        const isLast = enabledMethods[enabledMethods.length - 1] === 'boundary';
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Boundary Detection',
                    data: values,
                    borderColor: '#94a3b8',
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    borderWidth: 1.5,
                    fill: true,
                    tension: 0,
                    pointBackgroundColor: boundaryPointColors,
                    pointBorderColor: boundaryPointBorders,
                    pointBorderWidth: 1.5,
                    pointRadius: boundaryPointRadii,
                    pointHoverRadius: 8,
                    pointStyle: boundaryPointStyles,
                }]
            },
            options: getChartOptions(annotations, isLast)
        });
        stackedCharts.push(chart);
    }

    // Create Threshold Alert chart if enabled
    if (runThreshold) {
        const { tp: thresholdTp, cm: thresholdCm, fp: thresholdFp, exactMatches: thresholdExact, closeMatches: thresholdClose } = thresholdClassification;
        const canvas = createChartContainer('threshold', `Threshold Alert (>${thresholdPercent}%, offset=${thresholdOffset})`, '#ec4899', thresholdTp, thresholdCm, thresholdFp);
        const ctx = canvas.getContext('2d');

        const thresholdPointColors = values.map((_, i) => {
            if (thresholdDetectedIndices.includes(i)) {
                if (thresholdExact.has(i)) return '#f87171';
                if (thresholdClose.has(i)) return '#fde047';
                return '#f97316';
            }
            return 'transparent';
        });
        const thresholdPointBorders = values.map((_, i) => {
            if (thresholdDetectedIndices.includes(i)) {
                if (thresholdExact.has(i)) return '#ef4444';
                if (thresholdClose.has(i)) return '#eab308';
                return '#ea580c';
            }
            return 'transparent';
        });
        const thresholdPointRadii = values.map((_, i) => thresholdDetectedIndices.includes(i) ? 6 : 0);
        const thresholdPointStyles = values.map((_, i) => {
            if (thresholdDetectedIndices.includes(i)) {
                if (thresholdExact.has(i)) return 'circle';
                if (thresholdClose.has(i)) return 'rectRot';
                return 'triangle';
            }
            return 'circle';
        });

        const isLast = enabledMethods[enabledMethods.length - 1] === 'threshold';
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Threshold Alert Detection',
                    data: values,
                    borderColor: '#94a3b8',
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    borderWidth: 1.5,
                    fill: true,
                    tension: 0,
                    pointBackgroundColor: thresholdPointColors,
                    pointBorderColor: thresholdPointBorders,
                    pointBorderWidth: 1.5,
                    pointRadius: thresholdPointRadii,
                    pointHoverRadius: 8,
                    pointStyle: thresholdPointStyles,
                }]
            },
            options: getChartOptions(createAnnotations(), isLast)
        });
        stackedCharts.push(chart);
    }

    // Create Sliding Window chart if enabled
    if (runSlidingWindow) {
        const { tp: slidingWindowTp, cm: slidingWindowCm, fp: slidingWindowFp, exactMatches: slidingWindowExact, closeMatches: slidingWindowClose } = slidingWindowClassification;
        const canvas = createChartContainer('slidingWindow', `Sliding Window (N=${slidingWindowSize}, M=${slidingWindowOffset}, >${slidingWindowThreshold}%)`, '#14b8a6', slidingWindowTp, slidingWindowCm, slidingWindowFp);
        const ctx = canvas.getContext('2d');

        const slidingWindowPointColors = values.map((_, i) => {
            if (slidingWindowDetectedIndices.includes(i)) {
                if (slidingWindowExact.has(i)) return '#f87171';
                if (slidingWindowClose.has(i)) return '#fde047';
                return '#f97316';
            }
            return 'transparent';
        });
        const slidingWindowPointBorders = values.map((_, i) => {
            if (slidingWindowDetectedIndices.includes(i)) {
                if (slidingWindowExact.has(i)) return '#ef4444';
                if (slidingWindowClose.has(i)) return '#eab308';
                return '#ea580c';
            }
            return 'transparent';
        });
        const slidingWindowPointRadii = values.map((_, i) => slidingWindowDetectedIndices.includes(i) ? 6 : 0);
        const slidingWindowPointStyles = values.map((_, i) => {
            if (slidingWindowDetectedIndices.includes(i)) {
                if (slidingWindowExact.has(i)) return 'circle';
                if (slidingWindowClose.has(i)) return 'rectRot';
                return 'triangle';
            }
            return 'circle';
        });

        const isLast = enabledMethods[enabledMethods.length - 1] === 'slidingWindow';
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sliding Window Detection',
                    data: values,
                    borderColor: '#94a3b8',
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    borderWidth: 1.5,
                    fill: true,
                    tension: 0,
                    pointBackgroundColor: slidingWindowPointColors,
                    pointBorderColor: slidingWindowPointBorders,
                    pointBorderWidth: 1.5,
                    pointRadius: slidingWindowPointRadii,
                    pointHoverRadius: 8,
                    pointStyle: slidingWindowPointStyles,
                }]
            },
            options: getChartOptions(createAnnotations(), isLast)
        });
        stackedCharts.push(chart);
    }

    // Create Std Dev chart if enabled
    if (runStdDev) {
        const { tp: stdDevTp, cm: stdDevCm, fp: stdDevFp, exactMatches: stdDevExact, closeMatches: stdDevClose } = stdDevClassification;
        const canvas = createChartContainer('stdDev', `Std Dev (M=${stdDevWindow}, K=${stdDevNum}σ)`, '#a855f7', stdDevTp, stdDevCm, stdDevFp);
        const ctx = canvas.getContext('2d');

        const stdDevPointColors = values.map((_, i) => {
            if (stdDevDetectedIndices.includes(i)) {
                if (stdDevExact.has(i)) return '#f87171';
                if (stdDevClose.has(i)) return '#fde047';
                return '#f97316';
            }
            return 'transparent';
        });
        const stdDevPointBorders = values.map((_, i) => {
            if (stdDevDetectedIndices.includes(i)) {
                if (stdDevExact.has(i)) return '#ef4444';
                if (stdDevClose.has(i)) return '#eab308';
                return '#ea580c';
            }
            return 'transparent';
        });
        const stdDevPointRadii = values.map((_, i) => stdDevDetectedIndices.includes(i) ? 6 : 0);
        const stdDevPointStyles = values.map((_, i) => {
            if (stdDevDetectedIndices.includes(i)) {
                if (stdDevExact.has(i)) return 'circle';
                if (stdDevClose.has(i)) return 'rectRot';
                return 'triangle';
            }
            return 'circle';
        });

        const isLast = enabledMethods[enabledMethods.length - 1] === 'stdDev';
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Std Dev Detection',
                    data: values,
                    borderColor: '#94a3b8',
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    borderWidth: 1.5,
                    fill: true,
                    tension: 0,
                    pointBackgroundColor: stdDevPointColors,
                    pointBorderColor: stdDevPointBorders,
                    pointBorderWidth: 1.5,
                    pointRadius: stdDevPointRadii,
                    pointHoverRadius: 8,
                    pointStyle: stdDevPointStyles,
                }]
            },
            options: getChartOptions(createAnnotations(), isLast)
        });
        stackedCharts.push(chart);
    }

    // If no methods enabled, show a message
    if (enabledMethods.length === 0) {
        stackedChartsContainer.innerHTML = `
            <div class="stacked-chart" style="text-align: center; padding: 2rem;">
                <p style="color: #64748b;">Enable at least one analysis method to see the chart.</p>
            </div>
        `;
    }

    // Store MA result for stats display
    data._maResult = maResult;
    data._maClassification = maClassification;
}

// Update statistics display
function updateStats(data) {
    const values = data.data;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const std = Math.sqrt(
        values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length
    );

    statLength.textContent = values.length;
    statMean.textContent = mean.toFixed(2);
    statStd.textContent = std.toFixed(2);
    // Count only true change points (exclude outliers)
    const allCPs = data.ground_truth?.change_points || data.change_points || [];
    const trueChangePointCount = allCPs.filter(cp => cp.type !== 'outlier').length;
    statCpTruth.textContent = trueChangePointCount;
    statCpDetected.textContent = data.otava?.count ?? '-';
}

// Update accuracy metrics display
function updateAccuracyMetrics(data) {
    if (!data.accuracy) {
        metricPrecision.textContent = '-';
        metricRecall.textContent = '-';
        metricF1.textContent = '-';
        metricTp.textContent = '-';
        metricFp.textContent = '-';
        metricFn.textContent = '-';
        return;
    }

    const acc = data.accuracy;
    metricPrecision.textContent = (acc.precision * 100).toFixed(0) + '%';
    metricRecall.textContent = (acc.recall * 100).toFixed(0) + '%';
    metricF1.textContent = (acc.f1_score * 100).toFixed(0) + '%';
    metricTp.textContent = acc.true_positives;
    metricFp.textContent = acc.false_positives;
    metricFn.textContent = acc.false_negatives;
}

// Update comparison tables
function updateComparisonTables(data) {
    truthTableBody.innerHTML = '';
    detectedTableBody.innerHTML = '';

    const groundTruth = data.ground_truth?.change_points || data.change_points || [];
    const detected = data.otava?.detected_change_points || [];
    const matchedPairs = data.accuracy?.matched_pairs || [];

    const matchedTruthIndices = new Set(matchedPairs.map(p => p.ground_truth));
    const matchedDetectedIndices = new Set(matchedPairs.map(p => p.detected));

    // Ground truth table
    if (groundTruth.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" class="empty-message">No ground truth change points</td>';
        truthTableBody.appendChild(row);
    } else {
        groundTruth.forEach(cp => {
            const matched = matchedTruthIndices.has(cp.index);
            const matchInfo = matchedPairs.find(p => p.ground_truth === cp.index);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${cp.index}</strong></td>
                <td>${cp.type}</td>
                <td>${cp.description || '-'}</td>
                <td class="${matched ? 'status-matched' : 'status-missed'}">
                    ${matched ? `Yes (at ${matchInfo.detected})` : 'No'}
                </td>
            `;
            truthTableBody.appendChild(row);
        });
    }

    // Detected table
    if (detected.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="empty-message">No change points detected by Otava</td>';
        detectedTableBody.appendChild(row);
    } else {
        detected.forEach(cp => {
            const isTP = matchedDetectedIndices.has(cp.index);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${cp.index}</strong></td>
                <td>${cp.mean_before.toFixed(2)}</td>
                <td>${cp.mean_after.toFixed(2)}</td>
                <td>${cp.pvalue.toExponential(2)}</td>
                <td class="${isTP ? 'status-tp' : 'status-fp'}">
                    ${isTP ? 'True Positive' : 'False Positive'}
                </td>
            `;
            detectedTableBody.appendChild(row);
        });
    }
}

// Show all patterns with Otava comparison
async function showAllPatterns() {
    const length = lengthInput.value;
    const seed = seedInput.value;
    const windowLen = windowLenInput.value;
    const maxPvalue = maxPvalueInput.value;
    const tolerance = DEFAULT_TOLERANCE;

    try {
        document.body.classList.add('loading');

        // Fetch all generators with Otava analysis
        const results = {};
        let totalTP = 0, totalFP = 0, totalFN = 0;
        let patternsWithCP = 0;

        for (const name of Object.keys(generators)) {
            const params = new URLSearchParams({
                length,
                seed,
                window_len: windowLen,
                max_pvalue: maxPvalue,
                tolerance,
            });

            const response = await fetch(`/api/analyze/${name}?${params}`);
            const data = await response.json();

            if (!data.error) {
                results[name] = data;

                if (data.accuracy) {
                    totalTP += data.accuracy.true_positives;
                    totalFP += data.accuracy.false_positives;
                    totalFN += data.accuracy.false_negatives;
                    if (data.ground_truth?.count > 0) {
                        patternsWithCP++;
                    }
                }
            }
        }

        // Hide single chart view
        document.querySelector('.stacked-charts-container').classList.add('hidden');
        document.querySelector('.chart-legend').classList.add('hidden');
        statsSection.classList.add('hidden');
        accuracyMetrics.classList.add('hidden');
        cpDetail.classList.add('hidden');

        // Show multi-chart view
        multiChartContainer.classList.remove('hidden');

        // Update summary stats
        const overallPrecision = totalTP / (totalTP + totalFP) || 0;
        const overallRecall = totalTP / (totalTP + totalFN) || 0;
        const overallF1 = 2 * overallPrecision * overallRecall / (overallPrecision + overallRecall) || 0;

        summaryStats.innerHTML = `
            <div class="summary-stat">
                <h4>Patterns</h4>
                <span>${Object.keys(results).length}</span>
            </div>
            <div class="summary-stat">
                <h4>With CPs</h4>
                <span>${patternsWithCP}</span>
            </div>
            <div class="summary-stat">
                <h4>Total TP</h4>
                <span>${totalTP}</span>
            </div>
            <div class="summary-stat">
                <h4>Total FP</h4>
                <span>${totalFP}</span>
            </div>
            <div class="summary-stat">
                <h4>Total FN</h4>
                <span>${totalFN}</span>
            </div>
            <div class="summary-stat">
                <h4>Overall Precision</h4>
                <span>${(overallPrecision * 100).toFixed(0)}%</span>
            </div>
            <div class="summary-stat">
                <h4>Overall Recall</h4>
                <span>${(overallRecall * 100).toFixed(0)}%</span>
            </div>
            <div class="summary-stat">
                <h4>Overall F1</h4>
                <span>${(overallF1 * 100).toFixed(0)}%</span>
            </div>
        `;

        // Clear existing mini charts
        chartGrid.innerHTML = '';
        miniCharts.forEach(chart => chart.destroy());
        miniCharts = [];

        // Create mini charts for each generator
        for (const [name, data] of Object.entries(results)) {
            if (data.error) continue;

            const info = generators[name];

            const div = document.createElement('div');
            div.className = 'mini-chart';

            const title = document.createElement('h4');
            title.textContent = info ? info.name : name;

            const desc = document.createElement('p');
            desc.textContent = info ? info.description : '';

            const canvas = document.createElement('canvas');

            // Accuracy indicator
            const accuracyDiv = document.createElement('div');
            accuracyDiv.className = 'accuracy-indicator';

            if (data.accuracy && data.ground_truth?.count > 0) {
                const f1 = data.accuracy.f1_score;
                const colorClass = f1 >= 0.8 ? 'accuracy-good' : f1 >= 0.5 ? 'accuracy-medium' : 'accuracy-poor';
                accuracyDiv.innerHTML = `
                    <span>Truth: ${data.ground_truth.count}</span>
                    <span>Detected: ${data.otava?.count || 0}</span>
                    <span class="${colorClass}">F1: ${(f1 * 100).toFixed(0)}%</span>
                `;
            } else {
                accuracyDiv.innerHTML = `
                    <span>No CPs</span>
                    <span>Detected: ${data.otava?.count || 0}</span>
                    <span>${data.otava?.count > 0 ? 'FPs' : 'OK'}</span>
                `;
            }

            div.appendChild(title);
            div.appendChild(desc);
            div.appendChild(canvas);
            div.appendChild(accuracyDiv);
            chartGrid.appendChild(div);

            // Create mini chart
            const ctx = canvas.getContext('2d');
            // Exclude outliers from ground truth (they're anomalies, not change points)
            const allCPs = data.ground_truth?.change_points || [];
            const groundTruthIndices = allCPs
                .filter(cp => cp.type !== 'outlier')
                .map(cp => cp.index);
            const detectedIndices = data.otava?.detected_indices || [];
            const matchedPairs = data.accuracy?.matched_pairs || [];
            const matchedDetected = new Set(matchedPairs.map(p => p.detected));

            // Only show markers for Otava detected points (not ground truth)
            const pointBackgroundColors = data.data.map((_, i) => {
                if (detectedIndices.includes(i)) {
                    return matchedDetected.has(i) ? '#3b82f6' : '#ef4444';
                }
                return 'transparent';
            });

            const pointRadii = data.data.map((_, i) =>
                detectedIndices.includes(i) ? 4 : 0
            );

            // Create vertical line annotations for ground truth change points
            const miniAnnotations = {};
            groundTruthIndices.forEach((idx, i) => {
                miniAnnotations[`gt${i}`] = {
                    type: 'line',
                    xMin: idx,
                    xMax: idx,
                    borderColor: '#10b981',
                    borderWidth: 2,
                    borderDash: [4, 3],
                };
            });

            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.data.map((_, i) => i),
                    datasets: [{
                        data: data.data,
                        borderColor: '#94a3b8',
                        backgroundColor: 'rgba(148, 163, 184, 0.1)',
                        borderWidth: 1,
                        fill: true,
                        tension: 0,
                        pointBackgroundColor: pointBackgroundColors,
                        pointBorderColor: pointBackgroundColors,
                        pointRadius: pointRadii,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        annotation: {
                            annotations: miniAnnotations
                        }
                    },
                    scales: {
                        x: { display: false },
                        y: { min: parseInt(yMinInput.value), max: parseInt(yMaxInput.value), display: true, grid: { display: false } }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index',
                    }
                }
            });

            miniCharts.push(chart);

            // Click to view in main chart
            div.style.cursor = 'pointer';
            div.addEventListener('click', () => {
                selectGenerator(name);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

    } catch (error) {
        console.error('Failed to load all patterns:', error);
    } finally {
        document.body.classList.remove('loading');
    }
}

// Initialize dynamic params on load
updateDynamicParams();
