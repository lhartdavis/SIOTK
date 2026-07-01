from flask import Blueprint, Flask, render_template, request, redirect, url_for, session
import json
import os
import random
import time

# Get the directory of the current file (SIOTK.py, for instance)
current_dir = os.path.dirname(os.path.abspath(__file__))

# app = Flask(__name__) # if running locally only
# app.secret_key = "your_secret_key"
# app.config['UPLOAD_FOLDER'] = 'resources'

SIOTK = Blueprint(
    "SIOTK", __name__, template_folder="SIOTK_templates", static_folder="SIOTK_static"
)

MANAGEMENT_PASSWORD = "1234"
PASSWORD_COOLDOWN_SECONDS = 10
ALLOWED_IPV4S = {"REPLACE_WITH_MY_IP"}


# useful functions
def type_form_filepath(filepath):
    extension = os.path.splitext(filepath)[1].lower()
    if extension in [".jpg", ".jpeg", ".png", ".svg"]:
        return "image"
    if extension in [".wav", ".mp3"]:
        return "audio"
    return "text"


# Write functions for loading and saving data from/to decks.json:
def load_decks():
    # Construct the path to the file you want to open
    file_path = os.path.join(current_dir, "decks.json")
    with open(file_path, "r") as f:
        data = json.load(f)
    return data["decks"]


def save_decks(decks):
    # Construct the path to the file you want to open
    file_path = os.path.join(current_dir, "decks.json")
    with open(file_path, "w") as f:
        json.dump({"decks": decks}, f)


def is_allowed_ip():
    return request.remote_addr in ALLOWED_IPV4S


def is_management_authenticated():
    return is_allowed_ip() or session.get("management_authenticated") is True


def is_safe_next_url(next_url):
    return bool(next_url) and next_url.startswith("/") and not next_url.startswith("//")


def get_login_next_url():
    next_url = request.values.get("next") or url_for("SIOTK.decks")
    if not is_safe_next_url(next_url):
        return url_for("SIOTK.decks")
    return next_url


def get_cooldown_remaining():
    cooldown_until = session.get("password_cooldown_until", 0)
    remaining = cooldown_until - time.time()
    if remaining <= 0:
        session.pop("password_cooldown_until", None)
        return 0
    return int(remaining) + 1


def require_management_auth():
    if is_management_authenticated():
        return None

    next_url = request.full_path if request.query_string else request.path
    return redirect(url_for("SIOTK.login", next=next_url))


# Routes and functions here


@SIOTK.route("/")
def infinite_review():
    decks = load_decks()
    current_card = get_random_card(decks)
    return render_template("review.html", current_card=current_card)


def get_random_card(decks):
    # Calculate total weight for all cards
    total_weight = 0
    for deck in decks:
        for card in deck["cards"]:
            total_weight += deck["importance"] * card["importance"]

    # Select a random card based on weight
    random_weight = random.uniform(0, total_weight)
    current_weight = 0
    for deck in decks:
        for card in deck["cards"]:
            current_weight += deck["importance"] * card["importance"]
            if current_weight >= random_weight:
                return card

    return None


@SIOTK.route("/fullreview/<deck_name>")
def fullreview(deck_name):
    decks = load_decks()

    if "review_index" in session:
        session["review_index"] += 1
    else:
        session["review_index"] = 0

    for i, deck in enumerate(decks):
        if deck["name"] == deck_name:
            if len(deck["cards"]):
                return render_template(
                    "review.html",
                    current_card=deck["cards"][session["review_index"] % len(deck["cards"])],
                )

    return redirect(url_for("fullreview", deck_name=random.choice(decks)["name"]))


