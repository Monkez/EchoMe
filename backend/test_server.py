"""
Simple Test Server - Check if it works
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Backend is running!'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'TalkToMe Backend Ready'})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Backend Server Starting...")
    print("="*50)
    print("📍 URL: http://localhost:5000")
    print("🏥 Health: http://localhost:5000/api/health")
    print("="*50 + "\n")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
