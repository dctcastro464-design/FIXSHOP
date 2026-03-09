from flask import Flask, render_template, request, redirect, session
import sqlite3
import qrcode
import os

app = Flask(__name__)
app.secret_key = "clave_secreta"


def conectar():
    return sqlite3.connect("database.db")


def init_db():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reparaciones(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden TEXT,
        cliente TEXT,
        telefono TEXT,
        marca TEXT,
        modelo TEXT,
        imei TEXT,
        falla TEXT,
        estado TEXT,
        costo INTEGER,
        pagado INTEGER,
        vendedor TEXT,
        factura TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# LOGIN

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        if usuario == "admin" and password == "admin":
            session["admin"] = True
            return redirect("/panel")

    return render_template("login.html")


# PANEL ADMIN

@app.route("/panel")
def panel():

    if "admin" not in session:
        return redirect("/")

    conn = conectar()
    cursor = conn.cursor()

    busqueda = request.args.get("buscar")

    if busqueda:
        cursor.execute("""
        SELECT * FROM reparaciones
        WHERE cliente LIKE ?
        OR imei LIKE ?
        OR orden LIKE ?
        """, (f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"))

    else:
        cursor.execute("SELECT * FROM reparaciones")

    datos = cursor.fetchall()

    conn.close()

    return render_template("panel.html", datos=datos)


# NUEVA REPARACION

@app.route("/nueva", methods=["GET", "POST"])
def nueva():

    if request.method == "POST":

        cliente = request.form["cliente"]
        telefono = request.form["telefono"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        imei = request.form["imei"]
        falla = request.form["falla"]
        costo = request.form["costo"]
        pagado = request.form["pagado"]
        vendedor = request.form["vendedor"]
        factura = request.form["factura"]

        orden = "REP-" + imei[-4:]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO reparaciones
        (orden,cliente,telefono,marca,modelo,imei,falla,estado,costo,pagado,vendedor,factura)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            orden,
            cliente,
            telefono,
            marca,
            modelo,
            imei,
            falla,
            "Recibido",
            costo,
            pagado,
            vendedor,
            factura
        ))

        conn.commit()
        conn.close()

        url = "http://127.0.0.1:5000/estado/" + orden

        img = qrcode.make(url)

        carpeta_qr = os.path.join(app.root_path, "static", "qr")

        os.makedirs(carpeta_qr, exist_ok=True)

        ruta = os.path.join(carpeta_qr, orden + ".png")

        img.save(ruta)

        return redirect("/panel")

    return render_template("nueva_reparacion.html")


# CAMBIAR ESTADO

@app.route("/estado_cambiar", methods=["POST"])
def estado_cambiar():

    orden = request.form["orden"]
    estado = request.form["estado"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE reparaciones
    SET estado=?
    WHERE orden=?
    """, (estado, orden))

    conn.commit()
    conn.close()

    return redirect("/panel")


# PAGINA CLIENTE

@app.route("/estado/<orden>")
def estado(orden):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM reparaciones
    WHERE orden=?
    """, (orden,))

    dato = cursor.fetchone()

    conn.close()

    return render_template("estado.html", dato=dato)


if __name__ == "__main__":
    app.run(debug=True)