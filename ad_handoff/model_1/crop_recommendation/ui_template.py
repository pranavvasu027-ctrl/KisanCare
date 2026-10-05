"""Embedded HTML/JS frontend interface for Crop Recommendation System."""

HTML_UI: str = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Crop Recommendation & Rotation System</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #10b981;
            --primary-dark: #059669;
            --primary-light: #d1fae5;
            --secondary: #3b82f6;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            background-color: var(--bg);
            color: var(--text-main);
            line-height: 1.5;
            padding-bottom: 50px;
        }

        .header {
            background: linear-gradient(135deg, #064e3b 0%, #047857 50%, #059669 100%);
            color: white;
            padding: 36px 24px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        .header h1 {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }

        .header p {
            font-size: 1.05rem;
            opacity: 0.9;
            max-width: 800px;
            margin: 0 auto;
        }

        .badge-bar {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 16px;
            flex-wrap: wrap;
        }

        .badge {
            background: rgba(255,255,255,0.18);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 9999px;
            padding: 4px 14px;
            font-size: 0.85rem;
            font-weight: 500;
        }

        .container {
            max-width: 1280px;
            margin: -24px auto 0 auto;
            padding: 0 20px;
        }

        .grid-layout {
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 24px;
        }

        @media (max-width: 960px) {
            .grid-layout {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--card-bg);
            border-radius: 14px;
            border: 1px solid var(--border);
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
            margin-bottom: 24px;
        }

        .card-title {
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }

        .form-group {
            margin-bottom: 16px;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .form-row-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
        }

        label {
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            color: #334155;
            margin-bottom: 4px;
        }

        input[type="number"], select, input[type="text"] {
            width: 100%;
            padding: 9px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.92rem;
            background: #fff;
            color: var(--text-main);
            transition: border-color 0.2s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
        }

        .slider-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 4px;
        }

        .slider-row input[type="range"] {
            flex: 1;
            accent-color: var(--primary);
        }

        .slider-val {
            min-width: 45px;
            text-align: right;
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--primary-dark);
        }

        .btn-submit {
            width: 100%;
            background: var(--primary);
            color: white;
            padding: 14px 20px;
            font-size: 1rem;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.25);
            transition: all 0.2s;
            margin-top: 8px;
        }

        .btn-submit:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
        }

        .alert-box {
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            color: #065f46;
            border-radius: 10px;
            padding: 14px;
            font-size: 0.88rem;
            margin-bottom: 20px;
            line-height: 1.45;
        }

        .recommendation-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            background: #ffffff;
            transition: all 0.2s;
        }

        .recommendation-card:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
        }

        .rec-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .crop-badge {
            font-size: 1.3rem;
            font-weight: 700;
            color: #065f46;
            text-transform: capitalize;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .score-pill {
            background: #ecfdf5;
            border: 1px solid #10b981;
            color: #047857;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 1.05rem;
            font-weight: 700;
        }

        .score-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            background: #f8fafc;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
        }

        .score-item {
            text-align: center;
        }

        .score-item .label {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        .score-item .val {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-main);
        }

        .progress-bar {
            height: 6px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
        }

        .progress-fill {
            height: 100%;
            background: var(--primary);
            border-radius: 4px;
        }

        .reason-box {
            font-size: 0.88rem;
            color: #334155;
            line-height: 1.5;
            background: #fdfdfd;
            border-left: 3px solid var(--primary);
            padding: 8px 12px;
            border-radius: 0 6px 6px 0;
        }

        .source-tag {
            font-size: 0.74rem;
            color: var(--text-muted);
            margin-top: 8px;
            display: block;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>🌾 Smart Crop Recommendation System</h1>
        <p>Hugging Face ML Model + Independent Agronomic Crop-History &amp; Rotation Scoring Layer</p>
        <div class="badge-bar">
            <span class="badge">🤖 Model: Sheshank2609/crop-recommendation-system</span>
            <span class="badge">⚖️ Formula: 0.50 Soil + 0.30 Regional + 0.20 History</span>
            <span class="badge">🛡️ Soil-Test Primacy Guaranteed</span>
        </div>
    </div>

    <div class="container">
        <div class="grid-layout">
            <!-- INPUT PANEL -->
            <div>
                <form id="recommendForm" class="card">
                    <div class="card-title">🧪 1. Soil &amp; Climate Tests</div>
                    
                    <div class="form-row-3 form-group">
                        <div>
                            <label>Nitrogen (N)</label>
                            <input type="number" id="valN" value="90" step="1" required>
                        </div>
                        <div>
                            <label>Phosphorus (P)</label>
                            <input type="number" id="valP" value="42" step="1" required>
                        </div>
                        <div>
                            <label>Potassium (K)</label>
                            <input type="number" id="valK" value="43" step="1" required>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div>
                            <label>Soil pH (0 - 14)</label>
                            <input type="number" id="valPH" value="6.5" step="0.1" required>
                        </div>
                        <div>
                            <label>Temperature (°C)</label>
                            <input type="number" id="valTemp" value="25" step="0.5" required>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div>
                            <label>Humidity (%)</label>
                            <input type="number" id="valHum" value="80" step="1" required>
                        </div>
                        <div>
                            <label>Rainfall (mm)</label>
                            <input type="number" id="valRain" value="180" step="5" required>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>State / Agro-Climatic Zone</label>
                        <select id="valState">
                            <option value="West Bengal" selected>West Bengal</option>
                            <option value="Maharashtra">Maharashtra</option>
                            <option value="Punjab">Punjab</option>
                            <option value="Haryana">Haryana</option>
                            <option value="Uttar Pradesh">Uttar Pradesh</option>
                            <option value="Madhya Pradesh">Madhya Pradesh</option>
                            <option value="Gujarat">Gujarat</option>
                            <option value="Karnataka">Karnataka</option>
                            <option value="Tamil Nadu">Tamil Nadu</option>
                            <option value="Rajasthan">Rajasthan</option>
                        </select>
                    </div>

                    <div class="card-title" style="margin-top: 24px;">📜 2. Crop Rotation History</div>
                    
                    <div class="form-group">
                        <label>Current Crop (Standing / Just Harvested - T)</label>
                        <select id="curCrop">
                            <option value="">None / Fallow</option>
                            <option value="rice" selected>Rice / Paddy</option>
                            <option value="cotton">Cotton</option>
                            <option value="wheat">Wheat</option>
                            <option value="maize">Maize</option>
                            <option value="sugarcane">Sugarcane</option>
                            <option value="soybean">Soybean</option>
                            <option value="chickpea">Chickpea / Gram</option>
                            <option value="jute">Jute</option>
                            <option value="potato">Potato</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Previous 1 Crop (T-1)</label>
                        <select id="prev1Crop">
                            <option value="">None</option>
                            <option value="rice" selected>Rice / Paddy</option>
                            <option value="cotton">Cotton</option>
                            <option value="wheat">Wheat</option>
                            <option value="maize">Maize</option>
                            <option value="soybean">Soybean</option>
                            <option value="chickpea">Chickpea / Gram</option>
                            <option value="mustard">Mustard</option>
                        </select>
                    </div>

                    <div class="form-row form-group">
                        <div>
                            <label>Previous 2 (T-2)</label>
                            <select id="prev2Crop">
                                <option value="">None</option>
                                <option value="wheat" selected>Wheat</option>
                                <option value="rice">Rice</option>
                                <option value="soybean">Soybean</option>
                                <option value="cotton">Cotton</option>
                            </select>
                        </div>
                        <div>
                            <label>Previous 3 (T-3)</label>
                            <select id="prev3Crop">
                                <option value="">None</option>
                                <option value="rice">Rice</option>
                                <option value="wheat">Wheat</option>
                                <option value="soybean">Soybean</option>
                            </select>
                        </div>
                    </div>

                    <div class="card-title" style="margin-top: 24px;">⚖️ 3. Scoring Weights</div>
                    
                    <div class="form-group">
                        <label>Soil &amp; Climate Score Weight</label>
                        <div class="slider-row">
                            <input type="range" id="wSoil" min="0" max="1" step="0.05" value="0.50">
                            <span class="slider-val" id="wSoilVal">0.50</span>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Regional Suitability Weight</label>
                        <div class="slider-row">
                            <input type="range" id="wReg" min="0" max="1" step="0.05" value="0.30">
                            <span class="slider-val" id="wRegVal">0.30</span>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>History &amp; Rotation Weight</label>
                        <div class="slider-row">
                            <input type="range" id="wHist" min="0" max="1" step="0.05" value="0.20">
                            <span class="slider-val" id="wHistVal">0.20</span>
                        </div>
                    </div>

                    <button type="submit" class="btn-submit" id="submitBtn">🌱 Get Crop Recommendations</button>
                </form>
            </div>

            <!-- RESULTS PANEL -->
            <div>
                <div class="alert-box">
                    <strong>🛡️ Agronomic Separation Principle:</strong> The crop history layer is an independent rotation/nutrient-pressure layer and is <strong>not</strong> part of the Hugging Face model. Current soil-test NPK values remain the primary indicator of nutrient status.
                </div>

                <div class="card">
                    <div class="card-title">🏆 Recommended Crops Ranked by Final Score</div>
                    <div id="resultsContainer">
                        <p style="color: var(--text-muted); text-align: center; padding: 40px;">
                            Click <strong>"Get Crop Recommendations"</strong> to evaluate candidate crops using the real Hugging Face model and rotation engine.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Synchronize weight slider labels
        ['wSoil', 'wReg', 'wHist'].forEach(id => {
            const input = document.getElementById(id);
            const valSpan = document.getElementById(id + 'Val');
            input.addEventListener('input', () => {
                valSpan.textContent = Number(input.value).toFixed(2);
            });
        });

        const form = document.getElementById('recommendForm');
        const resultsContainer = document.getElementById('resultsContainer');
        const submitBtn = document.getElementById('submitBtn');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Calculating Recommendations...';

            const payload = {
                soil_climate: {
                    N: parseFloat(document.getElementById('valN').value),
                    P: parseFloat(document.getElementById('valP').value),
                    K: parseFloat(document.getElementById('valK').value),
                    ph: parseFloat(document.getElementById('valPH').value),
                    temperature: parseFloat(document.getElementById('valTemp').value),
                    humidity: parseFloat(document.getElementById('valHum').value),
                    rainfall: parseFloat(document.getElementById('valRain').value),
                    state: document.getElementById('valState').value
                },
                history: {
                    current_crop: document.getElementById('curCrop').value || null,
                    prev_crop_1: document.getElementById('prev1Crop').value || null,
                    prev_crop_2: document.getElementById('prev2Crop').value || null,
                    prev_crop_3: document.getElementById('prev3Crop').value || null
                },
                weights: {
                    soil_climate: parseFloat(document.getElementById('wSoil').value),
                    regional: parseFloat(document.getElementById('wReg').value),
                    history_rotation: parseFloat(document.getElementById('wHist').value)
                },
                top_k: 5
            };

            try {
                const res = await fetch('/api/v1/recommend', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                renderResults(data);
            } catch (err) {
                resultsContainer.innerHTML = `<p style="color:red;">Error fetching recommendations: ${err.message}</p>`;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '🌱 Get Crop Recommendations';
            }
        });

        function renderResults(data) {
            if (!data.recommendations || data.recommendations.length === 0) {
                resultsContainer.innerHTML = '<p>No recommendations returned.</p>';
                return;
            }

            let html = `
                <div style="display:flex; justify-content:space-between; margin-bottom:16px; font-size:0.85rem; color:#64748b;">
                    <span><strong>Model Source:</strong> ${data.model_source}</span>
                    <span><strong>Soil Status:</strong> N:${data.soil_test_npk_status.N}, P:${data.soil_test_npk_status.P}, K:${data.soil_test_npk_status.K}</span>
                </div>
            `;

            data.recommendations.forEach((rec, idx) => {
                const finalPct = Math.round(rec.final_score * 100);
                const soilPct = Math.round(rec.soil_climate_score * 100);
                const regPct = Math.round(rec.regional_score * 100);
                const histPct = Math.round(rec.history_rotation_score * 100);

                html += `
                    <div class="recommendation-card">
                        <div class="rec-header">
                            <div class="crop-badge">
                                <span>#${idx + 1}</span>
                                <span>${rec.crop}</span>
                            </div>
                            <div class="score-pill">
                                Final: ${rec.final_score.toFixed(4)}
                            </div>
                        </div>

                        <div class="score-grid">
                            <div class="score-item">
                                <div class="label">Soil/Climate (50%)</div>
                                <div class="val">${rec.soil_climate_score.toFixed(4)}</div>
                                <div class="progress-bar"><div class="progress-fill" style="width:${soilPct}%; background:#10b981;"></div></div>
                            </div>
                            <div class="score-item">
                                <div class="label">Regional (30%)</div>
                                <div class="val">${rec.regional_score.toFixed(4)}</div>
                                <div class="progress-bar"><div class="progress-fill" style="width:${regPct}%; background:#3b82f6;"></div></div>
                            </div>
                            <div class="score-item">
                                <div class="label">History/Rotation (20%)</div>
                                <div class="val">${rec.history_rotation_score.toFixed(4)}</div>
                                <div class="progress-bar"><div class="progress-fill" style="width:${histPct}%; background:#f59e0b;"></div></div>
                            </div>
                        </div>

                        <div class="reason-box">
                            <strong>Agronomic Reason:</strong> ${rec.reason}
                        </div>
                        <span class="source-tag">Source: ${rec.soil_climate_source || 'Hugging Face Model'}</span>
                    </div>
                `;
            });

            resultsContainer.innerHTML = html;
        }

        // Trigger default calculation immediately on page load
        window.addEventListener('DOMContentLoaded', () => {
            form.dispatchEvent(new Event('submit'));
        });
    </script>
</body>
</html>
"""
