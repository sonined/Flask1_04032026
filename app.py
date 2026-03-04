from flask import Flask

app = Flask(__name__)


@app.route("/")  # Это первый URL, который мы будем обрабатывать
def hello_world():  # Эта функция-обработчик будет вызвана при запросе этого URL
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True)