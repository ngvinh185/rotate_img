import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image
import shutil

app = Flask(__name__)

# --- CẤU HÌNH THƯ MỤC ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
LABELED_FOLDER = os.path.join(BASE_DIR, 'labeled')

# Danh sách nhãn theo yêu cầu
LABELS = ["Person", "Cat", "Dog", "Car", "Motorcycle", "Aircraft", "Flower", "Fruit"]

# Khởi tạo cấu trúc thư mục
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
for label in LABELS:
    os.makedirs(os.path.join(LABELED_FOLDER, label), exist_ok=True)

@app.route('/')
def index():
    # Lấy danh sách ảnh gốc chưa xử lý
    all_images = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    # Kiểm tra xem ảnh nào đã được gán nhãn (có tồn tại trong bất kỳ sub-folder nào của labeled)
    processed_files = []
    for label in LABELS:
        processed_files.extend(os.listdir(os.path.join(LABELED_FOLDER, label)))
    
    processed_set = set(processed_files)
    
    # Tìm vị trí ảnh đầu tiên chưa làm
    suggested_index = 0
    for i, filename in enumerate(all_images):
        if filename not in processed_set:
            suggested_index = i
            break

    return render_template('index.html', 
                           images=all_images, 
                           labels=LABELS, 
                           start_at=suggested_index,
                           processed_files=list(processed_set))

@app.route('/image/<filename>')
def get_image(filename):
    # Luôn lấy từ uploads vì khi gán nhãn xong ta di chuyển/copy đi chỗ khác
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/save_label', methods=['POST'])
def save_label():
    try:
        data = request.json
        filename = data['filename']
        label = data['label']
        crop_box = data.get('crop_box') # {x, y, width, height}

        src_path = os.path.join(UPLOAD_FOLDER, filename)
        dst_path = os.path.join(LABELED_FOLDER, label, filename)

        if not os.path.exists(src_path):
            return jsonify({"status": "error", "message": "File không tồn tại"}), 404

        if crop_box:
            # Chức năng cắt ảnh
            with Image.open(src_path) as img:
                # Tính toán tọa độ cắt
                left = crop_box['x']
                top = crop_box['y']
                right = left + crop_box['width']
                bottom = top + crop_box['height']
                
                # Cắt và lưu
                cropped_img = img.crop((left, top, right, bottom))
                cropped_img.save(dst_path)
        else:
            # Nếu không cắt thì copy/move nguyên bản
            shutil.copy2(src_path, dst_path)

        return jsonify({"status": "success", "label": label})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
