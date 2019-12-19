import flask
app = flask.Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return "Hello, World"
