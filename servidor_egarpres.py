import os
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "prestamos.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- DISEÑO PARA EL CELULAR (HTML) ---
HTML_MAIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Egarpres Móvil</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f7f6; font-family: sans-serif; }
        .card { border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-top: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 15px 15px 0 0; text-align: center; }
        .btn-success { background-color: #27ae60; border: none; font-weight: bold; }
        .wa-btn { background-color: #25d366; color: white; font-weight: bold; text-decoration: none; display: block; text-align: center; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container" style="max-width: 500px;">
        <div class="card">
            <div class="header">
                <h3>EGARPRES MÓVIL</h3>
                <small>Gestión de Cobros</small>
            </div>
            <div class="card-body">
                <input type="text" id="busqueda" class="form-control mb-3" placeholder="Nombre o Cédula..." onkeyup="buscar()">
                <div id="resultados" class="list-group"></div>
                
                <div id="pago-form" style="display:none;" class="mt-4">
                    <h5 id="n-cliente"></h5>
                    <div id="lista-prestamos"></div>
                    <hr>
                    <label>Monto a cobrar:</label>
                    <input type="number" id="monto" class="form-control mb-2" placeholder="0.00">
                    <button class="btn btn-success w-100 mb-3" id="btn-pago" onclick="confirmar()">✅ REGISTRAR PAGO</button>
                    <div id="feedback"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let cSel = null; let pSel = null;
        async function buscar() {
            let q = document.getElementById('busqueda').value;
            if(q.length < 3) return;
            let res = await fetch(`/api/clientes?q=${q}`);
            let data = await res.json();
            let h = '';
            data.forEach(c => {
                h += `<button class="list-group-item list-group-item-action" onclick='selCliente(\({JSON.stringify(c)})'>\){c.nombre}</button>`;
            });
            document.getElementById('resultados').innerHTML = h;
        }
        async function selCliente(c) {
            cSel = c;
            document.getElementById('n-cliente').innerText = 'Cliente: ' + c.nombre;
            document.getElementById('pago-form').style.display = 'block';
            document.getElementById('resultados').innerHTML = '';
            let res = await fetch(`/api/prestamos/${c.id}`);
            let prestamos = await res.json();
            let ph = '<h6>Seleccione el Préstamo:</h6>';
            prestamos.forEach(p => {
                ph += `<div class="alert alert-info" onclick='pSel=\({JSON.stringify(p)}; alert("Préstamo seleccionado")'>ID: \){p.id} - Saldo: \[{p.monto_prestado.toLocaleString()}</div>`;
                pSel = p;
            });
            document.getElementById('lista-prestamos').innerHTML = ph;
        }
        async function confirmar() {
            let m = document.getElementById('monto').value;
            if(!m || !pSel) return alert('Por favor seleccione un préstamo e ingrese el monto');
            document.getElementById('btn-pago').disabled = true;
            try {
                let res = await fetch('/api/pago', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({p_id: pSel.id, monto: m})
                });
                let d = await res.json();
                if(d.ok) {
                    let fecha = new Date().toLocaleDateString();
                    let msg = `*EGARPRES*%0A*Recibo de Pago*%0A*Fecha:* \({fecha}%0A*Cliente:* \){cSel.nombre}%0A*Monto:* \]{parseFloat(m).toLocaleString()}%0A*Nuevo Saldo:* \[{d.saldo.toLocaleString()}%0A¡Gracias por su puntualidad!`;
                    // Usamos el formato oficial de WhatsApp para el enlace
                    let waUrl = `https://wa.me/\({cSel.telefono.replace(/\\D/g,'')}?text=\){msg}`;
                    
                    document.getElementById('feedback').innerHTML = `
                        <div class="alert alert-success"><b>✅ ¡Pago registrado con éxito!</b><br>Nuevo saldo: \]{d.saldo.toLocaleString()}</div>
                        <a href="${waUrl}" class="wa-btn mb-2">📲 ENVIAR POR WHATSAPP</a>
                        <button class="btn btn-outline-secondary w-100" onclick="location.reload()">NUEVA OPERACIÓN</button>
                    `;
                    document.getElementById('btn-pago').style.display = 'none';
                }
            } catch(e) {
                alert('Error al registrar el pago');
                document.getElementById('btn-pago').disabled = false;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_MAIN)

@app.route('/api/clientes')
def clientes():
    q = request.args.get('q', '')
    db = get_db(); c = db.cursor()
    c.execute("SELECT id, nombre, telefono FROM clientes WHERE nombre LIKE ? LIMIT 10", (f"%{q}%",))
    res = [dict(r) for r in c.fetchall()]
    db.close(); return jsonify(res)

@app.route('/api/prestamos/<int:id>')
def prestamos(id):
    db = get_db(); c = db.cursor()
    c.execute("SELECT id, monto_prestado FROM prestamos WHERE cliente_id=? AND estado='ACTIVO'", (id,))
    res = [dict(r) for r in c.fetchall()]
    db.close(); return jsonify(res)

@app.route('/api/pago', methods=['POST'])
def pago():
    data = request.json
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT monto_prestado FROM prestamos WHERE id=?", (data['p_id'],))
    actual = cur.fetchone()[0]
    nuevo = actual - float(data['monto'])
    cur.execute("UPDATE prestamos SET monto_prestado=? WHERE id=?", (nuevo, data['p_id']))
    db.commit(); db.close()
    return jsonify({"ok": True, "saldo": nuevo})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)