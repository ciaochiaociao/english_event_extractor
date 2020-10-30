#!/usr/bin/python3
import json
from pathlib import Path
from flask import Flask, request

from .main import EventExtractor
from .event import Event

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello, this is an English Event Extractor API! Please access the url with <ip:port>/event?text=<text>\n"


@app.route('/event', methods=['GET'])
def get_event():

    text = request.args.get('text')
    
    temp_dir = Path('temp')
    temp_dir.mkdir(exist_ok=True)
    
    temp_id = 99999
    
    with (temp_dir/str(temp_id)).open(mode='w') as f:
        f.write(text)
        
    doc_id_dict = {temp_id: 'temp'}

    events = EventExtractor.extract(doc_id_dict)
    events_dict = Event.to_multidoc_dict(events)
    result = {
        'corefs': {},
        'events': events_dict
    }
    result = {'text': text, 'result': result}

    return json.dumps(result, ensure_ascii=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
