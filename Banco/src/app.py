from flask import Flask, jsonify, request, session, redirect, url_for
import threading
import secrets
from functools import wraps 

# Clase que representa la cuenta compartida por todos los cajeros
class CuentaBancaria:
    """
    Modelo simple de una cuenta bancaria usada por varios hilos.
    """
    def __init__(self, saldo_inicial):
        # Saldo inicial de la cuenta
        self.saldo = saldo_inicial 
        # Lock para evitar que dos hilos modifiquen el saldo al mismo tiempo
        self.lock = threading.Lock() 

    # Depósito protegido con lock
    def depositar(self, monto):
        # Bloqueo antes de modificar el saldo
        self.lock.acquire() 
        try:
            # Aquí solo un hilo puede entrar a la vez
            self.saldo += monto
            print(f"Depósito de ${monto}. Nuevo saldo: ${self.saldo}")
            return True, self.saldo
        finally:
            # Se libera el lock pase lo que pase
            self.lock.release()

    # Retiro protegido con lock
    def retirar(self, monto):
        # Tomamos el lock antes de checar/modificar saldo
        self.lock.acquire()
        try:
            # Verificamos si alcanza el saldo
            if self.saldo >= monto:
                self.saldo -= monto
                print(f"Retiro de ${monto} exitoso. Nuevo saldo: ${self.saldo}")
                return True, self.saldo
            else:
                return False, f"Fondos insuficientes. Saldo actual: ${self.saldo}"
        finally:
            # Se libera el lock
            self.lock.release()

# Configuración de la app Flask
app = Flask(__name__)
# Clave para sesiones (se genera al vuelo)
app.secret_key = secrets.token_hex(16)

# Datos simulados de cajeros, como si fuera la BD
CAJEROS_DB = {
    "1001": {"id": 1001, "nombre": "Cajero Juan", "pin": "1234"},
    "1002": {"id": 1002, "nombre": "Cajero María", "pin": "4321"},
    "1003": {"id": 1003, "nombre": "Cajero Global", "pin": "0000"}  # Este lo uso para pruebas
}

# Decorador para rutas que requieren sesión iniciada
def login_required(f):
    """
    Solo permite acceso si hay un cajero logueado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cajero_id' not in session:
            return jsonify({
                "status": "auth_error", 
                "message": "Acceso denegado. Inicia sesión primero."
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# Instancia global de la cuenta bancaria (todos los hilos trabajan sobre esta)
cuenta_bancaria = CuentaBancaria(saldo_inicial=1000)

# Rutas de API

@app.route('/saldo', methods=['GET'])
def consultar_saldo():
    """Regresa el saldo actual."""
    return jsonify({
        "status": "success",
        "saldo": cuenta_bancaria.saldo
    })

@app.route('/depositar', methods=['POST'])
@login_required 
def handle_depositar():
    """Procesa un depósito."""
    data = request.json
    cajero_id = session['cajero_id']
    try:
        monto = int(data.get('monto'))
        if monto <= 0:
            return jsonify({"status": "error", "message": "El monto debe ser mayor a cero"}), 400
            
        exito, saldo_o_mensaje = cuenta_bancaria.depositar(monto)
        print(f"[{cajero_id}] Depositó ${monto}. Nuevo saldo: ${saldo_o_mensaje}")
        
        return jsonify({
            "status": "success",
            "message": f"Depósito realizado. Saldo: ${saldo_o_mensaje}",
            "saldo_final": saldo_o_mensaje
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en depósito: {e}"}), 400

@app.route('/retirar', methods=['POST'])
@login_required
def handle_retirar():
    """Procesa un retiro."""
    data = request.json
    cajero_id = session['cajero_id']
    try:
        monto = int(data.get('monto'))
        if monto <= 0:
            return jsonify({"status": "error", "message": "El monto debe ser mayor a cero"}), 400
            
        exito, saldo_o_mensaje = cuenta_bancaria.retirar(monto)
        
        if exito:
            print(f"[{cajero_id}] Retiró ${monto}. Nuevo saldo: ${saldo_o_mensaje}")
            return jsonify({
                "status": "success",
                "message": f"Retiro exitoso. Saldo: ${saldo_o_mensaje}",
                "saldo_final": saldo_o_mensaje
            })
        else:
            return jsonify({
                "status": "error",
                "message": saldo_o_mensaje
            }), 400
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en retiro: {e}"}), 400
    
# Rutas de login/logout

@app.route('/login', methods=['POST'])
def login():
    """Inicio de sesión de cajero."""
    data = request.json
    cajero_id = str(data.get('cajero_id'))
    pin = data.get('pin')

    if cajero_id in CAJEROS_DB and CAJEROS_DB[cajero_id]['pin'] == pin:
        # Guardamos datos en la sesión
        session['cajero_id'] = cajero_id
        session['cajero_nombre'] = CAJEROS_DB[cajero_id]['nombre']
        
        return jsonify({
            "status": "success",
            "message": f"Bienvenido, {session['cajero_nombre']}.",
            "cajero": session['cajero_nombre']
        })
    else:
        return jsonify({
            "status": "error",
            "message": "ID o PIN incorrectos."
        }), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Cierra la sesión."""
    session.pop('cajero_id', None)
    session.pop('cajero_nombre', None)
    return jsonify({"status": "success", "message": "Sesión cerrada."})

@app.route('/cajero_status', methods=['GET'])
def cajero_status():
    """Revisa si alguien está logueado."""
    if 'cajero_id' in session:
        return jsonify({
            "status": "logged_in",
            "cajero_id": session['cajero_id'],
            "cajero_nombre": session['cajero_nombre']
        })
    return jsonify({"status": "logged_out", "message": "Nadie ha iniciado sesión."})

@app.route('/')
def serve_index():
    """Sirve la página principal."""
    return app.send_static_file('index.html')

# Inicio de la app Flask
if __name__ == '__main__':
    # Puerto cambiado a 5001 para no chocar con otro proyecto
    app.run(host='0.0.0.0', port=5001, debug=True)
