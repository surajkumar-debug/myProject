from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def calculator():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Calculator</title>
        <style>
            body{
                font-family: Arial;
                text-align:center;
                margin-top:100px;
                background:#f5f5f5;
            }

            .box{
                background:white;
                width:350px;
                margin:auto;
                padding:20px;
                border-radius:10px;
                box-shadow:0 0 10px rgba(0,0,0,0.2);
            }

            input{
                width:90%;
                padding:10px;
                margin:10px;
                font-size:18px;
            }

            button{
                padding:10px 20px;
                margin:5px;
                font-size:18px;
                cursor:pointer;
            }
        </style>

        <script>
            function calculate(op){

                let a = document.getElementById("num1").value;
                let b = document.getElementById("num2").value;

                fetch(`/calculate?a=${a}&b=${b}&op=${op}`)
                .then(res => res.json())
                .then(data => {
                    document.getElementById("result").innerHTML =
                    "Result = " + data.result;
                });
            }
        </script>
    </head>

    <body>

        <div class="box">
            <h1>🚀 Suraj Calculator</h1>

            <input id="num1" type="number" placeholder="First Number">

            <input id="num2" type="number" placeholder="Second Number">

            <br>

            <button onclick="calculate('add')">+</button>

            <button onclick="calculate('sub')">-</button>

            <button onclick="calculate('mul')">*</button>

            <button onclick="calculate('div')">/</button>

            <h2 id="result"></h2>

        </div>

    </body>
    </html>
    """

@app.route("/calculate")
def calculate():

    a = float(request.args.get("a",0))
    b = float(request.args.get("b",0))
    op = request.args.get("op")

    if op=="add":
        result = a+b

    elif op=="sub":
        result = a-b

    elif op=="mul":
        result = a*b

    elif op=="div":
        result = a/b if b!=0 else "Cannot divide by zero"

    else:
        result = "Invalid Operation"

    return {"result":result}

if __name__ == "__main__":
    app.run()