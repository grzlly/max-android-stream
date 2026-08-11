from flask import Flask, render_template_string, jsonify, request
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
    <title>Max Emulator</title>
    <style>
        body { margin: 0; padding: 0; background-color: #111; color: white; font-family: sans-serif; overflow: hidden; }
        iframe { width: 100vw; height: 100vh; border: none; display: none; }
        #loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
        .spinner { border: 4px solid #333; border-top: 4px solid #00ffcc; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
    <script>
        let iframeLoaded = false;
        setInterval(() => {
            fetch('/ping').then(r => r.json()).then(d => { if(!d.ok) window.location.reload(); }).catch(()=>{});
        }, 3000);
        let checkReady = setInterval(() => {
            if (iframeLoaded) { clearInterval(checkReady); return; }
            fetch('/status').then(r => r.json()).then(d => {
                if(d.ready) {
                    document.getElementById('loading').style.display = 'none';
                    let f = document.getElementById('emulator-frame');
                    f.style.display = 'block';
                    f.src = '/novnc/';
                    iframeLoaded = true;
                    clearInterval(checkReady);
                }
            }).catch(()=>{});
        }, 2000);
    </script>
</head>
<body>
    <div id="loading">
        <div class="spinner"></div>
        <h2>Запуск эмулятора...</h2>
        <p>Подождите 60-90 секунд.</p>
    </div>
    <iframe id="emulator-frame"></iframe>
</body>
</html>
"""

def setup_emulator():
    global is_ready
    with setup_lock:
        is_ready = False
        print("Waiting for Android to boot...")
        for _ in range(120):
            res = subprocess.run(["docker", "exec", "android-max", "adb", "shell", "getprop", "sys.boot_completed"],
                                 capture_output=True, text=True)
            if "1" in res.stdout:
                break
            time.sleep(5)
        res = subprocess.run(["docker", "exec", "android-max", "adb", "shell", "pm", "list", "packages", "com.vk.im"],
                             capture_output=True, text=True)
        if "com.vk.im" not in res.stdout:
            print("Installing APK...")
            subprocess.run(["docker", "exec", "android-max", "adb", "install", "-r", "/root/max.apk"], check=False)
        else:
            subprocess.run(["docker", "exec", "android-max", "adb", "shell", "pm", "clear", "com.vk.im"], check=False)
        subprocess.run(["docker", "exec", "android-max", "adb", "shell", "monkey",
                        "-p", "com.vk.im", "-c", "android.intent.category.LAUNCHER", "1"], check=False)
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
