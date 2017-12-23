from webserver.devices import devices_blueprint
from webserver.scheduler import scheduler_blueprint
from flask import Flask
from jinja2 import Environment, PackageLoader, select_autoescape

app = Flask(__name__)
app.register_blueprint(devices_blueprint, url_prefix='/devices')
app.register_blueprint(scheduler_blueprint, url_prefix='/scheduler')

env = Environment(
    loader=PackageLoader('webserver', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

@app.route("/")
def index():
    template = env.get_template("index.html")
    return template.render()


app.secret_key = b'\x1a\x03QU\x99\xbc\x92W\x8b\xf3}\xfa o3\xc0\xa1\xd9\xe3\x07;\x1a\x84{'
