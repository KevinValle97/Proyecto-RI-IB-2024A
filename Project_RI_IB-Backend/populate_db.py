import nltk
from flask import Flask
from flask_pymongo import PyMongo
from nltk.corpus import reuters

# Descargar el corpus de Reuters
nltk.download('reuters')

# Configuración de la aplicación Flask
app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/reutersdb'
mongo = PyMongo(app)

# Función para poblar la base de datos
def populate_db():
    articles_collection = mongo.db.articles

    # Limpiar la colección antes de poblarla
    articles_collection.delete_many({})

    for fileid in reuters.fileids():
        filename = fileid
        title = reuters.raw(fileid).split('\n')[0]
        body = reuters.raw(fileid)[len(title)+1:]
        topics = ','.join(reuters.categories(fileid))
        
        article = {
            'filename': filename,
            'title': title,
            'body': body,
            'topics': topics
        }
        articles_collection.insert_one(article)

    print("Base de datos poblada con éxito")

if __name__ == "__main__":
    with app.app_context():
        populate_db()
