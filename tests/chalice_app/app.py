import chalice

app = chalice.Chalice(app_name="chalice_app")


@app.route("/")
def index():
    return {"hello": "world"}
