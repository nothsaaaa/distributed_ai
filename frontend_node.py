# frontend_node.py
from flask import Flask, render_template, request
import requests
import logging

app = Flask(__name__)

CENTER_NODE = "http://localhost:5001"
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Advanced Math Tool</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            form { margin-bottom: 20px; }
            input[type="text"] { width: 300px; padding: 10px; margin-right: 10px; }
            button { padding: 10px 15px; background-color: #007BFF; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .result { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Advanced Math Tool</h1>
        <form method="POST" action="/solve">
            <input type="text" name="question" placeholder="Enter your math question" required>
            <button type="submit">Solve</button>
        </form>
    </body>
    </html>
    '''

@app.route('/solve', methods=['POST'])
def solve():
    question = request.form.get('question')
    print("[Frontend] Sending question to center node")
    try:
        response = requests.post(CENTER_NODE + '/process', json={"question": question})
        result = response.json()
        print("[Frontend] Response received from center node")

        # Extract the answer from the Ollama API response
        answer = result.get('message', {}).get('content', 'Error: No response from backend')

        # Replace newlines with <br> tags for proper rendering
        formatted_answer = answer.replace('\n', '<br>')

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Advanced Math Tool - Result</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .result {{ margin-top: 20px; }}
                a {{ text-decoration: none; color: #007BFF; }}
                a:hover {{ color: #0056b3; }}
            </style>
        </head>
        <body>
            <h1>Result</h1>
            <div class="result">
                <p><strong>Question:</strong> {question}</p>
                <p><strong>Answer:</strong></p>
                <p>{formatted_answer}</p>
            </div>
            <a href="/">Back</a>
        </body>
        </html>
        '''
    except Exception as e:
        print(f"[Frontend] !! ERROR: {e} !!")
        return f"Error: {str(e)}"


@app.route('/health')
def health():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Health</title>
        <script>
            async function fetchHealth() {
                try {
                    const response = await fetch('/api/health');
                    const data = await response.json();
                    const healthContainer = document.getElementById('health-stats');
                    healthContainer.innerHTML = JSON.stringify(data, null, 2);
                } catch (error) {
                    console.error("Failed to fetch health stats:", error);
                }
            }

            function startAutoRefresh() {
                fetchHealth();
                setInterval(fetchHealth, 100); // Refresh every 5 seconds
            }

            window.onload = startAutoRefresh;
        </script>
    </head>
    <body>
        <h1>System Health</h1>
        <pre id="health-stats">Loading...</pre>
        <a href="/">Back to Main</a>
    </body>
    </html>
    '''

@app.route('/api/health')
def api_health():
    try:
        response = requests.get(CENTER_NODE + '/globalhealth')
        return response.json()
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)  # Frontend runs on port 5000
