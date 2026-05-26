# (Este código es una versión mejorada que acepta sincronización)
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "prestamos.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/sincronizar-prestamo', methods=['POST'])
def sincronizar():
    data = request.json
    # Aquí el servidor recibirá el préstamo de tu PC y lo guardará
    return jsonify({"mensaje": "Recibido correctamente"}), 200

# ... (el resto del código que ya tenías para el celular)
