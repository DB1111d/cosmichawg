import http.server
import socketserver
import threading
import webbrowser
import os
import time
import sys

# ─── CONFIGURATION ───────────────────────────────────────────────
PORT = 8000
PROJECT_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "cosmichawg")
CHROMEDRIVER_PATH = os.path.join(os.path.expanduser("~"), ".wdm", "drivers", "chromedriver", "chromedriver")
CHROME_BINARY = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# ─────────────────────────────────────────────────────────────────

def start_server(folder, port):
    os.chdir(folder)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"✅ Server started at http://localhost:{port}")
        print(f"📁 Serving folder: {folder}")
        print(f"\nPress Ctrl+C to stop the server.\n")
        httpd.serve_forever()

def open_with_selenium(port):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        time.sleep(1.5)

        options = Options()
        options.binary_location = CHROME_BINARY

        service = Service(executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(f"http://localhost:{port}/index.html")
        print(f"🌐 Opened Chrome at http://localhost:{port}/index.html")

    except Exception as e:
        print(f"⚠️  Error: {e}")
        webbrowser.open(f"http://localhost:{port}/index.html")

if __name__ == "__main__":
    if not os.path.exists(PROJECT_FOLDER):
        print(f"❌ Folder not found: {PROJECT_FOLDER}")
        sys.exit(1)

    print(f"\n🚀 Starting local server...")

    server_thread = threading.Thread(target=start_server, args=(PROJECT_FOLDER, PORT), daemon=True)
    server_thread.start()

    open_with_selenium(PORT)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
