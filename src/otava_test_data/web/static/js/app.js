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
let analysisMethods = {};  // Tutorial content for analysis methods
let tutorialVisible = false;  // Track tutorial panel visibility

// Mix Mode State
let mixMode = false;              // Single Pattern vs Mix Patterns mode
let mixOperation = 'sum';         // 'sum' or 'append'
let mixComponents = [];           // [{name, data, changePoints, params, count}]
let mixedData = null;             // Combined data array
let mixedChangePoints = [];       // Merged ground truth change points
let tileBadges = {};              // Track count badges on tiles

// DOM Elements - Data Generation
const generatorGrid = document.getElementById('generator-grid');
const lengthSlider = document.getElementById('length-slider');
const lengthInput = document.getElementById('length-input');
const lengthMin = document.getElementById('length-min');
const lengthMax = document.getElementById('length-max');
const seedInput = document.getElementById('seed-input');
const dynamicParams = document.getElementById('dynamic-params');

// DOM Elements - Mix Mode
const modeSingleBtn = document.getElementById('mode-single-btn');
const modeMixBtn = document.getElementById('mode-mix-btn');
const mixInfo = document.getElementById('mix-info');
const mixRecipe = document.getElementById('mix-recipe');
const clearMixBtn = document.getElementById('clear-mix-btn');

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
const accuracyTableBody = document.getElementById('accuracy-table-body');

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

// DOM Elements - Tutorial
const toggleTutorialBtn = document.getElementById('toggle-tutorial-btn');
const generatorTutorialPanel = document.getElementById('generator-tutorial-panel');
const tutorialExplanation = document.getElementById('tutorial-explanation');
const tutorialUseCase = document.getElementById('tutorial-use-case');
const tutorialDetectionNotes = document.getElementById('tutorial-detection-notes');
const methodHelpBtns = document.querySelectorAll('.method-help-btn');
const metricsHelpBtn = document.getElementById('metrics-help-btn');
const metricsTutorialPanel = document.getElementById('metrics-tutorial-panel');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([loadGenerators(), loadAnalysisMethods()]);
    await populateGeneratorGrid();
    setupEventListeners();
    setupTutorialHandlers();
    updateGeneratorInfo();
    updateDynamicParams();
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

// Load analysis method explanations
async function loadAnalysisMethods() {
    try {
        const response = await fetch('/api/methods');
        analysisMethods = await response.json();
        populateMethodTutorials();
    } catch (error) {
        console.error('Failed to load analysis methods:', error);
    }
}

