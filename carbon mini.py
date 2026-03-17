from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import sqlite3
from datetime import datetime

PORT = 8000

# Create database
conn = sqlite3.connect("carbon.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS emissions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
distance REAL,
mode TEXT,
fuel TEXT,
cc INTEGER,
emission REAL,
date TEXT
)
""")

conn.commit()


def get_records():
    conn = sqlite3.connect("carbon.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM emissions ORDER BY id DESC")
    rows = cursor.fetchall()

    table = ""

    for r in rows:
        table += f"""
        <tr>
        <td>{r[1]}</td>
        <td>{r[2]}</td>
        <td>{r[3]}</td>
        <td>{r[4]}</td>
        <td>{r[5]:.2f}</td>
        <td>{r[6]}</td>
        </tr>
        """

    return table


class CarbonHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        records = get_records()

        html = f"""
        <html>
        <head>
        <title>Carbon Emission Tracker</title>

        <style>

        * {{
        box-sizing:border-box;
        font-family:Arial;
        }}

        body {{
        margin:0;
        background:linear-gradient(135deg,#6dd5ed,#2193b0);
        text-align:center;
        }}

        h2 {{
        color:white;
        }}

        .container {{
        width:420px;
        margin:auto;
        margin-top:50px;
        padding:25px;
        border-radius:12px;
        background:white;
        box-shadow:0 10px 25px rgba(0,0,0,0.2);
        transition:0.3s;
        }}

        .container:hover {{
        transform:scale(1.03);
        }}

        input,select {{
        width:90%;
        padding:10px;
        margin:10px;
        border-radius:6px;
        border:1px solid #ccc;
        transition:0.3s;
        }}

        input:focus,select:focus {{
        border-color:#2193b0;
        box-shadow:0 0 8px rgba(33,147,176,0.5);
        outline:none;
        }}

        button {{
        padding:12px 25px;
        border:none;
        border-radius:6px;
        background:#2193b0;
        color:white;
        cursor:pointer;
        font-size:15px;
        transition:0.3s;
        }}

        button:hover {{
        background:#176b87;
        transform:translateY(-2px);
        }}

        table {{
        margin:auto;
        margin-top:40px;
        border-collapse:collapse;
        width:80%;
        background:white;
        box-shadow:0 10px 20px rgba(0,0,0,0.2);
        }}

        th {{
        background:#2193b0;
        color:white;
        padding:10px;
        }}

        td {{
        padding:8px;
        border-bottom:1px solid #ddd;
        }}

        tr:hover {{
        background:#f1f1f1;
        }}

        </style>

        </head>

        <body>

        <h2>Carbon Emission Calculator</h2>

        <div class="container">

        <form method="POST">

        <input type="number" name="distance" placeholder="Distance (km)" required>

        <br>

        <select name="mode">
        <option value="car">Car</option>
        <option value="bike">Bike</option>
        <option value="bus">Bus</option>
        </select>

        <br>

        <select name="fuel">
        <option value="petrol">Petrol</option>
        <option value="diesel">Diesel</option>
        <option value="electric">Electric</option>
        </select>

        <br>

        <input type="number" name="cc" placeholder="Engine CC" required>

        <br>

        <button type="submit">Calculate Emission</button>

        </form>

        </div>

        <h2>Emission History</h2>

        <table>

        <tr>
        <th>Distance</th>
        <th>Mode</th>
        <th>Fuel</th>
        <th>CC</th>
        <th>Emission (kg CO2)</th>
        <th>Date & Time</th>
        </tr>

        {records}

        </table>

        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()
        self.wfile.write(html.encode())


    def do_POST(self):

        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length).decode()
        form = parse_qs(data)

        distance = float(form["distance"][0])
        mode = form["mode"][0]
        fuel = form["fuel"][0]
        cc = int(form["cc"][0])

        fuel_factor = {
        "petrol":0.192,
        "diesel":0.171,
        "electric":0.05
        }

        mode_factor = {
        "car":1,
        "bike":0.6,
        "bus":0.4
        }

        emission = distance * fuel_factor[fuel] * mode_factor[mode] * (1 + cc/2000)

        # Suggestion logic
        if emission < 2:
            level = "Low Emission"
            suggestion = "Good job. Your carbon footprint is low. Continue using eco friendly transport."

        elif emission < 5:
            level = "Moderate Emission"
            suggestion = "Consider carpooling or public transport to reduce emissions."

        else:
            level = "High Emission"
            suggestion = "High carbon footprint detected. Try electric vehicles, buses, trains or cycling."

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("carbon.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO emissions(distance,mode,fuel,cc,emission,date)
        VALUES(?,?,?,?,?,?)
        """,(distance,mode,fuel,cc,emission,now))

        conn.commit()

        result = f"""
        <html>
        <head>
        <style>

        body {{
        font-family:Arial;
        background:linear-gradient(135deg,#6dd5ed,#2193b0);
        text-align:center;
        }}

        .box {{
        background:white;
        width:420px;
        margin:auto;
        margin-top:120px;
        padding:30px;
        border-radius:10px;
        box-shadow:0 10px 25px rgba(0,0,0,0.2);
        }}

        button {{
        padding:10px 20px;
        background:#2193b0;
        color:white;
        border:none;
        border-radius:6px;
        cursor:pointer;
        }}

        </style>
        </head>

        <body>

        <div class="box">

        <h2>Emission Result</h2>

        <p><b>Estimated CO2 Emission:</b> {emission:.2f} kg</p>

        <p><b>Impact Level:</b> {level}</p>

        <p><b>Suggestion:</b></p>
        <p>{suggestion}</p>

        <br>

        <a href="/"><button>Back to Calculator</button></a>

        </div>

        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()
        self.wfile.write(result.encode())


server = HTTPServer(("localhost",PORT),CarbonHandler)

print("Server running at http://localhost:8000")

server.serve_forever()