from flask import Flask
from flask_cors import CORS
from .database import init_db

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
    
    # Configuración de la base de datos
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/reutersdb'

    # Inicializar la base de datos
    init_db(app)
    
    # Registrar blueprints
    from .routes import main
    app.register_blueprint(main)
    
    return app
