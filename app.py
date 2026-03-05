from flask import Flask, jsonify
from flask import request
import random

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


about_me = {
    "name": "Софья",
    "surname": "Недоступ",
    "email": "sonined@gmail.com"
}

quotes = [
   {
       "id": 3,
       "author": "Rick Cook",
       "rating": 4,
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "rating": 3,
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
   },
   {
       "id": 6,
       "author": "Mosher’s Law of Software Engineering",
       "rating": 5,
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "rating": 2,
       "text": "В теории, теория и практика неразделимы. На практике это не так."
   },

]


@app.route("/")  # Это первый URL, который мы будем обрабатывать
def hello_world():  # Эта функция-обработчик будет вызвана при запросе этого URL
    return "Hello, World!"


@app.route("/about")
def about():
    return about_me


@app.route("/quotes")
def get_all_quotes():
    return quotes


@app.route("/quotes/<int:id>")
def get_quote(id):
    for quote in quotes:
        if quote['id'] == id:
            return quote
    return None


@app.route("/quotes/count")
def get_quotes_count():
    return {"count":len(quotes)}


@app.route("/quotes/random")    
def get_quote_random():
    return random.choice(quotes)


def create_new_id():
    last_id = 0
    for quote in quotes:
        if quote['id'] > last_id:
            last_id = quote['id']
    return last_id + 1


@app.route("/quotes", methods=['POST'])
def create_quote():
    new_quote = request.json
    new_quote["id"] = create_new_id()
    if "rating" not in new_quote or new_quote["rating"] > 5:
        new_quote["rating"] = 1
    quotes.append(new_quote)
    return jsonify(new_quote), 201


@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_data = request.json
    quote = get_quote(id)
    if not quote:
        return f"Quote with id={id} not found", 404
    if "text" in new_data:
        quote["text"] = new_data["text"]
    if "author" in new_data:
        quote["author"] = new_data["author"]
    if "rating" in new_data and 1 <= new_data["rating"] <= 5:
        quote["rating"] = new_data["rating"]
    return quote, 200


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id: int):
    for quote in quotes:
        if quote['id'] == quote_id:
            quotes.remove(quote)
            return jsonify({"message": f"Quote with id={quote_id} has deleted"}), 200
    return f"Quote with id={quote_id} not found", 404


@app.route("/quotes/filter", methods=['GET'])
def filter_quotes():
    filters = request.args
    author = filters.get('author')
    rating = filters.get('rating')

    result = quotes

    if author is not None:
        result = [quote for quote in result if quote.get('author') == author]

    if rating is not None:
        result = [quote for quote in result if quote.get('rating') == int(rating)]

    return result


if __name__ == "__main__":
    app.run(debug=True)