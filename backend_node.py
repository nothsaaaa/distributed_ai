# backend_node.py
from flask import Flask, request, jsonify
import requests
import threading
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

CENTER_NODE_URL = "http://localhost:5001"  # Update with the actual center node address
BACKEND_ID = "backend_1"  # Assign a unique ID to this backend
load = 0
lock = threading.Lock()  # Thread-safe lock for updating load


def report_load():
    """Report the current load to the center node."""
    global load
    try:
        response = requests.post(
            f"{CENTER_NODE_URL}/update_load",
            json={"backend_id": BACKEND_ID, "load": load},
            timeout=2
        )
        if response.status_code == 200:
            print(f"[Backend] Successfully reported load {load} to center node.")
        else:
            print(f"[Backend] Failed to report load to center node. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"[Backend] Error reporting load to center node: {e}")


def increase_load():
    """Increase the load and report it to the center node."""
    global load
    with lock:
        load += 1
        print(f"[Backend] Load increased to {load}.")
        report_load()


def decrease_load():
    """Decrease the load and report it to the center node."""
    global load
    with lock:
        load -= 1
        print(f"[Backend] Load decreased to {load}.")
        report_load()


@app.route('/process', methods=['POST'])
def process():
    """Process the incoming question."""
    print("[Backend] Received request to process question.")
    data = request.json
    question = data.get('question', '')

    increase_load()  # Increment load before processing
    try:
        print("[Backend] Sending question to Ollama API...")
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2",
                "messages": [{"role": "user", "content": question}],
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            print("[Backend] Ollama API response received.")
            return jsonify(response.json())
        else:
            print(f"[Backend] Ollama API returned error: {response.status_code}")
            return jsonify({"error": "Ollama API error"}), response.status_code
    except requests.RequestException as e:
        print(f"[Backend] !! ERROR OCCURRED: {e} !!")
        return jsonify({"error": "Request to Ollama API failed"}), 500
    finally:
        decrease_load()  # Decrement load after processing


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    global load
    return jsonify({"status": "OK", "load": load}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002)  # Backend runs on port 5002
