from flask import Flask, request, send_file
import subprocess
import os
import uuid
import requests

app = Flask(__name__)

@app.route('/clip', methods=['POST'])
def clip_video():
    data = request.json
    video_url = data['video_url']
    start = data['start']
    duration = data['duration']

    input_file = f"input_{uuid.uuid4()}.mp4"
    output_file = f"clip_{uuid.uuid4()}.mp4"

    r = requests.get(video_url)
    with open(input_file, 'wb') as f:
        f.write(r.content)

    command = [
        "ffmpeg", "-ss", start, "-i", input_file,
        "-t", str(duration), "-c", "copy", output_file
    ]
    subprocess.run(command)

    return send_file(output_file, mimetype='video/mp4')

if __name__ == '__main__':
    app.run(debug=True)