// Populate method tutorial panels with content from API
function populateMethodTutorials() {
    // Populate Otava tutorial
    if (analysisMethods.otava) {
        const otavaTutorial = document.getElementById('otava-tutorial');
        if (otavaTutorial) {
            otavaTutorial.querySelector('.method-explanation').textContent = analysisMethods.otava.explanation;
            otavaTutorial.querySelector('.method-algorithm pre').textContent = analysisMethods.otava.algorithm;
            const bestForList = otavaTutorial.querySelector('.method-best-for ul');
            bestForList.innerHTML = analysisMethods.otava.best_for.map(item => `<li>${item}</li>`).join('');
        }
    }

    // Populate Moving Average tutorial
    if (analysisMethods.moving_average) {
        const maTutorial = document.getElementById('ma-tutorial');
        if (maTutorial) {
            maTutorial.querySelector('.method-explanation').textContent = analysisMethods.moving_average.explanation;
            maTutorial.querySelector('.method-algorithm pre').textContent = analysisMethods.moving_average.algorithm;
            const bestForList = maTutorial.querySelector('.method-best-for ul');
            bestForList.innerHTML = analysisMethods.moving_average.best_for.map(item => `<li>${item}</li>`).join('');
        }
    }

    // Populate Boundary tutorial
    if (analysisMethods.boundary) {
        const boundaryTutorial = document.getElementById('boundary-tutorial');
        if (boundaryTutorial) {
            boundaryTutorial.querySelector('.method-explanation').textContent = analysisMethods.boundary.explanation;
            boundaryTutorial.querySelector('.method-algorithm pre').textContent = analysisMethods.boundary.algorithm;
            const bestForList = boundaryTutorial.querySelector('.method-best-for ul');
            bestForList.innerHTML = analysisMethods.boundary.best_for.map(item => `<li>${item}</li>`).join('');
        }
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

    const generatorNames = Object.keys(generators);

    if (mixMode) {
        // Mix mode layout: Single row with clean patterns + noise + operation toggle
        const mixRow1Order = [
            'constant',
            'noise_normal',
            'noise_uniform',
            'outlier_clean',
            'step_function_clean',
            'regression_fix_clean',
            'amplitude_change_clean',
            'phase_change_clean',
            'banding_clean'
        ];
        const mixRow1Names = mixRow1Order;//.filter(name => generatorNames.includes(name));

        // Create pattern tiles
        for (const name of mixRow1Names) {
            const info = generators[name];
            const tile = createGeneratorTile(name, info, previewData[name], true);
            generatorGrid.appendChild(tile);
        }

        // Operation toggle tile at the end
        const opTile = document.createElement('div');
        opTile.className = 'generator-tile operation-tile';
        opTile.innerHTML = `
            <div class="op-label">${mixOperation.toUpperCase()}</div>
            <div class="op-hint">Click to toggle</div>
        `;
        opTile.addEventListener('click', toggleMixOperation);
        generatorGrid.appendChild(opTile);

        // Update badges for existing mix components
        updateTileBadges();

    } else {
        // Single mode layout: Original 4 rows
        const orderedNames = [];

        // Row 1 - single clean patterns
        const row1Order = [
            'constant',
            'outlier_clean',
            'step_function_clean',
            'regression_fix_clean',
            'amplitude_change_clean',
            'phase_change_clean',
            'banding_clean',
        ];
        const row1Names = row1Order;//.filter(name => generatorNames.includes(name));
        orderedNames.push(...row1Names);

        // Row 2 - multiple clean patterns (with placeholder)
        const row2Order = [
            '__placeholder__',
            'multiple_outliers_clean',
            'multiple_changes',
            'multiple_regression_fix_clean',
            'multiple_amplitude_changes_clean',
            'multiple_phase_changes_clean',
            'multiple_banding_clean'
        ];
        const row2Names = row2Order;
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
        const row3Names = row3Order;//.filter(name => generatorNames.includes(name));
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
        const row4Names = row4Order;//.filter(name => generatorNames.includes(name));
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
            console.info(name);
            console.info(info);
            const tile = createGeneratorTile(name, info, previewData[name], false);
            generatorGrid.appendChild(tile);

            // Add line breaks after each row
            if (tileIndex === row1EndIndex || tileIndex === row2EndIndex ||
                tileIndex === row3EndIndex || tileIndex === row4EndIndex) {
                const lineBreak = document.createElement('div');
                lineBreak.className = 'generator-grid-break';
                generatorGrid.appendChild(lineBreak);
            }
        }
    }

    // Apply mix mode class to grid
    generatorGrid.classList.toggle('mix-mode', mixMode);
}

/**
 * Create a generator tile element
 */
function createGeneratorTile(name, info, preview, isMixMode) {
    const tile = document.createElement('div');
    tile.className = 'generator-tile' + (!isMixMode && name === selectedGenerator ? ' selected' : '');
    tile.dataset.generator = name;

    // Preview container
    const previewDiv = document.createElement('div');
    previewDiv.className = 'generator-tile-preview';
    const canvas = document.createElement('canvas');
    canvas.id = `preview-${name}`;
    previewDiv.appendChild(canvas);

    // Name label
    const label = document.createElement('div');
    label.className = 'generator-tile-name';
    label.textContent = info.name;

    tile.appendChild(previewDiv);
    tile.appendChild(label);

    // Click handler - different for mix mode vs single mode
    if (isMixMode) {
        tile.addEventListener('click', () => addToMix(name));
    } else {
        tile.addEventListener('click', () => selectGenerator(name));
    }

    // Create mini chart
    if (preview && preview.data) {
        createTileChart(canvas, preview.data, !isMixMode && name === selectedGenerator);
    }

    return tile;
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

// Setup tutorial event handlers
function setupTutorialHandlers() {
    // Generator tutorial toggle
    if (toggleTutorialBtn) {
        toggleTutorialBtn.addEventListener('click', () => {
            tutorialVisible = !tutorialVisible;
            if (tutorialVisible) {
                generatorTutorialPanel.classList.remove('hidden');
                toggleTutorialBtn.classList.add('active');
            } else {
                generatorTutorialPanel.classList.add('hidden');
                toggleTutorialBtn.classList.remove('active');
            }
        });
    }

    // Metrics tutorial toggle
    if (metricsHelpBtn && metricsTutorialPanel) {
        metricsHelpBtn.addEventListener('click', () => {
            const isVisible = !metricsTutorialPanel.classList.contains('hidden');
            if (isVisible) {
                metricsTutorialPanel.classList.add('hidden');
                metricsHelpBtn.classList.remove('active');
            } else {
                metricsTutorialPanel.classList.remove('hidden');
                metricsHelpBtn.classList.add('active');
            }
        });
    }

    // Method help button handlers
    methodHelpBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const methodId = btn.dataset.method;
            const tutorialId = methodId === 'moving_average' ? 'ma-tutorial' : `${methodId}-tutorial`;
            const tutorialPanel = document.getElementById(tutorialId);

            if (tutorialPanel) {
                const isVisible = !tutorialPanel.classList.contains('hidden');
                // Hide all method tutorials first
                document.querySelectorAll('.method-tutorial').forEach(panel => {
                    panel.classList.add('hidden');
                });
                document.querySelectorAll('.method-help-btn').forEach(b => {
                    b.classList.remove('active');
                });

                // Toggle the clicked one
                if (!isVisible) {
                    tutorialPanel.classList.remove('hidden');
                    btn.classList.add('active');
                }
            }
        });
    });

    // Initialize tooltips for parameter labels
    initializeTooltips();
}

