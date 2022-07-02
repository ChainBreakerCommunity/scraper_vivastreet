from flask import Flask, jsonify, request, make_response
from flask.helpers import send_from_directory
from flask_cors import CORS
import bot.bot 
from utils.env import get_config
config = get_config()

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Main page.
@app.route('/')
def root():
    """
    Return the frontend of the application.
    """
    return send_from_directory("./static", 'index.html')

@app.route('/api/execute_scraper', methods = ["GET"])
def execute_scraper():
    bot.bot.execute_scraper()
    return jsonify({"message": "bot executed"}), 200

if __name__ == '__main__':
    app.run(port = config["PORT"], debug = bool(config["DEBUG"]))