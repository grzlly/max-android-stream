from flask import Flask, render_template_string, jsonify
import time
import subprocess
import threading

app = Flask(__name__)

is_ready = False
last_ping = 0
setup_lock = threading.Lock()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Max</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0a; color: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; height: 100vh; overflow: hidden; }
        #vnc-frame { width: 100%; height: 100vh; border: none; display: none; background: #000; }
        #loading {
            position: fixed; inset: 0;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            gap: 20px; background: #0a0a0a;
        }
        .logo { font-size: 2.5rem; font-weight: 800; letter-spacing: -1px; color: #fff; }
        .logo span { color: #e50914; }
        .spinner {
            width: 44px; height: 44px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #e50914;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .status { font-size: 0.9rem; color: rgba(255,255,255,0.4); }
    </style>
    <script>
        let iframeLoaded = false;

        // Keep-alive ping
        setInterval(() => {
            fetch('/ping').then(r => r.json()).then(d => {
                if (!d.ok) window.location.reload();
            }).catch(() => {});
        }, 3000);

        // Poll until emulator ready
        const checkReady = setInterval(() => {
            if (iframeLoaded) { clearInterval(checkReady); return; }
            fetch('/status').then(r => r.json()).then(d => {
                if (d.ready) {
                    document.getElementById('loading').style.display = 'none';
                    const f = document.getElementById('vnc-frame');
                    // Open raw noVNC client — no docker-android branding
                    f.src = '/novnc/vnc.html?autoconnect=true&resize=scale&show_dot=true';
                    f.style.display = 'block';
                    iframeLoaded = true;
                    clearInterval(checkReady);
                }
            }).catch(() => {});
        }, 2000);
    </script>
</head>
<body>
    <div id="loading">
        <div class="logo">M<span>A</span>X</div>
        <div class="spinner"></div>
        <p class="status">Запуск... подождите 60-90 секунд</p>
    </div>
    <iframe id="vnc-frame" allowfullscreen></iframe>
</body>
</html>
"""

def setup_emulator():
    global is_ready
    with setup_lock:
        is_ready = False
        print("Waiting for Android boot...")
        for _ in range(120):
            res = subprocess.run(
                ["docker", "exec", "android-max", "adb", "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True
            )
            if "1" in res.stdout:
                print("Android booted!")
                break
            time.sleep(5)

        # Check if Max is installed
        res = subprocess.run(
            ["docker", "exec", "android-max", "adb", "shell", "pm", "list", "packages", "com.vk.im"],
            capture_output=True, text=True
        )
        if "com.vk.im" not in res.stdout:
            print("Installing Max APK...")
            subprocess.run(
                ["docker", "exec", "android-max", "adb", "install", "-r", "/root/max.apk"],
                check=False, timeout=120
            )
        else:
            print("App installed, clearing data...")
            subprocess.run(
                ["docker", "exec", "android-max", "adb", "shell", "pm", "clear", "com.vk.im"],
                check=False
            )

        # Launch Max
        subprocess.run(
            ["docker", "exec", "android-max", "adb", "shell", "monkey",
             "-p", "com.vk.im", "-c", "android.intent.category.LAUNCHER", "1"],
            check=False
        )
        time.sleep(3)
        is_ready = True
        print("Ready!")

@app.route('/')
def index():
    global last_ping
    last_ping = time.time()
    threading.Thread(target=setup_emulator, daemon=True).start()
    return render_template_string(HTML_TEMPLATE)

@app.route('/ping')
def ping():
    global last_ping
    last_ping = time.time()
    return jsonify({"ok": True})

@app.route('/status')
def status():
    return jsonify({"ready": is_ready})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
