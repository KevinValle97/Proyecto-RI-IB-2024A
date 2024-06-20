from flask import Blueprint, jsonify, request, render_template
from .database import mongo
from bson.objectid import ObjectId
import json
import os
from datetime import datetime
from collections import defaultdict
import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import CategorizedPlaintextCorpusReader

main = Blueprint('main', __name__)


DROP_STOPWORDS = True
STEMMING = False
codelist = ['\r', '\n', '\t']

# Load stopwords
def load_stopwords(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        stopwords = file.read().splitlines()
    return stopwords

stoplist = load_stopwords('reuters/stopwords')

# Text parsing function
def parse_doc(text):
    text = text.lower()
    text = re.sub(r'&(.)+', "", text)
    text = re.sub(r'pct', 'percent', text)
    text = re.sub(r"[^\w\d'\s]+", '', text)
    text = re.sub(r'[^\x00-\x7f]', r'', text)
    if text.isdigit(): text = ""
    for code in codelist:
        text = re.sub(code, ' ', text)
    text = re.sub('\s+', ' ', text)
    return text

# Token parsing function
def parse_words(text, stoplist):
    tokens = text.split()
    re_punc = re.compile('[%s]' % re.escape(string.punctuation))
    tokens = [re_punc.sub('', w) for w in tokens]
    tokens = [word for word in tokens if word.isalpha()]
    tokens = [word for word in tokens if len(word) > 2]
    tokens = [word for word in tokens if len(word) < 21]
    if DROP_STOPWORDS:
        tokens = [w for w in tokens if not w in stoplist]
    text = ' '.join(tokens)
    return tokens, text

# Load Reuters corpus from local directory
corpus_root = 'reuters'
reuters = CategorizedPlaintextCorpusReader(
    corpus_root,
    r'(training|test).*',
    cat_file='cats.txt',
    encoding='ISO-8859-2'
)

# Generador para procesar textos
def generate_processed_texts(docs):
    for doc in docs:
        text_string = parse_doc(doc)
        tokens, text_string = parse_words(text_string, stoplist)
        yield text_string

# Procesamiento de textos de entrenamiento y prueba
train_documents = [reuters.raw(fileid) for fileid in reuters.fileids() if fileid.startswith('training/')]
test_documents = [reuters.raw(fileid) for fileid in reuters.fileids() if fileid.startswith('test/')]

train_texts_generator = generate_processed_texts(train_documents)
test_texts_generator = generate_processed_texts(test_documents)

# TF-IDF Vectorization
tfidf_vectorizer = TfidfVectorizer()
train_vectors = tfidf_vectorizer.fit_transform(train_texts_generator)

# Build inverted index for TF-IDF
vocabulario_tfidf = tfidf_vectorizer.get_feature_names_out()
indice_invertido_tfidf = defaultdict(list)
for i, documento in enumerate(train_documents):
    palabras_indices = train_vectors[i].nonzero()[1]
    for indice_palabra in palabras_indices:
        palabra = vocabulario_tfidf[indice_palabra]
        indice_invertido_tfidf[palabra].append(i)

# Query processing
def procesar_consulta(consulta, vectorizador, indice_invertido, train_vectors):
    consulta_vectorizada = vectorizador.transform([consulta])
    consulta_indices = consulta_vectorizada.nonzero()[1]
    consulta_terminos = [vectorizador.get_feature_names_out()[i] for i in consulta_indices]

    documentos_relevantes = set()
    for termino in consulta_terminos:
        if termino in indice_invertido:
            documentos_relevantes.update(indice_invertido[termino])

    documentos_relevantes = list(documentos_relevantes)
    if not documentos_relevantes:
        return []

    relevantes_tfidf = train_vectors[documentos_relevantes]
    similitudes = cosine_similarity(consulta_vectorizada, relevantes_tfidf).flatten()

    return [(doc, similitud) for doc, similitud in zip(documentos_relevantes, similitudes)]

# Función para clasificar documentos
def rankear_documentos(documentos_similitudes, nombres_archivos, top_n=5):
    documentos_similitudes.sort(key=lambda x: x[1], reverse=True)
    documentos_rankeados = [(nombres_archivos[doc], similitud) for doc, similitud in documentos_similitudes[:top_n]]
    
    # Concatenar la carpeta y el nombre del archivo
    documentos_rankeados_con_ruta = [(os.path.join('training', nombres_archivos[doc]), similitud) for doc, similitud in documentos_similitudes[:top_n]]
    
    return documentos_rankeados_con_ruta


# Obtener nombres de documentos de entrenamiento y prueba
train_docs = [os.path.basename(fileid) for fileid in reuters.fileids() if fileid.startswith('training/')]
test_docs = [os.path.basename(fileid) for fileid in reuters.fileids() if fileid.startswith('test/')]


# Obtener documentos
def get_document_content(file_id):
    return reuters.raw(file_id)

# Ruta para buscar la query
@main.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data['query']
    documentos_similitudes_tfidf = procesar_consulta(query, tfidf_vectorizer, indice_invertido_tfidf, train_vectors)
    documentos_rankeados_tfidf = rankear_documentos(documentos_similitudes_tfidf, train_docs)

    documentos_content = [{'title': reuters.raw(file_id).split('\n')[0], 'content': '\n'.join(get_document_content(file_id).split('\n')[1:])} for file_id, _ in documentos_rankeados_tfidf]

    print("Received query:", query)
    save_search_result('search', query, documentos_content)
    return jsonify({"message": "Query received", "query": query, "result": documentos_content})

# Guardar resultados de búsqueda
def save_search_result(search_type, query, result):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    search_entry = {
        'timestamp': timestamp,
        'search_type': search_type,
        'query': query,
        'result': result
    }
    file_path = 'search_results.json'
    
    if os.path.exists(file_path):
        with open(file_path, 'r+') as file:
            data = json.load(file)
            data.append(search_entry)
            file.seek(0)
            json.dump(data, file, indent=4)
    else:
        with open(file_path, 'w') as file:
            json.dump([search_entry], file, indent=4)

# Ruta para obtener todos los documentos
@main.route('/articles', methods=['GET'])
def get_articles():
    articles = mongo.db.articles.find()
    data = []
    for article in articles:
        data.append({
            'id': str(article['_id']),
            'title': article['title'],
            'body': article['body'],
            'topics': article['topics']
        })
    save_search_result('all_articles', 'N/A', data)
    return jsonify(data)

# Ruta para obtener un documento por ID
@main.route('/articles/<id>', methods=['GET'])
def get_article(id):
    article = mongo.db.articles.find_one({'_id': ObjectId(id)})
    result = {}
    if article:
        result = {
            'id': str(article['_id']),
            'title': article['title'],
            'body': article['body'],
            'topics': article['topics']
        }
    else:
        result = {'error': 'Article not found'}
    
    save_search_result('article_by_id', id, result)
    return jsonify(result)

# Ruta para obtener un documento por título
@main.route('/articles/title/<title>', methods=['GET'])
def get_article_by_title(title):
    article = mongo.db.articles.find_one({'title': {'$regex': title, '$options': 'i'}})
    result = {}
    if article:
        result = {
            'id': str(article['_id']),
            'title': article['title'],
            'body': article['body'],
            'topics': article['topics']
        }
    else:
        result = {'error': 'Article not found'}
    
    save_search_result('article_by_title', title, result)
    return jsonify(result)

# Ruta para obtener documentos por tópico
@main.route('/articles/body/<body>', methods=['GET'])
def get_articles_by_body(body):
    articles = mongo.db.articles.find({'body': {'$regex': body, '$options': 'i'}})
    result = []
    for article in articles:
        article_data = {
            'id': str(article['_id']),
            'title': article['title'],
            'body': article['body'],
            'topics': article['topics']
        }
        result.append(article_data)

    save_search_result('articles_by_body', body, result)
    return jsonify({'articles': result})


