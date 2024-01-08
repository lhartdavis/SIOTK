from flask import Flask, render_template, request, redirect, url_for, flash, g, session, Blueprint
from werkzeug.utils import secure_filename
import json
import os
import random
import time

# Get the directory of the current file (SIOTK.py, for instance)
current_dir = os.path.dirname(os.path.abspath(__file__))

#app = Flask(__name__) # if running locally only
#app.secret_key = "your_secret_key"
#app.config['UPLOAD_FOLDER'] = 'resources'

SIOTK = Blueprint('SIOTK', __name__, template_folder='SIOTK_templates', static_folder='SIOTK_static')

# useful functions
def type_form_filepath(filepath):
    if filepath[-4:] in [".jpg", ".jpeg", ".png", ".svg"]:
        return "image"
    if filepath[-4:] in [".wav", ".mp3"]:
        return "audio"
    return "text"

#Write functions for loading and saving data from/to decks.json:
def load_decks():
    # Construct the path to the file you want to open
    file_path = os.path.join(current_dir, 'decks.json')
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data['decks']

def save_decks(decks):
    # Construct the path to the file you want to open
    file_path = os.path.join(current_dir, 'decks.json')
    with open(file_path, 'r') as f:
        json.dump({"decks": decks}, f)

# Routes and functions here

@SIOTK.route('/')
def infinite_review():
    decks = load_decks()
    current_card = get_random_card(decks)
    return render_template('review.html', current_card=current_card)

def get_random_card(decks):
    # Calculate total weight for all cards
    total_weight = 0
    for deck in decks:
        for card in deck['cards']:
            total_weight += deck['importance'] * card['importance']

    # Select a random card based on weight
    random_weight = random.uniform(0, total_weight)
    current_weight = 0
    for deck in decks:
        for card in deck['cards']:
            current_weight += deck['importance'] * card['importance']
            if current_weight >= random_weight:
                return card

    return None


@SIOTK.route('/fullreview/<deck_name>')
def fullreview(deck_name):
    decks = load_decks()

    if 'review_index' in session:
        session['review_index'] += 1
    else:
        session['review_index'] = 0

    for i, deck in enumerate(decks):
        if deck['name'] == deck_name:
            if len(deck['cards']):
                return render_template('review.html', current_card=deck['cards'][session['review_index'] % len(deck["cards"])])

    return redirect(url_for("fullreview", deck_name = random.choice(decks)['name']))
    

@SIOTK.route('/decks', methods=['GET', 'POST'])
def decks():
    if request.method == 'POST':
        decks = load_decks()

        if request.form.get('action') == 'create':
            decks.append({
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'importance': float(request.form.get('importance')),
                'cards': []
            })

        elif request.form.get('action') == 'edit':
            for deck in decks:
                if deck['name'] == request.form.get('name'):
                    deck['description'] = request.form.get('description')
                    deck['importance'] = float(request.form.get('importance'))

        elif request.form.get('action') == 'delete':
            decks = [deck for deck in decks if deck['name'] != request.form.get('name')]

        save_decks(decks)

    decks = load_decks()
    return render_template('decks.html', decks=decks)


@SIOTK.route('/decks/<deck_name>', methods=['GET', 'POST'])
def deck(deck_name):
    decks = load_decks()
    deck_index = None

    for i, deck in enumerate(decks):
        if deck['name'] == deck_name:
            deck_index = i

    if deck_index is None:
        return redirect(url_for('decks'))

    if request.method == 'POST':
        if request.form.get('action') == 'add_card':

            decks[deck_index]['cards'].append({
                'question': {
                    'type': type_form_filepath(request.form.get('question')),
                    'content': request.form.get('question')
                },
                'answer': {
                    'type': type_form_filepath(request.form.get('answer')),
                    'content': request.form.get('answer')
                },
                'importance': float(request.form.get('importance'))
            })

        elif request.form.get('action') == 'edit_card':
            for i, card in enumerate(decks[deck_index]['cards']):
                if i == int(request.form.get('id')):
                    card['question']['type'] = type_form_filepath(request.form.get('question')),
                    card['question']['content'] = request.form.get('question')
                    card['answer']['type'] = type_form_filepath(request.form.get('answer')),
                    card['answer']['content'] = request.form.get('answer')
                    card['importance'] = float(request.form.get('importance'))

        elif request.form.get('action') == 'delete_card':
            decks[deck_index]['cards'] = [card for card in decks[deck_index]['cards'] if card['question']['content'] != request.form.get('question')]

        elif request.form.get('action') == 'edit_deck':
            decks[deck_index]['description'] = request.form.get('description')
            decks[deck_index]['importance'] = float(request.form.get('importance'))

        save_decks(decks)

    return render_template('deck.html', deck=decks[deck_index])



if __name__ == '__main__':
    app = Flask(__name__) #if running locally only
    app.secret_key = 'your_secret_key'+str(time.time())  # Replace with a real secret key
    app.register_blueprint(SIOTK, url_prefix="")
    app.run(debug=True)
