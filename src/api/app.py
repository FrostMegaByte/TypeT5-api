import os
from pathlib import Path
from flask import Flask, request, jsonify, g
from api.typet5_main import TypeT5Model

app = Flask(__name__)
typet5 = TypeT5Model()

@app.before_request
def before_request():
    g.typet5 = typet5

@app.route('/')
async def home():
    return "Hello, Flask!"

@app.route('/api')
async def api():
    print("Running TypeT5 on data/code directory")
    try:
        json_response = await g.typet5.run_model()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return json_response

@app.route('/api/<path:project_directory>')
async def api_on_dir(project_directory):
    if not project_directory:
        return jsonify({'error': 'Missing project directory'}), 400

    project_directory = Path(project_directory)
    if not project_directory.is_dir():
        return jsonify({'error': 'Invalid project directory'}), 400
    
    print("Running TypeT5")
    try:
        json_response = await g.typet5.run_model_on_dir(project_directory)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return json_response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)