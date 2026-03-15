from flask import Flask, request, jsonify, send_from_directory
import subprocess
import sys
import os

app = Flask(__name__, static_folder='.')

@app.route('/run-search')
def run_search():
    address = request.args.get('address', '')
    radius = request.args.get('radius', '')
    if not address or not radius:
        print(result.stderr)
        return jsonify({'error': 'Missing address or radius'}), 400

    # Call search.py with address and radius as arguments
    # Assumes search.py is updated to accept command-line arguments
    try:
        result = subprocess.run([
            sys.executable, 'search.py', address, radius
        ], capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(result.stderr)
            return jsonify({'status': 'success'})
        else:
            print(result.stderr)
            return jsonify({'status': 'error', 'output': result.stderr}), 500
    except Exception as e:
        print(result.stderr)
        return jsonify({'status': 'error', 'output': str(e)}), 500


# Serve static files (index.html, school-list.html, schools.json, etc.)
@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
