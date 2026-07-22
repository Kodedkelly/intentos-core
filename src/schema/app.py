import os
import sys
import sqlite3
from flask import Flask, jsonify, render_template_string
from config import IntentOSConfig

# Enforce strict absolute structural path resolution tracking
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

app = Flask(__name__)
db_path = os.path.join(IntentOSConfig.DATA_MOAT_DIR, "intentos_data_moat.db")

# High-utility HTML dashboard design layout served straight out of the platform core
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>IntentOS — Core Database Analytics</title>
    <script src="https://tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans p-8">
    <div class="max-w-5xl mx-auto space-y-6">
        <header class="border-b border-slate-800 pb-4">
            <h1 class="text-xl font-black text-white tracking-tight">IntentOS Local Analytics</h1>
            <p class="text-xs text-slate-400 font-medium">Relational Storage Moat Monitoring Console (Port 5001)</p>
        </header>

        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <h2 class="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">Latest Logged Interactions</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left font-mono text-xs text-slate-300">
                    <thead>
                        <tr class="border-b border-slate-800 text-slate-500 font-bold">
                            <th class="pb-2">Timestamp (us)</th>
                            <th class="pb-2">Hardware Source ID</th>
                            <th class="pb-2">Decoded Intent</th>
                            <th class="pb-2">Confidence</th>
                            <th class="pb-2">Lead Buffer</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/50">
                        {% for row in rows %}
                        <tr class="hover:bg-slate-800/20">
                            <td class="py-2.5 text-slate-400">{{ row[1] }}</td>
                            <td class="py-2.5 font-bold text-slate-200">{{ row[2] }}</td>
                            <td class="py-2.5 text-emerald-400 font-extrabold">{{ row[4] }}</td>
                            <td class="py-2.5 font-semibold text-white">{{ (row[5]*100)|round(2) }}%</td>
                            <td class="py-2.5 text-indigo-400 font-bold">-{{ row[6]/1000 }}ms</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def view_dashboard():
    """Queries historical telemetry records from the database matrix and renders the HTML dashboard."""
    if not os.path.exists(db_path):
        return render_template_string(DASHBOARD_TEMPLATE, rows=[])
        
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # Extract the latest 15 logged telemetry frames sequentially
        cursor.execute("SELECT * FROM hmi_telemetry_logs ORDER BY id DESC LIMIT 15")
        rows = cursor.fetchall()
        
    return render_template_string(DASHBOARD_TEMPLATE, rows=rows)

if __name__ == "__main__":
    print("[IntentOS WebUX] Operational. Booting Flask local monitoring gateway...")
    app.run(host="127.0.0.1", port=5001, debug=False)
