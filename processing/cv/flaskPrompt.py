from flask import Flask
from flask import request
from flask import jsonify
import subprocess
import os

app = Flask(__name__)

# In-memory storage for simplicity
data_store = {}

@app.route('/data', methods=['POST'])
def store_data():
    # Store the incoming JSON data
    data = request.json
    data_store['latest'] = data
    return jsonify({"message": "Data stored successfully."})

@app.route('/data', methods=['GET'])
def get_data():
    # Retrieve the stored data
    data = data_store.get('latest', {})
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)