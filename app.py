from flask import Flask, request, send_file, after_this_request, jsonify
import subprocess
import os
import uuid
import requests

app = Flask(__name__)

# Root route to avoid 404 on /
@app.route('/')
def index():
    return '✅ Flask video clipper is running!'

# Video clipping endpoint
@app.route('/clip', methods=['POST'])
def clip_video():
    try:
        data = request.get_json()

        # Validate input
        if not all(k in data for k in ('video_url', 'start', 'duration')):
            return jsonify({'error': 'Missing required parameters'}), 400

        video_url = data['video_url']
        start = data['start']
        duration = data['duration']

        input_file = f"input_{uuid.uuid4()}.mp4"
        output_file = f"clip_{uuid.uuid4()}.mp4"

        # Download video
        r = requests.get(video_url, stream=True)
        if r.status_code != 200:
            return jsonify({'error': 'Failed to download video'}), 400

        with open(input_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Run ffmpeg to clip video
        command = [
            "ffmpeg", "-y", "-ss", start, "-i", input_file,
            "-t", str(duration), "-c", "copy", output_file
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        @after_this_request
        def cleanup(response):
            try:
                os.remove(input_file)
                os.remove(output_file)
            except Exception as e:
                app.logger.error(f"Error deleting temp files: {e}")
            return response

        return send_file(output_file, mimetype='video/mp4')

    except Exception as e:
        app.logger.error(f"Unhandled exception: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))  # fallback to 5050 instead of 5000
    print(f"🚀 Running on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)



