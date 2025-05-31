import requests
import time
from flask import Flask, request, jsonify
import logging
import random

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

BACKENDS = [
    {"id": "backend_1", "url": "http://localhost:5002", "last_checked": 0, "is_down": False, "load": 0, "last_response_code": None},
    {"id": "backend_2", "url": "http://192.168.0.166:5002", "last_checked": 0, "is_down": False, "load": 0, "last_response_code": None},
]

CHECK_INTERVAL = 300  # 5 minutes in seconds


def update_backend_health():
    """Update the health status and load of all backends."""
    for backend in BACKENDS:
        # Skip if the backend is marked down and not due for a recheck
        if backend["is_down"] and (time.time() - backend["last_checked"] <= CHECK_INTERVAL):
            continue

        try:
            print(f"[Center Node] Checking health of {backend['id']}...")
            response = requests.get(backend["url"] + '/health', timeout=2)
            backend["last_response_code"] = response.status_code
            if response.status_code == 200:
                health_data = response.json()
                backend["load"] = health_data.get('load', 0)
                backend["is_down"] = False
                print(f"[Center Node] {backend['id']} is healthy with load {backend['load']}.")
            else:
                backend["is_down"] = True
                backend["last_checked"] = time.time()
                backend["load"] = 0
                print(f"[Center Node] {backend['id']} returned error code {response.status_code}. Marked as down.")
        except requests.RequestException:
            backend["is_down"] = True
            backend["last_checked"] = time.time()
            backend["last_response_code"] = None
            backend["load"] = 0
            print(f"[Center Node] {backend['id']} is unreachable. Marked as down.")


def find_least_loaded_backend():
    update_backend_health()

    shuffled_backends = BACKENDS[:]
    random.shuffle(shuffled_backends)
    print(f"[Center Node] Shuffled backend list: {[b['id'] for b in shuffled_backends]}")

    available_backends = [backend for backend in shuffled_backends if not backend["is_down"]]

    if not available_backends:
        print("[Center Node] No available backends.")
        return None

    least_loaded_backend = min(available_backends, key=lambda b: b["load"])
    print(f"[Center Node] Selected backend: {least_loaded_backend['id']} with load {least_loaded_backend['load']}.")
    return least_loaded_backend



@app.route('/process', methods=['POST'])
def process():
    print("[Center Node] Request received from frontend.")
    data = request.json
    question = data.get('question', '')
    print("[Center Node] Finding least loaded backend...")
    backend = find_least_loaded_backend()
    if not backend:
        print("[Center Node] !! No available backends !!")
        return jsonify({"error": "No available backends"}), 503

    try:
        print(f"[Center Node] Forwarding request to {backend['id']}.")
        response = requests.post(backend["url"] + '/process', json={"question": question})
        backend["last_response_code"] = response.status_code
        if response.status_code == 200:
            print("[Center Node] Backend response received. Returning to frontend.")
            return jsonify(response.json())
        else:
            print("[Center Node] Backend returned an error.")
            return jsonify({"error": "Backend error"}), response.status_code
    except requests.RequestException:
        backend["is_down"] = True
        backend["last_checked"] = time.time()
        backend["last_response_code"] = None
        backend["load"] = 0
        print(f"[Center Node] !! Backend {backend['id']} failed during processing !! Marking as down.")
        return jsonify({"error": "Backend failed"}), 500


@app.route('/globalhealth', methods=['GET'])
def global_health():
    """Returns the status of each backend server."""
    return jsonify([
        {
            "id": backend["id"],
            "url": backend["url"],
            "is_down": backend["is_down"],
            "last_checked": backend["last_checked"],
            "load": backend["load"],
            "last_response_code": backend["last_response_code"]
        }
        for backend in BACKENDS
    ]), 200


@app.route('/health', methods=['GET'])
def health():
    return "OK", 200


@app.route('/update_load', methods=['POST'])
def update_load():
    data = request.json
    backend_id = data.get('backend_id')
    load = data.get('load')

    if not backend_id or load is None:
        print("[Center Node] Invalid update_load request: Missing backend_id or load.")
        return jsonify({"error": "Missing backend_id or load"}), 400

    for backend in BACKENDS:
        if backend.get("id") == backend_id:
            backend["load"] = load
            print(f"[Center Node] Updated load for {backend_id} to {load}.")
            return jsonify({"message": "Load updated"}), 200

    print(f"[Center Node] Received load update from unknown backend: {backend_id}.")
    return jsonify({"error": "Unknown backend"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # Center runs on port 5001
