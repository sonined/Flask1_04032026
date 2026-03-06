from flask import Flask, jsonify, request, g, abort
from http import HTTPStatus
from pathlib import Path
from werkzeug.exceptions import HTTPException
import random
import sqlite3


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "quotes.db"  # <- тут путь к БД


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(path_to_db)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.errorhandler(HTTPException)
def hancle_exeption(e):
    """Функция для перехвата HTTP ошибок и возврата в виде JSON"""
    return jsonify({"message": e.description}), e.code


def new_table(name_db: str):
    create_table = """
    CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT NOT NULL,
    text TEXT NOT NULL,
    rating INTEGER NOT NULL
    );
    """
    # Подключение в БД
    connection = sqlite3.connect(name_db)

    # Создаем cursor, он позволяет делать SQL-запросы
    cursor = connection.cursor()

    # Выполняем запрос:
    cursor.execute(create_table)

    # Фиксируем выполнение(транзакцию)
    connection.commit()

    # Закрыть курсор:
    cursor.close()

    # Закрыть соединение:
    connection.close()


@app.route("/quotes")
def get_all_quotes():
    select_quotes = "SELECT * from quotes"

    # Создаем cursor, он позволяет делать SQL-запросы
    cursor = get_db().cursor()

    # Выполняем запрос:
    cursor.execute(select_quotes)

    # Извлекаем результаты запроса
    quotes_db = cursor.fetchall()  # get list[tuple]
    print(f"{quotes_db=}")

    # Подготовка данных для отправки в правильном формате
    # Необходимо выполнить преобразование: 
    # list[tuple] -> list[dict]
    keys = {"id", "author", "text", "rating"}
    quotes = []
    for quote_db in quotes_db:
        quote = dict(zip(keys, quote_db))
        quotes.append(quote)
    return jsonify(quotes), 200


@app.route("/quotes/<int:id>")
def get_quote(id):
    select_quote = "SELECT * FROM quotes WHERE id=?"
    cursor = get_db().cursor()
    cursor.execute(select_quote, (id,))
    quote_db = cursor.fetchone() # Получаем одну запись из БД
    if quote_db:
        keys = {"id", "author", "text", "rating"}
        quote = dict(zip(keys, quote_db))
        return jsonify(quote), 200
    else:
        return {"error": f"Quote with id={id} not found"}, 404


@app.route("/quotes/count")
def get_quotes_count():
    select_count = "SELECT count(*) as count FROM quotes"
    cursor = get_db().cursor()
    cursor.execute(select_count)
    count = cursor.fetchone()
    if count:
        return jsonify(count=count[0]), 200
    abort(503) # вернем ошибку 503


@app.route("/quotes", methods=['POST'])
def create_quote():
    insert_quote = "INSERT INTO quotes (author, text, rating) VALUES (?, ?, ?)"
    new_quote = request.json
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(insert_quote, (new_quote["author"], new_quote["text"], new_quote["rating"]))
    new_id = cursor.lastrowid # Получаем их БД id новой цитаты
    connection.commit()
    new_quote['id'] = new_id
    return jsonify(new_quote), 201


@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_data = request.json
    attributes: set = set(new_data.keys()) & {'author', 'rating', 'text'}
    if "rating" in attributes and new_data["rating"] not in range(1, 6):
        attributes.remove("rating")
    if attributes:
        update_quote = f"UPDATE quotes SET {', '.join(attr + '=?' for attr in attributes)} WHERE id=?"
        params = tuple(new_data.get(attr) for attr in attributes) + (id, )
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute(update_quote, params)
        rows = cursor.rowcount
        if rows:
            connection.commit()
            cursor.close()
            responce, status_code = get_quote(id)
            if  status_code == 200:
                return responce, HTTPStatus.OK
        connection.rollback()
    else:
        responce, status_code = get_quote(id)
        if  status_code == 200:
            return responce, HTTPStatus.OK
    abort(404, f"Quote with id={id} not found.")


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id: int):
    delete_quote = "DELETE FROM quotes WHERE id=?"
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(delete_quote, (quote_id,))
    if cursor.rowcount > 0:
        connection.commit()
        cursor.close()
        return jsonify({"message": f"Quote with id={quote_id} has deleted"}), 200
    connection.rollback()
    abort(404, f"Quote with id={quote_db} not found")


# @app.route("/quotes/filter", methods=['GET'])
# def filter_quotes():
#     filters = request.args
#     author = filters.get('author')
#     rating = filters.get('rating')

#     result = quotes

#     if author is not None:
#         result = [quote for quote in result if quote.get('author') == author]

#     if rating is not None:
#         result = [quote for quote in result if quote.get('rating') == int(rating)]

#     return result


if __name__ == "__main__":
    new_table('quotes.db')
    app.run(debug=True)