// Initialize custom tooltips for parameter labels and help buttons
function initializeTooltips() {
    document.querySelectorAll('.param-label[data-tooltip]').forEach(label => {
        label.addEventListener('mouseenter', showTooltip);
        label.addEventListener('mouseleave', hideTooltip);
    });

    // Parameter help buttons - show tooltip on click
    document.querySelectorAll('.param-help-btn[data-tooltip]').forEach(btn => {
        btn.addEventListener('click', toggleParamTooltip);
    });

    // Close tooltips when clicking elsewhere
    document.addEventListener('click', (e) => {
        if (!e.target.classList.contains('param-help-btn')) {
            document.querySelectorAll('.param-tooltip-popup').forEach(t => t.remove());
            document.querySelectorAll('.param-help-btn').forEach(b => b.classList.remove('active'));
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

// Toggle tooltip popup for param help buttons
function toggleParamTooltip(e) {
    e.stopPropagation();
    const btn = e.target;
    const tooltipText = btn.dataset.tooltip;
    if (!tooltipText) return;

    // Check if already showing
    if (btn._tooltipPopup) {
        btn._tooltipPopup.remove();
        btn._tooltipPopup = null;
        btn.classList.remove('active');
        return;
    }

    // Close other tooltips
    document.querySelectorAll('.param-tooltip-popup').forEach(t => t.remove());
    document.querySelectorAll('.param-help-btn').forEach(b => {
        b._tooltipPopup = null;
        b.classList.remove('active');
    });

    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'param-tooltip-popup';
    tooltip.textContent = tooltipText;
    document.body.appendChild(tooltip);

    // Position tooltip
    const rect = btn.getBoundingClientRect();
    tooltip.style.left = `${rect.left}px`;
    tooltip.style.top = `${rect.bottom + 5}px`;

    // Store reference
    btn._tooltipPopup = tooltip;
    btn.classList.add('active');
}

// Show tooltip
function showTooltip(e) {
    const label = e.target;
    const tooltipText = label.dataset.tooltip;
    if (!tooltipText) return;

    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'param-tooltip';
    tooltip.textContent = tooltipText;
    document.body.appendChild(tooltip);

    // Position tooltip
    const rect = label.getBoundingClientRect();
    tooltip.style.left = `${rect.left}px`;
    tooltip.style.top = `${rect.bottom + 5}px`;

    // Store reference for removal
    label._tooltip = tooltip;
}

// Hide tooltip
function hideTooltip(e) {
    const label = e.target;
    if (label._tooltip) {
        label._tooltip.remove();
        label._tooltip = null;
    }
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

    // Mix mode controls
    modeSingleBtn.addEventListener('click', () => toggleMixMode(false));
    modeMixBtn.addEventListener('click', () => toggleMixMode(true));
    clearMixBtn.addEventListener('click', clearMix);

    // Otava controls
    runOtavaCheckbox.addEventListener('change', refreshDisplay);
    windowLenInput.addEventListener('change', refreshDisplay);
    maxPvalueInput.addEventListener('change', refreshDisplay);

    // Y-Axis Min slider with bounds
    setupSliderWithBounds(yMinSlider, yMinInput, yMinBoundMin, yMinBoundMax, refreshDisplay);

    // Y-Axis Max slider with bounds
    setupSliderWithBounds(yMaxSlider, yMaxInput, yMaxBoundMin, yMaxBoundMax, refreshDisplay);

    // Moving Average controls
    runMaCheckbox.addEventListener('change', refreshDisplay);
    maWindowInput.addEventListener('change', refreshDisplay);
    maThresholdInput.addEventListener('change', refreshDisplay);

    // Boundary controls
    runBoundaryCheckbox.addEventListener('change', refreshDisplay);
    boundaryUpperInput.addEventListener('change', refreshDisplay);
    boundaryLowerInput.addEventListener('change', refreshDisplay);

    // Threshold Alert controls
    runThresholdCheckbox.addEventListener('change', refreshDisplay);
    thresholdPercentInput.addEventListener('change', refreshDisplay);
    thresholdOffsetInput.addEventListener('change', refreshDisplay);

    // Sliding Window controls
    runSlidingWindowCheckbox.addEventListener('change', refreshDisplay);
    slidingWindowSizeInput.addEventListener('change', refreshDisplay);
    slidingWindowOffsetInput.addEventListener('change', refreshDisplay);
    slidingWindowThresholdInput.addEventListener('change', refreshDisplay);

    // Std Dev controls
    runStdDevCheckbox.addEventListener('change', refreshDisplay);
    stdDevWindowInput.addEventListener('change', refreshDisplay);
    stdDevNumInput.addEventListener('change', refreshDisplay);
}

// Update generator info display
function updateGeneratorInfo() {
    if (mixMode && mixComponents.length > 0) {
        // Mix mode with components
        const totalCPs = mixedChangePoints ? mixedChangePoints.filter(cp => cp.type !== 'outlier').length : 0;
        generatorTitle.textContent = 'Mixed Pattern';
        const opText = mixOperation === 'sum' ? 'Sum' : 'Append';
        generatorDescription.textContent = `${mixComponents.length} component(s) combined using ${opText} operation`;

        if (totalCPs > 0) {
            changePointInfo.classList.remove('hidden');
        } else {
            changePointInfo.classList.add('hidden');
        }
        return;
    }

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

        // Update tutorial panel content
        if (info.tutorial) {
            tutorialExplanation.textContent = info.tutorial.explanation || '-';
            tutorialUseCase.textContent = info.tutorial.use_case || '-';
            tutorialDetectionNotes.textContent = info.tutorial.detection_notes || '-';
        } else {
            tutorialExplanation.textContent = '-';
            tutorialUseCase.textContent = '-';
            tutorialDetectionNotes.textContent = '-';
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

            // Create input container with input and optional help button
            const inputContainer = document.createElement('div');
            inputContainer.className = 'input-with-help';

            const input = document.createElement('input');
            input.type = paramInfo.type;
            input.id = `param-${paramName}`;
            input.name = paramName;
            input.value = paramInfo.default;
            input.min = paramInfo.min;
            input.max = paramInfo.max;
            input.step = paramInfo.step || 1;
            input.addEventListener('change', generateData);
            inputContainer.appendChild(input);

            // Add help button if tooltip exists
            if (paramInfo.tooltip) {
                const helpBtn = document.createElement('button');
                helpBtn.type = 'button';
                helpBtn.className = 'param-help-btn';
                helpBtn.dataset.tooltip = paramInfo.tooltip;
                helpBtn.textContent = '?';
                helpBtn.addEventListener('click', toggleParamTooltip);
                inputContainer.appendChild(helpBtn);
            }

            div.appendChild(label);
            div.appendChild(inputContainer);
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

    // Store all results for accuracy metrics display
    data._methodResults = {
        otava: runOtavaCheckbox.checked ? {
            name: 'Otava',
            classification: otavaClassification,
            detectedIndices: detectedIndices
        } : null,
        ma: runMa ? {
            name: 'Moving Average',
            classification: maClassification,
            detectedIndices: maDetectedIndices
        } : null,
        boundary: runBoundary ? {
            name: 'Boundary',
            classification: boundaryClassification,
            detectedIndices: boundaryDetectedIndices
        } : null,
        threshold: runThreshold ? {
            name: 'Threshold Alert',
            classification: thresholdClassification,
            detectedIndices: thresholdDetectedIndices
        } : null,
        slidingWindow: runSlidingWindow ? {
            name: 'Sliding Window',
            classification: slidingWindowClassification,
            detectedIndices: slidingWindowDetectedIndices
        } : null,
        stdDev: runStdDev ? {
            name: 'Std Dev',
            classification: stdDevClassification,
            detectedIndices: stdDevDetectedIndices
        } : null
    };
    data._groundTruthCount = groundTruthIndices.length;
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
    // Clear the table
    accuracyTableBody.innerHTML = '';

    const methodResults = data._methodResults;
    const groundTruthCount = data._groundTruthCount || 0;

    if (!methodResults) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="8" class="empty-message">No analysis methods enabled</td>';
        accuracyTableBody.appendChild(row);
        return;
    }

    // Add a row for each enabled method
    const methodOrder = ['otava', 'ma', 'boundary', 'threshold', 'slidingWindow', 'stdDev'];
    let hasAnyMethod = false;

    for (const methodKey of methodOrder) {
        const method = methodResults[methodKey];
        if (!method) continue;

        hasAnyMethod = true;
        const { tp, cm, fp } = method.classification;

        // FN = ground truth not matched by any detection (exact or close)
        // Since each method is evaluated independently, FN = groundTruthCount - (tp + cm)
        const fn = Math.max(0, groundTruthCount - tp - cm);

        // Calculate precision, recall, F1
        // For precision: TP+CM are "good" detections, FP are bad
        const totalDetected = tp + cm + fp;
        const precision = totalDetected > 0 ? (tp + cm) / totalDetected : 0;

        // For recall: how many ground truth were found (exactly or closely)
        const recall = groundTruthCount > 0 ? (tp + cm) / groundTruthCount : 0;

        // F1 score
        const f1 = (precision + recall) > 0 ? 2 * precision * recall / (precision + recall) : 0;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${method.name}</strong></td>
            <td>${tp}</td>
            <td>${cm}</td>
            <td>${fp}</td>
            <td>${fn}</td>
            <td>${(precision * 100).toFixed(0)}%</td>
            <td>${(recall * 100).toFixed(0)}%</td>
            <td>${(f1 * 100).toFixed(0)}%</td>
        `;
        accuracyTableBody.appendChild(row);
    }

    if (!hasAnyMethod) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="8" class="empty-message">No analysis methods enabled</td>';
        accuracyTableBody.appendChild(row);
    }
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

// ==========================================
// Mix Mode Functions
// ==========================================

/**
 * Refresh the current display - calls the appropriate update function based on mode
 */
function refreshDisplay() {
    if (mixMode && mixComponents.length > 0) {
        computeAndDisplayMixedData();
    } else {
        generateData();
    }
}

/**
 * Toggle between Single Pattern and Mix Patterns mode
 */
function toggleMixMode(enable) {
    mixMode = enable;

    // Update button states
    modeSingleBtn.classList.toggle('active', !enable);
    modeMixBtn.classList.toggle('active', enable);

    // Toggle mix info visibility
    mixInfo.classList.toggle('hidden', !enable);

    // Toggle grid class
    generatorGrid.classList.toggle('mix-mode', enable);

    // Clear mix state when switching modes
    if (enable) {
        clearMix();
        updateMixDisplay();
    } else {
        // Clear badges and restore normal tile behavior
        clearMix();
        // Re-render the selected generator in single mode
        if (selectedGenerator) {
            generateData();
        }
    }

    // Rebuild grid for mix mode layout
    populateGeneratorGrid();
}

/**
 * Toggle between Sum and Append operations
 */
function toggleMixOperation() {
    mixOperation = mixOperation === 'sum' ? 'append' : 'sum';
    updateMixDisplay();
    if (mixComponents.length > 0) {
        computeAndDisplayMixedData();
    }
    // Update the operation tile
    const opTile = document.querySelector('.operation-tile');
    if (opTile) {
        const opLabel = opTile.querySelector('.op-label');
        if (opLabel) {
            opLabel.textContent = mixOperation.toUpperCase();
        }
    }
}

/**
 * Patterns that should have randomized x-axis positions when added to mix
 */
const RANDOMIZE_POSITION_PATTERNS = [
    'outlier', 'outlier_clean', 'outlier_uniform',
    'step_function', 'step_function_clean', 'step_function_uniform',
    'regression_fix', 'regression_fix_clean', 'regression_fix_uniform'
];

/**
 * Shift an array by a given offset, padding with the first value (no wrapping)
 * Positive offset shifts the pattern to the right
 */
function shiftArray(arr, offset) {
    if (offset === 0) return [...arr];
    const n = arr.length;
    const firstVal = arr[0];

    if (offset > 0) {
        // Shift right: pad beginning with first value, truncate end
        const padding = new Array(offset).fill(firstVal);
        return [...padding, ...arr.slice(0, n - offset)];
    } else {
        // Shift left: truncate beginning, pad end with last value
        const lastVal = arr[n - 1];
        const padding = new Array(-offset).fill(lastVal);
        return [...arr.slice(-offset), ...padding];
    }
}

/**
 * Add a generator to the mix
 */
async function addToMix(generatorName) {
    const length = parseInt(lengthInput.value);
    const seed = parseInt(seedInput.value);

    try {
        document.body.classList.add('loading');

        // Fetch data for this generator
        const params = new URLSearchParams({ length, seed });
        const response = await fetch(`/api/generate/${generatorName}?${params}`);
        const result = await response.json();

        if (result.error) {
            console.error('Error fetching generator data:', result.error);
            return;
        }

        let data = result.data;
        let changePoints = result.ground_truth?.change_points || result.change_points || [];

        // For certain patterns, randomize the x-axis position by shifting the data
        if (RANDOMIZE_POSITION_PATTERNS.includes(generatorName)) {
            // Generate a random offset (can be positive or negative, avoiding edges)
            const margin = Math.floor(length * 0.15);  // 15% margin from edges
            const maxShift = Math.floor(length * 0.35);  // Max 35% shift in either direction
            const randomOffset = Math.floor(Math.random() * (2 * maxShift + 1)) - maxShift;

            // Shift the data array (no wrapping)
            data = shiftArray(data, randomOffset);

            // Adjust change point indices, clamping to valid range
            changePoints = changePoints.map(cp => ({
                ...cp,
                index: Math.max(0, Math.min(length - 1, cp.index + randomOffset))
            }));
        }

        // Check if this generator is already in the mix
        const existingIdx = mixComponents.findIndex(c => c.name === generatorName);
        if (existingIdx >= 0) {
            // For patterns with randomized positions, always add as new instance
            if (RANDOMIZE_POSITION_PATTERNS.includes(generatorName)) {
                mixComponents[existingIdx].count++;
                // Store additional instances with their own data/changePoints
                if (!mixComponents[existingIdx].instances) {
                    mixComponents[existingIdx].instances = [{
                        data: mixComponents[existingIdx].data,
                        changePoints: mixComponents[existingIdx].changePoints
                    }];
                }
                mixComponents[existingIdx].instances.push({ data, changePoints });
            } else {
                // Increment count for non-randomized patterns
                mixComponents[existingIdx].count++;
            }
        } else {
            // Add new component
            const component = {
                name: generatorName,
                displayName: generators[generatorName]?.name || generatorName,
                data: data,
                changePoints: changePoints,
                params: { length, seed },
                count: 1
            };
            // For randomizable patterns, track instances
            if (RANDOMIZE_POSITION_PATTERNS.includes(generatorName)) {
                component.instances = [{ data, changePoints }];
            }
            mixComponents.push(component);
        }

        // Update display
        updateMixDisplay();
        updateTileBadges();
        computeAndDisplayMixedData();

    } catch (error) {
        console.error('Failed to add generator to mix:', error);
    } finally {
        document.body.classList.remove('loading');
    }
}

/**
 * Remove one instance of a generator from the mix
 */
function removeFromMix(generatorName) {
    const idx = mixComponents.findIndex(c => c.name === generatorName);
    if (idx >= 0) {
        const comp = mixComponents[idx];
        comp.count--;

        // For patterns with instances, also remove the last instance
        if (comp.instances && comp.instances.length > 0) {
            comp.instances.pop();
        }

        if (comp.count <= 0) {
            mixComponents.splice(idx, 1);
        }

        updateMixDisplay();
        updateTileBadges();
        if (mixComponents.length > 0) {
            computeAndDisplayMixedData();
        } else {
            // Clear charts when no components
            stackedChartsContainer.innerHTML = `
                <div class="stacked-chart" style="text-align: center; padding: 2rem;">
                    <p style="color: #64748b;">Click patterns to add to the mix...</p>
                </div>
            `;
        }
    }
}

/**
 * Clear all mix state
 */
function clearMix() {
    mixComponents = [];
    mixedData = null;
    mixedChangePoints = [];
    mixOperation = 'sum';
    tileBadges = {};
    updateMixDisplay();
    updateTileBadges();

    if (mixMode) {
        // Clear charts
        stackedChartsContainer.innerHTML = `
            <div class="stacked-chart" style="text-align: center; padding: 2rem;">
                <p style="color: #64748b;">Click patterns to add to the mix...</p>
            </div>
        `;
        // Reset generator info
        generatorTitle.textContent = 'Mix Patterns';
        generatorDescription.textContent = 'Click on patterns to combine them';
        changePointInfo.classList.add('hidden');

        // Update the operation tile
        const opTile = document.querySelector('.operation-tile');
        if (opTile) {
            const opLabel = opTile.querySelector('.op-label');
            if (opLabel) {
                opLabel.textContent = 'SUM';
            }
        }
    }
}

/**
 * Sum operation: add data arrays element-wise, cycling shorter arrays
 * Then normalize to keep the mean at a reasonable baseline
 */
function sumMix(components) {
    if (components.length === 0) return { data: [], changePoints: [] };

    // Calculate max length considering counts
    let maxLen = 0;
    for (const comp of components) {
        maxLen = Math.max(maxLen, comp.data.length);
    }

    // Initialize result array
    const result = new Array(maxLen).fill(0);
    const allChangePoints = [];

    // Add each component
    for (const comp of components) {
        if (comp.instances) {
            // For patterns with randomized positions, use each instance's data
            for (const instance of comp.instances) {
                for (let j = 0; j < maxLen; j++) {
                    result[j] += instance.data[j % instance.data.length];
                }
                // Collect change points from each instance
                for (const cp of instance.changePoints) {
                    allChangePoints.push({ ...cp });
                }
            }
        } else {
            // For regular patterns, use count
            for (let i = 0; i < comp.count; i++) {
                for (let j = 0; j < maxLen; j++) {
                    result[j] += comp.data[j % comp.data.length];
                }
            }
            // Collect change points (once per component type for non-instance patterns)
            for (const cp of comp.changePoints) {
                allChangePoints.push({ ...cp });
            }
        }
    }

    // Deduplicate change points by index+type
    const changePointsMap = {};
    for (const cp of allChangePoints) {
        const key = `${cp.index}-${cp.type}`;
        if (!changePointsMap[key]) {
            changePointsMap[key] = cp;
        }
    }

    // Normalize: shift the result so the mean matches the first component's mean
    const firstData = components[0].instances ? components[0].instances[0].data : components[0].data;
    const targetMean = firstData.reduce((a, b) => a + b, 0) / firstData.length;
    const currentMean = result.reduce((a, b) => a + b, 0) / result.length;
    const shift = targetMean - currentMean;

    for (let i = 0; i < result.length; i++) {
        result[i] += shift;
    }

    return {
        data: result,
        changePoints: Object.values(changePointsMap)
    };
}

/**
 * Append operation: concatenate data arrays, offsetting change points
 */
function appendMix(components) {
    if (components.length === 0) return { data: [], changePoints: [] };

    const result = [];
    const changePoints = [];
    let offset = 0;

    for (const comp of components) {
        if (comp.instances) {
            // For patterns with randomized positions, use each instance
            for (const instance of comp.instances) {
                result.push(...instance.data);

                for (const cp of instance.changePoints) {
                    changePoints.push({
                        ...cp,
                        index: cp.index + offset,
                        description: `${cp.description || cp.type} (from ${comp.displayName})`
                    });
                }

                offset += instance.data.length;
            }
        } else {
            // For regular patterns, use count
            for (let i = 0; i < comp.count; i++) {
                result.push(...comp.data);

                for (const cp of comp.changePoints) {
                    changePoints.push({
                        ...cp,
                        index: cp.index + offset,
                        description: `${cp.description || cp.type} (from ${comp.displayName})`
                    });
                }

                offset += comp.data.length;
            }
        }
    }

    return { data: result, changePoints };
}

/**
 * Compute mixed data based on current operation
 */
function computeMixedData() {
    if (mixComponents.length === 0) {
        mixedData = null;
        mixedChangePoints = [];
        return;
    }

    const mixResult = mixOperation === 'sum'
        ? sumMix(mixComponents)
        : appendMix(mixComponents);

    mixedData = mixResult.data;
    mixedChangePoints = mixResult.changePoints;
}

/**
 * Compute mixed data and display in charts
 */
async function computeAndDisplayMixedData() {
    computeMixedData();

    if (!mixedData || mixedData.length === 0) {
        return;
    }

    // Create a fake response object to pass to updateChart
    const fakeData = {
        generator: 'mixed',
        data: mixedData,
        ground_truth: {
            change_points: mixedChangePoints,
            count: mixedChangePoints.filter(cp => cp.type !== 'outlier').length
        },
        otava: null,  // Will be computed by updateChart if checkbox is enabled
    };

    // Run Otava analysis on mixed data if enabled
    if (runOtavaCheckbox.checked) {
        try {
            const params = new URLSearchParams({
                window_len: windowLenInput.value,
                max_pvalue: maxPvalueInput.value,
            });
            const response = await fetch(`/api/detect?${params}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: mixedData })
            });
            const otavaResult = await response.json();
            if (!otavaResult.error) {
                fakeData.otava = otavaResult;
            }
        } catch (error) {
            console.error('Failed to run Otava on mixed data:', error);
        }
    }

    updateChart(fakeData);
    updateStats(fakeData);
    updateAccuracyMetrics(fakeData);
    updateMixComparisonTables(fakeData);
    updateGeneratorInfo();

    // Show chart sections
    document.querySelector('.stacked-charts-container').classList.remove('hidden');
    document.querySelector('.chart-legend').classList.remove('hidden');
    statsSection.classList.remove('hidden');
    accuracyMetrics.classList.remove('hidden');
    cpDetail.classList.remove('hidden');
    multiChartContainer.classList.add('hidden');
}

