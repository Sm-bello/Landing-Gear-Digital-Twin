import psycopg2
import time
import random
import csv
import os
import socket
import smtplib
import math
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
#   ✈️  AEROTWIN MASTER CONTROLLER - V5.1 (BUTTER SMOOTH EDITION)
# ==============================================================================

# --- DATABASE CONFIG ---
DB_NAME = "project_db"
DB_USER = "postgres"
DB_PASS = "A#1Salamatu"
DB_HOST = "localhost"
TELEGRAF_HOST = "127.0.0.1"
TELEGRAF_PORT = 8094 

# --- FLIGHTGEAR CONFIG ---
FG_HOST = "127.0.0.1"
FG_PORT = 5502

# --- EMAIL CONFIG ---
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_RECEIVER = "bellosani2drescue@gmail.com"

# --- NETWORK SOCKETS (Non-Blocking) ---
udp_fg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_telegraf = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- FILE SETUP ---
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
csv_filename = os.path.join(desktop_path, "Dornier_228_HighFidelity_Dataset.csv")

# --- GLOBAL STATE ---
state = { 
    "lat": 5.2614, "lon": -3.9263, "alt": 21, "heading": 90, "roll": 0.0, "pitch": 0.0,
    "gear_position": 1.0, "gear_cycles": 0, "main_health": 100.0, "nose_health": 100.0,
    "hyd_pressure": 3000, "brake_temp": 150, "strut_pressure": 1800, "oil_temp": 45.0,
    "vibration": 0.1, "g_force": 1.0, "side_load": 0.0, "seal_integrity": 1.0,
    "runway_condition": "DRY", "flight_id": "INIT", "phase": "INIT"
}

AIRPORTS = {"LOS": {"lat": 6.5774, "lon": 3.3212, "alt": 135}, "ABJ": {"lat": 5.2614, "lon": -3.9263, "alt": 21}}

# ==============================================================================
#   ⚡ HIGH-SPEED TELEMETRY
# ==============================================================================

def send_telemetry():
    """Sends visuals (FG) and data (Telegraf) instantly."""
    # 1. FlightGear (Visuals First)
    msg = f"{state['lat']},{state['lon']},{state['alt']},{state['roll']},{state['pitch']},{state['heading']},{state['gear_position']},{state['gear_position']},{state['gear_position']}\n"
    try:
        udp_fg.sendto(msg.encode(), (FG_HOST, FG_PORT))
    except: pass

    # 2. InfluxDB via Telegraf
    timestamp = int(time.time() * 1000000000)
    line = f"flight_telemetry,flight_id={state['flight_id']},phase={state['phase']} " \
           f"altitude={state['alt']},speed={state['speed']},g_force={state['g_force']}," \
           f"gear_pos={state['gear_position']},hyd_pressure={state['hyd_pressure']}," \
           f"brake_temp={state['brake_temp']},vibration={state['vibration']}," \
           f"main_health={state['main_health']} {timestamp}"
    try:
        udp_telegraf.sendto(line.encode(), (TELEGRAF_HOST, TELEGRAF_PORT))
    except: pass

