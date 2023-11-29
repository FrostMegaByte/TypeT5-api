from flask import Flask, g
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
    json_response = await g.typet5.run_model()
    return json_response

if __name__ == '__main__':
    app.run(debug=True)