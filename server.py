from flask import Flask, send_from_directory, request

app = Flask(__name__, static_folder='site', static_url_path='')


@app.route('/')
def index():
    return send_from_directory('site', 'index.html')


@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    print(f"Received: container {data['container_oc']}, condition: {data['condition']}")
    return '', 204


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