@SIOTK.route("/login", methods=["GET", "POST"])
def login():
    next_url = get_login_next_url()
    error = None

    if is_allowed_ip():
        return redirect(next_url)

    cooldown_remaining = get_cooldown_remaining()

    if request.method == "POST":
        if cooldown_remaining:
            error = "Too many attempts."
        elif request.form.get("password") == MANAGEMENT_PASSWORD:
            session["management_authenticated"] = True
            session.pop("password_cooldown_until", None)
            return redirect(next_url)
        else:
            session["password_cooldown_until"] = time.time() + PASSWORD_COOLDOWN_SECONDS
            cooldown_remaining = PASSWORD_COOLDOWN_SECONDS
            error = "Incorrect password."

    return render_template(
        "login.html",
        cooldown_remaining=cooldown_remaining,
        error=error,
        next_url=next_url,
    )


@SIOTK.route("/logout")
def logout():
    session.pop("management_authenticated", None)
    session.pop("password_cooldown_until", None)
    return redirect(url_for("SIOTK.infinite_review"))


@SIOTK.route("/decks", methods=["GET", "POST"])
def decks():
    auth_redirect = require_management_auth()
    if auth_redirect:
        return auth_redirect

    if request.method == "POST":
        decks = load_decks()

        if request.form.get("action") == "create":
            decks.append(
                {
                    "name": request.form.get("name"),
                    "description": request.form.get("description"),
                    "importance": float(request.form.get("importance")),
                    "cards": [],
                }
            )

        elif request.form.get("action") == "edit":
            for deck in decks:
                if deck["name"] == request.form.get("name"):
                    deck["description"] = request.form.get("description")
                    deck["importance"] = float(request.form.get("importance"))

        elif request.form.get("action") == "delete":
            decks = [deck for deck in decks if deck["name"] != request.form.get("name")]

        save_decks(decks)

    decks = load_decks()
    return render_template(
        "decks.html",
        decks=decks,
        show_logout=session.get("management_authenticated") is True,
    )


@SIOTK.route("/decks/<deck_name>", methods=["GET", "POST"])
def deck(deck_name):
    auth_redirect = require_management_auth()
    if auth_redirect:
        return auth_redirect

    decks = load_decks()
    deck_index = None

    for i, deck in enumerate(decks):
        if deck["name"] == deck_name:
            deck_index = i

    if deck_index is None:
        return redirect(url_for("decks"))

    if request.method == "POST":
        if request.form.get("action") == "add_card":
            decks[deck_index]["cards"].append(
                {
                    "question": {
                        "type": type_form_filepath(request.form.get("question")),
                        "content": request.form.get("question"),
                    },
                    "answer": {
                        "type": type_form_filepath(request.form.get("answer")),
                        "content": request.form.get("answer"),
                    },
                    "importance": float(request.form.get("importance")),
                }
            )

        elif request.form.get("action") == "edit_card":
            for i, card in enumerate(decks[deck_index]["cards"]):
                if i == int(request.form.get("id")):
                    card["question"]["type"] = type_form_filepath(request.form.get("question"))
                    card["question"]["content"] = request.form.get("question")
                    card["answer"]["type"] = type_form_filepath(request.form.get("answer"))
                    card["answer"]["content"] = request.form.get("answer")
                    card["importance"] = float(request.form.get("importance"))

        elif request.form.get("action") == "delete_card":
            decks[deck_index]["cards"] = [
                card
                for card in decks[deck_index]["cards"]
                if card["question"]["content"] != request.form.get("question")
            ]

        elif request.form.get("action") == "edit_deck":
            decks[deck_index]["description"] = request.form.get("description")
            decks[deck_index]["importance"] = float(request.form.get("importance"))

        save_decks(decks)

    return render_template(
        "deck.html",
        deck=decks[deck_index],
        show_logout=session.get("management_authenticated") is True,
    )


if __name__ == "__main__":
    app = Flask(__name__)  # if running locally only
    app.secret_key = "your_secret_key" + str(time.time())  # Replace with a real secret key
    app.register_blueprint(SIOTK, url_prefix="")
    app.run(debug=True, port=52742)
