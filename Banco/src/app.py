from flask import Flask, jsonify, request, session, redirect, url_for
import threading
import secrets
from functools import wraps 

# --- 1. CLASE DEL RECURSO COMPARTIDO: CuentaBancaria ---
class CuentaBancaria:
    """
    Representa la cuenta bancaria central a la que acceden todos los cajeros.
    Es el recurso compartido y requiere sincronización.
    """
    def __init__(self, saldo_inicial):
        # El saldo es el dato que debe ser protegido
        self.saldo = saldo_inicial 
        # El Mutex (Lock) para garantizar la exclusión mutua
        self.lock = threading.Lock() 

    # --- MÉTODO PROTEGIDO: Depósito ---
    def depositar(self, monto):
        # La operación de depósito es una sección crítica (Leer-Modificar-Escribir) [cite: 51, 25]
        # Si no se protege, un depósito podría 'perderse' [cite: 52]
        
        # 1. Adquirir el permiso/bloqueo (mutex.lock())
        self.lock.acquire() 
        try:
            # Sección Crítica: Solo un hilo a la vez puede ejecutar este bloque.
            self.saldo += monto
            print(f"Depósito de ${monto}. Nuevo saldo: ${self.saldo}")
            return True, self.saldo
        finally:
            # 2. Liberar el permiso/bloqueo (mutex.unlock())
            self.lock.release()

    # --- MÉTODO PROTEGIDO: Retiro ---
    def retirar(self, monto):
        # La operación de retiro también es una sección crítica [cite: 28, 29]
        
        # 1. Adquirir el permiso/bloqueo (mutex.lock())
        self.lock.acquire()
        try:
            # Lógica de verificación y modificación protegida
            # 
            if self.saldo >= monto:
                # La secuencia "Leer-Modificar-Escribir" es ahora atómica [cite: 26, 82]
                self.saldo -= monto
                print(f"Retiro de ${monto} exitoso. Nuevo saldo: ${self.saldo}")
                return True, self.saldo
            else:
                return False, f"Fondos insuficientes. Saldo actual: ${self.saldo}"
        finally:
            # 2. Liberar el permiso/bloqueo (mutex.unlock())
            self.lock.release()

# --- 2. CONFIGURACIÓN DE FLASK ---
app = Flask(__name__)
# Es obligatorio usar una clave secreta para manejar las sesiones
app.secret_key = secrets.token_hex(16)

# --- DATOS SIMULADOS DE CAJEROS (Base de Datos) ---
# Usaremos esto para simular la validación del login
CAJEROS_DB = {
    "1001": {"id": 1001, "nombre": "Cajero Juan", "pin": "1234"},
    "1002": {"id": 1002, "nombre": "Cajero María", "pin": "4321"},
    "1003": {"id": 1003, "nombre": "Cajero Global", "pin": "0000"} # Para pruebas de estrés
}

# --- FUNCIÓN DECORADORA PARA PROTEGER RUTAS ---
def login_required(f):
    """
    Decorador para asegurar que solo los usuarios logueados accedan a ciertas rutas.
    """
    @wraps(f) # Importa 'wraps' de functools
    def decorated_function(*args, **kwargs):
        if 'cajero_id' not in session:
            # Si no hay cajero_id en la sesión, se niega el acceso
            return jsonify({
                "status": "auth_error", 
                "message": "Acceso denegado. Por favor, inicie sesión."
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# Creamos UNA ÚNICA instancia de CuentaBancaria (el recurso compartido)
# Usaremos el Saldo Inicial para el Caso de Prueba 1 y 2 [cite: 59, 73]
cuenta_bancaria = CuentaBancaria(saldo_inicial=1000)

# --- 3. RUTAS API REST ---

@app.route('/saldo', methods=['GET'])
def consultar_saldo():
    """Consulta el saldo actual."""
    # La lectura simple del saldo NO es la sección crítica [cite: 25]
    return jsonify({
        "status": "success",
        "saldo": cuenta_bancaria.saldo
    })

@app.route('/depositar', methods=['POST'])
@login_required 
def handle_depositar():
    """Maneja las peticiones de depósito."""
    data = request.json
    cajero_id = session['cajero_id']
    try:
        monto = int(data.get('monto'))
        if monto <= 0:
            return jsonify({"status": "error", "message": "El monto debe ser positivo"}), 400
            
        exito, saldo_o_mensaje = cuenta_bancaria.depositar(monto)
        print(f"[{cajero_id}] - Depósito de ${monto}. Nuevo saldo: ${saldo_o_mensaje}")
        
        return jsonify({
            "status": "success",
            "message": f"Depósito exitoso. Saldo: ${saldo_o_mensaje}",
            "saldo_final": saldo_o_mensaje
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al procesar depósito: {e}"}), 400

@app.route('/retirar', methods=['POST'])
@login_required
def handle_retirar():
    """Maneja las peticiones de retiro."""
    data = request.json
    cajero_id = session['cajero_id']
    try:
        monto = int(data.get('monto'))
        if monto <= 0:
            return jsonify({"status": "error", "message": "El monto debe ser positivo"}), 400
            
        exito, saldo_o_mensaje = cuenta_bancaria.retirar(monto)
        
        if exito:
            print(f"[{cajero_id}] - Retiro de ${monto} exitoso. Nuevo saldo: ${saldo_o_mensaje}")
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
        return jsonify({"status": "error", "message": f"Error al procesar retiro: {e}"}), 400
    
# --- RUTAS DE AUTENTICACIÓN ---

@app.route('/login', methods=['POST'])
def login():
    """Maneja el inicio de sesión del cajero."""
    data = request.json
    cajero_id = str(data.get('cajero_id')) # El ID del cajero (Ej: 1001)
    pin = data.get('pin')

    if cajero_id in CAJEROS_DB and CAJEROS_DB[cajero_id]['pin'] == pin:
        # Éxito: Guardar el ID y nombre del cajero en la sesión
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
            "message": "ID de Cajero o PIN incorrectos."
        }), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Cierra la sesión del cajero."""
    session.pop('cajero_id', None)
    session.pop('cajero_nombre', None)
    return jsonify({"status": "success", "message": "Sesión cerrada."})

@app.route('/cajero_status', methods=['GET'])
def cajero_status():
    """Verifica si hay un cajero logueado."""
    if 'cajero_id' in session:
        return jsonify({
            "status": "logged_in",
            "cajero_id": session['cajero_id'],
            "cajero_nombre": session['cajero_nombre']
        })
    return jsonify({"status": "logged_out", "message": "Nadie ha iniciado sesión."})

@app.route('/')
def serve_index():
    """Sirve la página principal (index.html) desde la carpeta static."""
    return app.send_static_file('index.html')

# --- 4. INICIO DE LA APLICACIÓN ---
if __name__ == '__main__':
    # Usaremos '0.0.0.0' para que la app sea accesible desde otros dispositivos en tu red (Fase 4)
    # Por defecto, se ejecuta en el puerto 5000.
    app.run(host='0.0.0.0', port=5001, debug=True)