/**
 * Update comparison tables for mix mode
 */
function updateMixComparisonTables(data) {
    truthTableBody.innerHTML = '';
    detectedTableBody.innerHTML = '';

    const groundTruth = data.ground_truth?.change_points || [];
    const detected = data.otava?.detected_change_points || [];

    // Ground truth table
    if (groundTruth.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" class="empty-message">No ground truth change points</td>';
        truthTableBody.appendChild(row);
    } else {
        groundTruth.forEach(cp => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${cp.index}</strong></td>
                <td>${cp.type}</td>
                <td>${cp.description || '-'}</td>
                <td>-</td>
            `;
            truthTableBody.appendChild(row);
        });
    }

    // Detected table
    if (!detected || detected.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="empty-message">No change points detected by Otava</td>';
        detectedTableBody.appendChild(row);
    } else {
        detected.forEach(cp => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${cp.index}</strong></td>
                <td>${cp.mean_before?.toFixed(2) || '-'}</td>
                <td>${cp.mean_after?.toFixed(2) || '-'}</td>
                <td>${cp.pvalue?.toExponential(2) || '-'}</td>
                <td>-</td>
            `;
            detectedTableBody.appendChild(row);
        });
    }
}

/**
 * Update the mix recipe display
 */
function updateMixDisplay() {
    if (mixComponents.length === 0) {
        mixRecipe.innerHTML = 'Click patterns to add...';
        return;
    }

    const parts = mixComponents.map(comp => {
        const countStr = comp.count > 1 ? `${comp.count}x ` : '';
        return `<span class="component">${countStr}${comp.displayName}</span>`;
    });

    const opSymbol = mixOperation === 'sum' ? '+' : '&rarr;';
    mixRecipe.innerHTML = parts.join(`<span class="operation"> ${opSymbol} </span>`);
}

/**
 * Update count badges on tiles
 */
function updateTileBadges() {
    // Remove all existing badges
    document.querySelectorAll('.tile-count-badge').forEach(badge => badge.remove());

    // Remove in-mix class from all tiles
    document.querySelectorAll('.generator-tile').forEach(tile => {
        tile.classList.remove('in-mix');
    });

    if (!mixMode) return;

    // Add badges for components in mix
    for (const comp of mixComponents) {
        const tile = document.querySelector(`.generator-tile[data-generator="${comp.name}"]`);
        if (tile) {
            tile.classList.add('in-mix');
            if (comp.count > 0) {
                const badge = document.createElement('div');
                badge.className = 'tile-count-badge';
                badge.textContent = comp.count;
                tile.appendChild(badge);
            }
        }
    }
}

// Initialize dynamic params on load
updateDynamicParams();
