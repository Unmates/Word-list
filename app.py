import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client= MongoClient("mongodb://farelli:shakti@ac-mrep1ay-shard-00-00.kxxqxff.mongodb.net:27017,ac-mrep1ay-shard-00-01.kxxqxff.mongodb.net:27017,ac-mrep1ay-shard-00-02.kxxqxff.mongodb.net:27017/?ssl=true&replicaSet=atlas-afnrt3-shard-0&authSource=admin&retryWrites=true&w=majority")

db = client.dbsparta

app = Flask(__name__)

@app.route('/')
def index():
    word_result = db.words.find({}, {'_id':False})
    words = []
    for word in word_result:
        definition= word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    return render_template('index.html', words=words)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key= 'f9e50420-e25e-4a19-9fa9-7930a5acd3d1'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definition = response.json()

    if not definition:
        return redirect(url_for(
            'error',
            msg= keyword
        ))
    if type(definition[0]) is str:
        suggestion= ','.join(definition)
        return redirect(url_for(
            'error',
            suggestion=suggestion,
            msg=keyword
        ))

    status = request.args.get('status_give', 'new')
    return render_template('detail.html', word=keyword, definition=definition, status=status)

@app.route('/api/save_word', methods=['POST'])
def apisave():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definition = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definition,
        'date':datetime.now().strftime('%Y-%m-%d')
    }
    db.words.insert_one(doc)
    return jsonify({
        'result' : 'success',
        'msg' : f'the word {word} was saved'
    })

@app.route('/api/delete_word', methods=['POST'])
def apidel():
    word = request.form.get('word_give')
    db.words.delete_one({'word':  word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result' : 'success',
        'msg' : f'the word {word} was deleted'
    })
    
@app.route('/api/get_ex', methods=["GET"])
def get_exs():
    word= request.args.get('word')
    example_data= db.examples.find({'word' : word})
    examples=[]
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id'))
        })
    return jsonify({
        'result' : 'success',
        'example' : examples
        })
    
@app.route('/api/save_ex', methods=["POST"])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc={
        'word' : word,
        'example' : example
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'your example: "{example}" was saved'
    })
    
@app.route('/api/delete_ex', methods=["POST"])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg' : f'Your example for the word "{word}", was deleted'
    })

@app.route('/error')
def error():
    msg= request.args.get('msg')
    suggestion= request.args.get('suggestion')
    suggest=''
    if suggestion != None:
        suggest= suggestion.split(',')
    return render_template('error.html', msg=msg, suggest=suggest)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
 