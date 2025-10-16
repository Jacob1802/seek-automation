#!/usr/bin/env python3
"""
Simple Job Application Dashboard
Run with: uv python dashboard.py [path/to/applied.json]
Then open: http://localhost:8000
"""

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import FastAPI, HTTPException
from pathlib import Path
import json
import sys
import uvicorn

app = FastAPI()

# File path configuration - can be overridden via CLI
DEFAULT_PATH = "application_pipeline/application_materials/applied.json"
DATA_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_PATH)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Application Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #2c3e50; margin-bottom: 10px; }
        .subtitle { color: #7f8c8d; margin-bottom: 30px; }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 14px;
        }
        
        .filters {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .filters h3 { margin-bottom: 15px; color: #2c3e50; }
        .filter-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .filter-item label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-size: 14px;
            font-weight: 500;
        }
        .filter-item input, .filter-item select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .table-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #3498db;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
            font-size: 14px;
        }
        tr:hover { background: #f8f9fa; }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .score { 
            font-weight: 600;
            color: #3498db;
        }
        .file-upload {
            margin-bottom: 20px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .file-upload input {
            margin-right: 10px;
        }
        .btn {
            background: #3498db;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover { background: #2980b9; }
        .error { color: #e74c3c; padding: 20px; background: #fadbd8; border-radius: 5px; margin-bottom: 20px; }
        .link-cell a { color: #3498db; text-decoration: none; }
        .link-cell a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💼 Job Application Dashboard</h1>
        <p class="subtitle">Track and manage your job applications</p>
        
        <div id="error" class="error" style="display:none;"></div>
        
        <div id="dashboard" style="display:none;">
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value" id="totalApps">0</div>
                    <div class="metric-label">Total Applications</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="seekApps">0</div>
                    <div class="metric-label">Via Seek</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="emailApps">0</div>
                    <div class="metric-label">Via Email</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="avgScore">-</div>
                    <div class="metric-label">Avg Similarity</div>
                </div>
            </div>
            
            <div class="filters">
                <h3>🔍 Filters</h3>
                <div class="filter-group">
                    <div class="filter-item">
                        <label>Search Position</label>
                        <input type="text" id="searchInput" placeholder="Search..." onkeyup="filterTable()">
                    </div>
                    <div class="filter-item">
                        <label>Application Method</label>
                        <select id="methodFilter" onchange="filterTable()">
                            <option value="all">All Methods</option>
                            <option value="seek">Seek Only</option>
                            <option value="email">Email Only</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="table-container">
                <table id="jobsTable">
                    <thead>
                        <tr>
                            <th>Job ID</th>
                            <th>Position</th>
                            <th>Applied On</th>
                            <th>Via Seek</th>
                            <th>Via Email</th>
                            <th>Similarity</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let jobsData = [];
        
        // Load from server file
        function loadFromServer() {
            fetch('/api/load-data')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showError(data.error);
                    } else {
                        processData(data);
                    }
                })
                .catch(err => {
                    showError('Error loading data: ' + err.message);
                });
        }
        
        // Auto-load on page load
        window.onload = function() {
            loadFromServer();
        };
        
        function processData(data) {
            if (!data.jobs) {
                showError('No jobs data found in file');
                return;
            }
            
            jobsData = Object.entries(data.jobs).map(([id, job]) => ({
                id,
                position: job.position || 'N/A',
                appliedOn: new Date(job.applied_on),
                viaSeek: job.applied_via_seek,
                viaEmail: job.applied_via_email,
                similarity: job.similarity_score,
                link: job.link || ''
            }));
            
            jobsData.sort((a, b) => b.appliedOn - a.appliedOn);
            
            document.getElementById('error').style.display = 'none';
            document.getElementById('dashboard').style.display = 'block';
            
            updateMetrics();
            renderTable();
        }
        
        function updateMetrics() {
            const total = jobsData.length;
            const seek = jobsData.filter(j => j.viaSeek).length;
            const email = jobsData.filter(j => j.viaEmail).length;
            const scores = jobsData.filter(j => j.similarity !== undefined).map(j => j.similarity);
            const avgScore = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2) : 'N/A';
            
            document.getElementById('totalApps').textContent = total;
            document.getElementById('seekApps').textContent = seek;
            document.getElementById('emailApps').textContent = email;
            document.getElementById('avgScore').textContent = avgScore;
        }
        
        function renderTable() {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            
            const filtered = getFilteredData();
            
            filtered.forEach(job => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${job.id}</td>
                    <td><strong>${job.position}</strong></td>
                    <td>${formatDate(job.appliedOn)}</td>
                    <td><span class="badge ${job.viaSeek ? 'badge-success' : 'badge-danger'}">${job.viaSeek ? '✓' : '✗'}</span></td>
                    <td><span class="badge ${job.viaEmail ? 'badge-success' : 'badge-danger'}">${job.viaEmail ? '✓' : '✗'}</span></td>
                    <td><span class="score">${job.similarity !== undefined ? job.similarity.toFixed(2) : 'N/A'}</span></td>
                    <td class="link-cell">${job.link ? `<a href="${job.link}" target="_blank">View</a>` : '-'}</td>
                `;
            });
        }
        
        function getFilteredData() {
            let filtered = [...jobsData];
            
            const search = document.getElementById('searchInput').value.toLowerCase();
            if (search) {
                filtered = filtered.filter(j => j.position.toLowerCase().includes(search));
            }
            
            const method = document.getElementById('methodFilter').value;
            if (method === 'seek') {
                filtered = filtered.filter(j => j.viaSeek);
            } else if (method === 'email') {
                filtered = filtered.filter(j => j.viaEmail);
            }
            
            return filtered;
        }
        
        function filterTable() {
            renderTable();
        }
        
        function formatDate(date) {
            return date.toLocaleString('en-AU', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            document.getElementById('dashboard').style.display = 'none';
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_TEMPLATE

@app.get("/api/load-data")
async def load_data():
    """Load data from the configured file path"""
    try:
        if not DATA_FILE.exists():
            raise HTTPException(status_code=404, detail=f'File not found: {DATA_FILE}')
        
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        
        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid JSON format')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Job Application Dashboard (FastAPI)")
    print("="*50)
    print(f"\n📂 Loading from: {DATA_FILE.absolute()}")
    
    if not DATA_FILE.exists():
        print(f"⚠️  Warning: File not found at {DATA_FILE}")
        print("   You can still upload a file via the web interface")
    
    print("\n🌐 Open your browser and go to:")
    print("   http://localhost:8000")
    print("\n💡 Usage:")
    print(f"   python {sys.argv[0]} [path/to/applied.json]")
    print("\n⏹️  Press CTRL+C to stop the server\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)