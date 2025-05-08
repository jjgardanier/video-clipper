from flask import Flask, request, send_file, after_this_request, jsonify
import subprocess
import os
import uuid
import requests

app = Flask(__name__)

# Root route
@app.route('/')
def index():
    return '✅ Flask video clipper is running!'

# Clipping route
@app.route('/clip', methods=['POST'])
def clip_video():
    try:
        data = request.get_json()
        app.logger.info(f"Received data: {data}")

        # Validate input
        if not all(k in data for k in ('video_url', 'start', 'duration')):
            return jsonify({'error': 'Missing required parameters'}), 400

        video_url = data['video_url']
        start = data['start']
        duration = data['duration']

        if not duration or duration.strip() == "":
            return jsonify({'error': 'Duration must not be empty'}), 400

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

        # Build and run ffmpeg command
        command = [
            "ffmpeg", "-y", "-ss", start, "-i", input_file,
            "-t", str(duration), "-c", "copy", output_file
        ]
        app.logger.info(f"Running ffmpeg command: {' '.join(command)}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(output_file):
            error_msg = result.stderr.decode()
            app.logger.error(f"ffmpeg failed: {error_msg}")
            return jsonify({'error': 'Video clipping failed', 'ffmpeg_error': error_msg}), 500

        # Clean up files after response
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
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"🚀 Running on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