def update_db_event(cursor, phase):
    """Sends COMMAND signal to Postgres. (Only once per phase change)"""
    try:
        sql = """
            INSERT INTO flight_operations 
            (aircraft_id, flight_number, phase, arrival_time, 
             main_strut_health, latitude, longitude, roll, pitch, gear_position) 
            VALUES (1, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (state['flight_id'], phase, state['main_health'], 
                             state['lat'], state['lon'], state['roll'], state['pitch'], state['gear_position']))
    except: pass

def update_physics(phase, speed_target, dt):
    state['phase'] = phase
    state['speed'] = speed_target
    
    # Hydraulics
    target_hyd = 3000 if state['seal_integrity'] > 0.8 else 2500
    if phase in ["Takeoff", "Approach"]: target_hyd -= 200
    state['hyd_pressure'] += (target_hyd - state['hyd_pressure']) * 0.2
    
    # Temps
    if "Taxi" in phase or "Landing" in phase:
        state['brake_temp'] += (speed_target * 0.5) * dt
    else:
        state['brake_temp'] -= 2.0 * dt
    
    # Vibration (Random Noise)
    base_vib = 0.05 + ((100 - state['main_health']) * 0.01)
    state['vibration'] = base_vib + random.uniform(-0.05, 0.05)

def inject_faults(phase):
    if phase == "Landing":
        risk = state['gear_cycles'] / 100.0
        if random.random() < (0.1 + risk * 0.2):
            impact = 1.3 + random.uniform(0.5, 2.0)
            state['g_force'] = impact
            state['main_health'] -= impact * 0.5
            print(f"   ⚠️  HARD LANDING: {impact:.2f}G")
            if impact > 2.5: send_email_alert("HARD LANDING", f"G-Force: {impact}")
        else:
            state['g_force'] = 1.1 

def send_email_alert(subj, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"🚨 {subj}"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except: pass

# ==============================================================================
#   🔄 FLIGHT LOOP
# ==============================================================================

def fly_segment(cursor, flight_id, phase, start_pos, end_pos, duration, speed, gear_target, csv_writer, csv_file):
    # ⚡ OPTIMIZATION: 60 FPS (16ms per frame)
    fps = 60
    steps = int(duration * fps)
    
    lat_step = (end_pos['lat'] - start_pos['lat']) / steps
    lon_step = (end_pos['lon'] - start_pos['lon']) / steps
    alt_step = (end_pos['alt'] - start_pos['alt']) / steps
    gear_step = (gear_target - state['gear_position']) / steps
    state['heading'] = math.degrees(math.atan2(end_pos['lon']-start_pos['lon'], end_pos['lat']-start_pos['lat'])) % 360
    
    # 1. NOTIFY MATLAB (Once per phase)
    update_db_event(cursor, phase)
    print(f"   ✈️ {phase} STARTED")

    for i in range(steps):
        # Physics Update
        state['lat'] += lat_step
        state['lon'] += lon_step
        state['alt'] += alt_step
        state['gear_position'] += gear_step
        state['flight_id'] = flight_id
        
        # Pitch Logic
        if alt_step > 0.5: state['pitch'] = 7.0
        elif alt_step < -0.5: state['pitch'] = -5.0
        else: state['pitch'] = 0.0
        
        # Math & Network
        update_physics(phase, speed, 1.0/fps)
        send_telemetry() # UDP is fast, safe to do every frame
        
        # ⚡ OPTIMIZATION: Write to CSV less often (Every 60 frames = 1 sec)
        # This prevents the "Hard Drive Stutter"
        if i % 60 == 0:
            row = [datetime.now(), flight_id, phase, state['alt'], speed, state['lat'], state['lon'],
                   state['roll'], state['pitch'], state['heading'], state['gear_position'], state['g_force'],
                   state['hyd_pressure'], "NORMAL", state['brake_temp'], state['strut_pressure'], 
                   state['oil_temp'], state['vibration'], state['side_load'], state['gear_cycles'], 
                   state['seal_integrity'], state['runway_condition']]
            csv_writer.writerow(row)
            # NO flush() here! Let the OS handle it.
        
        time.sleep(1.0/fps) 

def run_simulation():
    print(f"📂 Data: {csv_filename}")
    f = open(csv_filename, "w", newline='')
    writer = csv.writer(f)
    writer.writerow(["Time", "ID", "Phase", "Alt", "Speed", "Lat", "Lon", "Roll", "Pitch", "Hdg", "Gear", "G", "Hyd", "Stat", "Brk", "Strut", "Oil", "Vib", "Side", "Cyc", "Seal", "Rwy"])

    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        conn.autocommit = True
        cursor = conn.cursor()
    except: cursor = None

    print("\n⚡ STARTING 75-FLIGHT CYCLE (60 FPS SMOOTH MODE)...")
    
    for i in range(1, 76):
        flight_id = f"NG-{i:03d}"
        origin = "ABJ" if i % 2 != 0 else "LOS"
        dest = "LOS" if i % 2 != 0 else "ABJ"
        print(f"\n--- 🛫 Flight {flight_id} ({i}/75) ---")
        
        p1 = {'lat': AIRPORTS[origin]['lat'], 'lon': AIRPORTS[origin]['lon'], 'alt': AIRPORTS[origin]['alt']}
        p2 = {'lat': p1['lat']+0.01, 'lon': p1['lon']+0.01, 'alt': p1['alt']}
        fly_segment(cursor, flight_id, "Taxi", p1, p2, 3, 20, 1.0, writer, f)
        
        p3 = {'lat': p1['lat']+0.05, 'lon': p1['lon']+0.05, 'alt': 1500}
        fly_segment(cursor, flight_id, "Takeoff", p2, p3, 8, 140, 0.0, writer, f)
        
        p4 = {'lat': p3['lat']+0.05, 'lon': p3['lon']+0.05, 'alt': 5000}
        fly_segment(cursor, flight_id, "Climb", p3, p4, 4, 180, 0.0, writer, f)

        p5 = {'lat': AIRPORTS[dest]['lat']-0.1, 'lon': AIRPORTS[dest]['lon']-0.1, 'alt': 5000}
        fly_segment(cursor, flight_id, "Cruise", p4, p5, 4, 220, 0.0, writer, f)
        
        p6 = {'lat': AIRPORTS[dest]['lat']-0.05, 'lon': AIRPORTS[dest]['lon']-0.05, 'alt': 2000}
        fly_segment(cursor, flight_id, "Descent", p5, p6, 4, 180, 0.0, writer, f)
        
        p7 = {'lat': AIRPORTS[dest]['lat'], 'lon': AIRPORTS[dest]['lon'], 'alt': AIRPORTS[dest]['alt']}
        fly_segment(cursor, flight_id, "Approach", p6, p7, 8, 160, 1.0, writer, f)
        
        state['gear_cycles'] += 1
        inject_faults("Landing")
        p8 = {'lat': p7['lat']+0.01, 'lon': p7['lon']+0.01, 'alt': p7['alt']}
        fly_segment(cursor, flight_id, "Landing", p7, p8, 5, 80, 1.0, writer, f)
        
        # Flush the file only at the END of a flight to be safe
        f.flush()

    f.close()
    if conn: conn.close()

if __name__ == "__main__":
    run_simulation()