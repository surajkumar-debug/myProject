from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello Suraj! Render deployment successful 🚀"

if __name__ == "__main__":
    app.run()
