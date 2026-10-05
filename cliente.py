"""
cliente.py - Cliente interactivo de consola para la API de Gestión de Tareas.
Usa requests.Session para conservar la cookie de sesión tras el login.
"""
import getpass
import re

import requests

URL_BASE = "http://127.0.0.1:5000"
sesion = requests.Session()


def pedir_credenciales():
    usuario = input("Usuario: ").strip()
    password = getpass.getpass("Contraseña (no se muestra al escribir): ").strip()
    return {"usuario": usuario, "contraseña": password}


def mostrar_respuesta(resp):
    """Imprime el estado y el mensaje (JSON) devuelto por el servidor."""
    try:
        cuerpo = resp.json()
        texto = cuerpo.get("mensaje") or cuerpo.get("error")
    except ValueError:
        texto = None  # la respuesta no es JSON (por ejemplo, un error 500 en HTML)
    if texto is None:
        texto = "Error interno del servidor." if resp.status_code >= 500 else "Respuesta sin mensaje."
    print(f"[{resp.status_code}] {texto}")


def registrarse():
    resp = sesion.post(f"{URL_BASE}/registro", json=pedir_credenciales(), timeout=5)
    mostrar_respuesta(resp)


def iniciar_sesion():
    resp = sesion.post(f"{URL_BASE}/login", json=pedir_credenciales(), timeout=5)
    mostrar_respuesta(resp)


def ver_tareas():
    resp = sesion.get(f"{URL_BASE}/tareas", timeout=5)
    if resp.status_code == 200:
        # Extrae el título <h1> del HTML para mostrarlo en consola
        titulo = re.search(r"<h1>(.*?)</h1>", resp.text, re.S)
        print(f"[200] Respuesta HTML recibida: {titulo.group(1) if titulo else ''}")
    else:
        mostrar_respuesta(resp)


def menu():
    opciones = {"1": registrarse, "2": iniciar_sesion, "3": ver_tareas}
    while True:
        print("\n=== Gestión de Tareas ===")
        print("1. Registrarse\n2. Iniciar sesión\n3. Ver tareas\n4. Salir")
        eleccion = input("Elija una opción: ").strip()
        if eleccion == "4":
            print("¡Hasta luego!")
            break
        accion = opciones.get(eleccion)
        if not accion:
            print("Opción inválida.")
            continue
        try:
            accion()
        except requests.exceptions.RequestException:
            print("No se pudo conectar con el servidor. ¿Está en ejecución?")


if __name__ == "__main__":
    menu()