from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Calculator App 🚀</h1>

    <p>Examples:</p>

    <ul>
        <li>/add?a=10&b=20</li>
        <li>/sub?a=50&b=15</li>
        <li>/mul?a=5&b=8</li>
        <li>/div?a=100&b=4</li>
    </ul>
    """

@app.route("/add")
def add():
    a = float(request.args.get("a", 0))
    b = float(request.args.get("b", 0))
    return {"operation": "addition", "result": a + b}

@app.route("/sub")
def sub():
    a = float(request.args.get("a", 0))
    b = float(request.args.get("b", 0))
    return {"operation": "subtraction", "result": a - b}

@app.route("/mul")
def mul():
    a = float(request.args.get("a", 0))
    b = float(request.args.get("b", 0))
    return {"operation": "multiplication", "result": a * b}

@app.route("/div")
def div():
    a = float(request.args.get("a", 0))
    b = float(request.args.get("b", 1))
    return {"operation": "division", "result": a / b}

if __name__ == "__main__":
    app.run()