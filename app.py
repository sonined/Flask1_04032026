from flask import Flask, jsonify, request
from http import HTTPStatus
from pathlib import Path
import random
import sqlite3


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db"  # <- тут путь к БД


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

#quotes = [
#   {
#       "id": 3,
#       "author": "Rick Cook",
#       "rating": 4,
#       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
#   },
#   {
#       "id": 5,
#       "author": "Waldi Ravens",
#       "rating": 3,
#       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
#   },
#   {
#       "id": 6,
#       "author": "Mosher’s Law of Software Engineering",
#       "rating": 5,
#       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
#   },
#   {
#       "id": 8,
#       "author": "Yoggi Berra",
#       "rating": 2,
#       "text": "В теории, теория и практика неразделимы. На практике это не так."
#   },

#]


@app.route("/quotes")
def get_all_quotes():
    select_quotes = "SELECT * from quotes"

    # Подключение в БД
    connection = sqlite3.connect("store.db")

    # Создаем cursor, он позволяет делать SQL-запросы
    cursor = connection.cursor()

    # Выполняем запрос:
    cursor.execute(select_quotes)

    # Извлекаем результаты запроса
    quotes_db = cursor.fetchall()  # get list[tuple]
    print(f"{quotes_db=}")

    # Закрыть курсор:
    cursor.close()

    # Закрыть соединение:
    connection.close()

    # Подготовка данных для отправки в правильном формате
    # Необходимо выполнить преобразование: 
    # list[tuple] -> list[dict]
    keys = {"id", "author", "text"}
    quotes = []
    for quote_db in quotes_db:
        quote = dict(zip(keys, quote_db))
        quotes.append(quote)
    return jsonify(quotes), 200


@app.route("/quotes/<int:id>")
def get_quote(id):
    select_quote = "SELECT * FROM quotes WHERE id=?;"
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    cursor.execute(select_quote, (id,))
    quote_db = cursor.fetchone()
    cursor.close()
    connection.close()
    if quote_db:
        keys = {"id", "author", "text"}
        quote = dict(zip(keys, quote_db))
        return jsonify(quote), 200
    else:
        return f"Quote with id={id} not found", 404


@app.route("/quotes/count")
def get_quotes_count():
    return {"count":len(quotes)}


@app.route("/quotes", methods=['POST'])
def create_quote():
    insert_quote = "INSERT INTO quotes (author, text) VALUES (?, ?);"
    select_quote = "SELECT * FROM quotes WHERE id=?;"
    new_quote = request.json
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    cursor.execute(insert_quote, (new_quote["author"], new_quote["text"]))
    connection.commit()
    new_id = cursor.lastrowid
    cursor.execute(select_quote, (new_id,))
    quote_db = cursor.fetchone()
    cursor.close()
    connection.close()
    keys = {"id", "author", "text"}
    quote = dict(zip(keys, quote_db))
    return jsonify(quote), 201


@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    update_quote_author = "UPDATE quotes SET author=? WHERE id=?;"
    update_quote_text = "UPDATE quotes SET text=? WHERE id=?;"
    select_quote = "SELECT * FROM quotes WHERE id=?;"
    new_data = request.json

    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    
    if "author" in new_data:
        cursor.execute(update_quote_author, (new_data["author"], id))
    connection.commit()

    if "text" in new_data:
        cursor.execute(update_quote_text, (new_data["text"], id))
    connection.commit()

    if cursor.rowcount > 0:
        cursor.execute(select_quote, (id,))
        quote_db = cursor.fetchone()
        keys = {"id", "author", "text"}
        quote = dict(zip(keys, quote_db))
        return jsonify(quote), 200
    else:
        return jsonify({"error": f"Quote not update"}), 500

    cursor.close()
    connection.close()


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id: int):
    delete_quote = "DELETE FROM quotes WHERE id=?;"

    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()

    cursor.execute(delete_quote, (quote_id,))
    connection.commit()

    if cursor.rowcount > 0:
        return jsonify({"message": f"Quote with id={quote_id} has deleted"}), 200
    else:
        return jsonify({"error": f"Quote not deleted"}), 500
    
    cursor.close()
    connection.close()


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