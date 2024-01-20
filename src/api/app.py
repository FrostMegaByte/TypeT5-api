import os
from pathlib import Path
import time
from flask import Flask, jsonify, g
from api.typet5_main import TypeT5Model

app = Flask(__name__)
typet5 = TypeT5Model()

@app.before_request
def before_request():
    g.typet5 = typet5

@app.route('/')
async def home():
    return "Welcome to the TypeT5 API! Visit /api to run TypeT5 on your provided project directory"

@app.route('/api')
async def api():
    print("Running TypeT5 on /data/code directory")
    try:
        start_time = time.time()
        response = await g.typet5.run_model()
        finish_time = time.time() - start_time
        response["time_taken"] = f"{finish_time:.2f} seconds"
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)