import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.get_json() or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'Please provide a valid URL.'}), 400

    # Modern client player spoofing to bypass YouTube bot detection on cloud IPs
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web_creator']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            raw_formats = info.get('formats', [])
            extracted_formats = []
            seen_resolutions = set()

            for f in reversed(raw_formats):
                download_url = f.get('url')
                if not download_url:
                    continue

                ext = f.get('ext', 'mp4')
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                height = f.get('height')
                
                if height:
                    res_label = f"{height}p"
                elif vcodec == 'none' and acodec != 'none':
                    res_label = "Audio Only"
                else:
                    res_label = f.get('format_note') or "SD"

                combo_key = f"{res_label}-{ext}"
                if combo_key in seen_resolutions:
                    continue
                seen_resolutions.add(combo_key)

                extracted_formats.append({
                    'format_id': f.get('format_id'),
                    'ext': ext,
                    'resolution': res_label,
                    'has_video': vcodec != 'none',
                    'has_audio': acodec != 'none',
                    'download_url': download_url,
                })

            return jsonify({
                'title': info.get('title', 'YouTube Video'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration_string', ''),
                'formats': extracted_formats
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

