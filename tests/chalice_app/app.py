from chalice import Chalice

app = Chalice(app_name="chalice_app")


@app.route("/")
def index():
    return {"hello": "world"}
