from sanic import Sanic
from sanic import Blueprint, response
from sanic.response import text

app = Sanic("MyHelloWorldApp")

@app.get("/")
async def hello_world(request):
    return text("00002 Hello, world.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)