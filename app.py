import os, time, json
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image

app = Flask(__name__)

# --- CẤU HÌNH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
LABELED_FOLDER = os.path.join(BASE_DIR, 'labeled')
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')
LABELS = ["Person", "Cat", "Dog", "Car", "Motorcycle", "Aircraft", "Flower", "Fruit"]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
for label in LABELS:
    os.makedirs(os.path.join(LABELED_FOLDER, label), exist_ok=True)

def get_last_progress():
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f: 
                data = json.load(f)
                return int(data.get('last_index', 0))
    except: return 0
    return 0

@app.route('/')
def index():
    images = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    # Đảm bảo index không vượt quá giới hạn
    idx = get_last_progress()
    if idx >= len(images): idx = 0
    return render_template('index.html', images=images, labels=LABELS, last_index=idx)

@app.route('/image/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/save_all_and_next', methods=['POST'])
def save_all_and_next():
    try:
        data = request.json
        filename = data['filename']
        items = data['items'] 
        next_index = data['next_index']

        # Lưu vị trí mới vào file
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({'last_index': int(next_index)}, f)

        if items:
            src_path = os.path.join(UPLOAD_FOLDER, filename)
            with Image.open(src_path) as img:
                for item in items:
                    label = item['label']
                    timestamp = int(time.time() * 1000)
                    new_filename = f"{label}_{timestamp}_{filename}"
                    dst_path = os.path.join(LABELED_FOLDER, label, new_filename)
                    
                    # Cắt ảnh
                    crop = img.crop((item['x'], item['y'], item['x']+item['width'], item['y']+item['height']))
                    if crop.mode in ("RGBA", "P"): crop = crop.convert("RGB")
                    crop.save(dst_path, quality=95)

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/update_progress', methods=['POST'])
def update_progress():
    # API này dùng khi bấm nút Back/Next mà không lưu
    data = request.json
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'last_index': int(data['index'])}, f)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
