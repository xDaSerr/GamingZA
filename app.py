import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Configuración de la aplicación
app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)

# Configuración del Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicia sesión para acceder"
login_manager.login_message_category = "info"

# Clase de Usuario
class User(UserMixin):
    def __init__(self, id, username, role_id):
        self.id = id
        self.username = username
        self.role_id = role_id

    def get_id(self):
        return str(self.id)

# Verificar si el usuario actual es administrador
def es_admin():
    return session.get('role') == 'admin'

# Inyectar estado de sesión y rol en todas las plantillas
@app.context_processor
def inject_user():
    return dict(
        logged_in=current_user.is_authenticated,
        username=current_user.username if current_user.is_authenticated else None,
        es_admin=es_admin()
    )

# Cargar el usuario desde la sesión
@login_manager.user_loader
def load_user(user_id):
    result = db.session.execute(text("SELECT id, username, role_id FROM usuarios WHERE id = :id"), {'id': user_id}).fetchone()
    if result:
        return User(result[0], result[1], result[2])
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login_register():
    if request.method == 'POST':
        if 'login' in request.form:
            username = request.form['username']
            password = request.form['password']
            result = db.session.execute(text("SELECT id, username, password, role_id FROM usuarios WHERE username = :username"), {'username': username}).fetchone()
            if result and result[2] == password:
                user_obj = User(result[0], result[1], result[3])
                login_user(user_obj)
                session['username'] = result[1]
                session['role'] = 'admin' if result[3] == 1 else 'editor' if result[3] == 2 else 'client'
                flash(f'Bienvenido {session["username"]} ({session["role"]})', 'success')
                return redirect(url_for('index'))
            else:
                flash('Usuario o contraseña incorrectos', 'danger')

        elif 'register' in request.form:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            role_id = 3
            db.session.execute(text("""
                INSERT INTO usuarios (username, email, password, role_id)
                VALUES (:username, :email, :password, :role_id)
            """), {'username': username, 'email': email, 'password': password, 'role_id': role_id})
            db.session.commit()
            flash('Registro exitoso', 'success')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
@login_required
def admin_register():
    if not es_admin():
        flash('Acceso denegado: Solo administradores pueden registrar usuarios.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        role_id = 1 if role == 'admin' else 2
        db.session.execute(text("""
            INSERT INTO usuarios (username, email, password, role_id)
            VALUES (:username, :email, :password, :role_id)
        """), {'username': username, 'email': email, 'password': password, 'role_id': role_id})
        db.session.commit()
        flash(f'Usuario {username} registrado como {role}.', 'success')
        return redirect(url_for('admin_register'))

    return render_template('admin_register.html')

@app.route('/admin/agregar_producto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    if not es_admin():
        flash('Acceso denegado: Solo los administradores pueden agregar productos.', 'danger')
        return redirect(url_for('tienda'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        imagen = request.files['imagen']

        if imagen and imagen.filename != '':
            upload_folder = os.path.join('static', 'img', 'MERCH')
            os.makedirs(upload_folder, exist_ok=True)
            ruta_imagen = os.path.join(upload_folder, imagen.filename)
            imagen.save(ruta_imagen)
            ruta_relativa = f'img/MERCH/{imagen.filename}'
        else:
            ruta_relativa = None

        try:
            db.session.execute(text("""
                INSERT INTO productos (nombre, descripcion, precio, imagen, stock)
                VALUES (:nombre, :descripcion, :precio, :imagen, :stock)
            """), {'nombre': nombre, 'descripcion': descripcion, 'precio': precio, 'imagen': ruta_relativa, 'stock': stock})
            db.session.commit()
            flash('Producto agregado exitosamente', 'success')
            return redirect(url_for('tienda'))
        except Exception as e:
            flash(f'Error al agregar el producto: {str(e)}', 'danger')
            return redirect(url_for('agregar_producto'))
    return render_template('agregar_producto.html')

@app.route('/admin/eliminar_producto/<int:producto_id>', methods=['POST'])
@login_required
def eliminar_producto(producto_id):
    if not es_admin():
        flash('Acceso denegado: Solo los administradores pueden eliminar productos.', 'danger')
        return redirect(url_for('tienda'))

    try:
        db.session.execute(text("DELETE FROM productos WHERE id = :id"), {'id': producto_id})
        db.session.commit()
        flash('Producto eliminado exitosamente', 'success')
        return redirect(url_for('tienda'))
    except Exception as e:
        flash(f'Error al eliminar el producto: {str(e)}', 'danger')
        return redirect(url_for('tienda'))

@app.route('/carrito/obtener')
@login_required
def obtener_carrito():
    result = db.session.execute(text("""
        SELECT p.id, p.nombre, p.precio, p.imagen, c.cantidad
        FROM carrito c
        JOIN productos p ON c.producto_id = p.id
        WHERE c.usuario_id = :usuario_id
    """), {'usuario_id': current_user.id}).fetchall()
    carrito_list = [{'id': r[0], 'nombre': r[1], 'precio': r[2], 'imagen': r[3], 'cantidad': r[4]} for r in result]
    return jsonify({'success': True, 'carrito': carrito_list})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('login'))

@app.route('/tienda')
def tienda():
    result = db.session.execute(text("SELECT id, nombre, precio, descripcion, imagen FROM productos")).fetchall()
    return render_template('tienda.html', productos=result)

@app.route('/reviews')
def reviews():
    return render_template('reviews.html')

@app.route('/noticias')
def noticias():
    return render_template('noticias.html')

@app.route('/guias')
def guias():
    return render_template('guias.html')

@app.route('/contactos')
def contactos():
    return render_template('contactos.html')

@app.route('/test_db')
def test_db():
    try:
        result = db.session.execute(text("SELECT current_database();")).fetchone()
        return f"Conexión exitosa a la base de datos: {result[0]}"
    except Exception as e:
        return f"Error al conectar a la base de datos: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
