"""
servidor.py - API REST para el Sistema de Gestión de Tareas (PFO 2).

Endpoints:
    POST /registro  -> crea un usuario (contraseña hasheada)
    POST /login     -> valida credenciales e inicia sesión
    GET  /tareas    -> página HTML de bienvenida (requiere sesión iniciada)
"""
import os
import sqlite3

from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)
# Clave para firmar la cookie de sesión. En producción, definir SECRET_KEY como variable de entorno.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiar")


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
def get_db():
    """Abre una conexión a SQLite con acceso a columnas por nombre."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea la tabla de usuarios si no existe."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )


@app.cli.command("init-db")
def init_db_command():
    """Comando: flask --app servidor init-db"""
    init_db()
    print(f"Base de datos inicializada en {DATABASE}")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def obtener_credenciales():
    """Extrae y valida usuario/contraseña del JSON. Devuelve (usuario, contraseña) o (None, None)."""
    data = request.get_json(silent=True) or {}
    usuario = str(data.get("usuario", "")).strip()
    password = str(data.get("contraseña", ""))
    if not usuario or not password:
        return None, None
    return usuario, password


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.route("/registro", methods=["POST"])
def registro():
    usuario, password = obtener_credenciales()
    if not usuario:
        return jsonify({"error": "Se requieren 'usuario' y 'contraseña'."}), 400

    # Hash con salt aleatorio (nunca se guarda la contraseña en texto plano)
    password_hash = generate_password_hash(password)

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                (usuario, password_hash),
            )
    except sqlite3.IntegrityError:
        # La columna 'usuario' es UNIQUE: el usuario ya existe
        return jsonify({"error": "El usuario ya existe."}), 409

    return jsonify({"mensaje": f"Usuario '{usuario}' registrado correctamente."}), 201


@app.route("/login", methods=["POST"])
def login():
    usuario, password = obtener_credenciales()
    if not usuario:
        return jsonify({"error": "Se requieren 'usuario' y 'contraseña'."}), 400

    with get_db() as conn:
        fila = conn.execute(
            "SELECT password_hash FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()

    # Mismo mensaje si falla el usuario o la clave (no revela qué usuarios existen)
    if fila is None or not check_password_hash(fila["password_hash"], password):
        return jsonify({"error": "Credenciales inválidas."}), 401

    session["usuario"] = usuario
    return jsonify({"mensaje": f"Bienvenido, {usuario}. Login exitoso."}), 200


@app.route("/tareas", methods=["GET"])
def tareas():
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"error": "Acceso denegado. Inicie sesión primero."}), 401
    return render_template("index.html", usuario=usuario)


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()  # garantiza que la BD exista al iniciar
    app.run(host="127.0.0.1", port=5000, debug=True)
