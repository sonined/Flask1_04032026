from flask import Flask, jsonify, request, g, abort
from http import HTTPStatus
from pathlib import Path
from werkzeug.exceptions import HTTPException

# import for sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, func, ForeignKey
from flask_migrate import Migrate


class Base(DeclarativeBase):
    pass


BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'quotes.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)


class AuthorModel(db.Model):
    __tablename__ = 'authors'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int] = mapped_column(String(32), index= True, unique=True)
    quotes: Mapped[list['QuoteModel']] = relationship(back_populates='author', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
            }


class QuoteModel(db.Model):
    __tablename__ = 'quotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(server_default='1')

    def __init__(self, author, text, rating):
        self.author = author
        self.text  = text
        self.rating = rating


    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "rating": self.rating
        }


@app.errorhandler(HTTPException)
def hancle_exeption(e):
    """Функция для перехвата HTTP ошибок и возврата в виде JSON"""
    return jsonify({"message": e.description}), e.code

# === CRUD ДЛЯ АВТОРОВ ===


@app.route("/authors", methods=["POST"])
def create_author():
       author_data = request.json
       author = AuthorModel(author_data["name"])
       db.session.add(author)
       db.session.commit()
       return author.to_dict(), 201

# === CRUD ДЛЯ ЦИТАТ ===

@app.route("/quotes")
def get_all_quotes():
    quotes_db = db.session.scalars(db.select(QuoteModel)).all()
    quotes = []
    for quote in quotes_db:
        quotes.append(quote.to_dict())
    return jsonify(quotes), 200


@app.route("/quotes/<int:id>")
def get_quote(id):
    quote = db.session.get(QuoteModel, id)
    if quote:
        quote = quote.to_dict()
        return jsonify(quote), 200
    else:
        return jsonify({"error": f"Quote with id={id} not found"}), 404
    

@app.route("/authors/<int:author_id>/quotes")
def get_authors_quotes(author_id):
    author = db.session.get(AuthorModel, author_id)
    quotes = []
    for quote in author.quotes:
        quotes.append(quote.to_dict())
    return jsonify(author=author.to_dict(), quotes=quotes), 200


@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id: int):
   author = db.session.get(AuthorModel, author_id)
   new_quote = request.json
   if author:
        if "rating" in new_quote:
            rating = new_quote['rating']
            if new_quote['rating'] in range(1, 6):
                quote = QuoteModel(author, new_quote["rating"])
        if "text" in new_quote:
            quote = QuoteModel(author, new_quote["text"])
   db.session.add(quote)
   db.session.commit()
   return quote.to_dict(), 201


@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_data = request.json
    quote = db.session.get(QuoteModel, id)
    if quote:
        if "rating" in new_data:
            rating = new_data['rating']
            if new_data['rating'] in range(1, 6):
                quote.rating = rating 
        if "author" in new_data:
            quote.author = new_data["author"]
        if "text" in new_data:
            quote.text = new_data["text"]
        db.session.commit()
        new_quote = quote.to_dict()
        return jsonify(new_quote), 201
    else:  
        return jsonify({"error": f"Quote with id={id} not found"}), 404


@app.route("/quotes/<int:id>", methods=["DELETE"])
def delete_quote(id: int):
    quote = db.session.get(QuoteModel, id)
    db.session.delete(quote)
    try:
        db.session.commit()
        return jsonify({"message": f"Quote with id={id} has deleted"}), 200
    except Exception as e:
        db.session.rollback()
        abort(503, f"Database error: {e.description}")


@app.route("/quotes/count")
def get_quotes_count():
    count = db.session.scalar(func.count(QuoteModel.id))
    return jsonify(count=count), 200


# @app.route("/quotes", methods=['POST'])
# def create_quote():
#     new_data = request.json
#     if 'author' not in new_data or 'text' not in new_data:
#         return jsonify({"error": "Author or text not found"}), 404
#     else:
#         if 'rating' not in new_data or new_data['rating'] not in range(1, 6):
#             rating = 1
#         else:
#             rating = new_data['rating']
#         new_quote = QuoteModel(author=new_data['author'], text=new_data['text'], rating=rating)
#         db.session.add(new_quote)
#         db.session.commit()
#         new_quote = new_quote.to_dict()
#         return jsonify(new_quote), 201


@app.route("/quotes/filter", methods=['GET'])
def filter_quotes():
    filters = request.args
    author = filters.get('author')
    rating = filters.get('rating')

    result = db.select(QuoteModel)

    if author is not None:
        result = result.filter_by(author=author)

    if rating is not None:
        result = result.filter_by(rating=rating)

    result = db.session.scalars(result).all()

    quotes = []

    for quote in result:
        quotes.append(quote.to_dict())
    return jsonify(quotes), 200


if __name__ == "__main__":
    app.run(debug=True)
