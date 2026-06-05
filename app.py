from flask import Flask, render_template, request, jsonify
import requests
from deep_translator import GoogleTranslator
import time

app = Flask(__name__)

import os
APIFY_API_KEY = os.environ.get("APIFY_API_KEY", "")

def get_instagram_comments(post_url):
    url = "https://api.apify.com/v2/acts/apify~instagram-comment-scraper/runs"
    headers = {
        "Authorization": f"Bearer {APIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "directUrls": [post_url],
        "resultsLimit": 200
    }
    
    response = requests.post(url, json=payload, headers=headers)
    run_data = response.json()
    run_id = run_data["data"]["id"]
    
    # صبر کن تا تموم بشه
    while True:
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        status_res = requests.get(status_url, headers=headers)
        status = status_res.json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        time.sleep(3)
    
    # گرفتن نتایج
    dataset_id = status_res.json()["data"]["defaultDatasetId"]
    results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    results = requests.get(results_url, headers=headers)
    return results.json()

def translate_text(text):
    try:
        if not text or len(text.strip()) == 0:
            return text
        translated = GoogleTranslator(source='sq', target='fa').translate(text)
        return translated
    except:
        return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    post_url = data.get('url')
    
    comments = get_instagram_comments(post_url)
    results = []
    
    for comment in comments:
        original = comment.get('text', '')
        translated = translate_text(original)
        results.append({
            'username': comment.get('ownerUsername', 'Unknown'),
            'original': original,
            'translated': translated
        })
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
