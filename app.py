import os
import zipfile
from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
from PIL import Image

app = Flask(__name__)

# --- CẤU HÌNH THƯ MỤC ---
# Đảm bảo đường dẫn tuyệt đối để tránh lỗi không tìm thấy file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # Lấy danh sách ảnh và sắp xếp
    images = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))])
    
    # Kiểm tra xem những ảnh nào đã làm xong
    processed_files = set(os.listdir(PROCESSED_FOLDER))

    # Tìm vị trí gợi ý (ảnh đầu tiên chưa làm)
    suggested_index = 0
    for i, filename in enumerate(images):
        if filename not in processed_files:
            suggested_index = i
            break
    
    # Nếu tất cả đã làm xong, trỏ về cuối
    if suggested_index == 0 and len(images) > 0 and images[-1] in processed_files:
         suggested_index = len(images) - 1

    return render_template('index.html', 
                           images=images, 
                           start_at=suggested_index, 
                           processed_files=list(processed_files))

@app.route('/image/<filename>')
def get_image(filename):
    # Ưu tiên lấy ảnh đã xoay (processed)
    if os.path.exists(os.path.join(PROCESSED_FOLDER, filename)):
        response = send_from_directory(PROCESSED_FOLDER, filename)
    else:
        response = send_from_directory(UPLOAD_FOLDER, filename)
    
    # Chống cache để ảnh cập nhật ngay khi xoay
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/rotate', methods=['POST'])
def rotate_image():
    try:
        data = request.json
        filename = data['filename']
        angle = int(data.get('angle', 0))

        # Xác định nguồn ảnh (ưu tiên lấy ảnh đã có trong processed để xoay tiếp)
        if os.path.exists(os.path.join(PROCESSED_FOLDER, filename)):
            source_path = os.path.join(PROCESSED_FOLDER, filename)
        else:
            source_path = os.path.join(UPLOAD_FOLDER, filename)
            
        if not os.path.exists(source_path):
             return jsonify({"status": "error", "message": "File not found"}), 404

        img = Image.open(source_path)
        
        # Xoay ảnh (expand=True để không bị cắt góc)
        rotated_img = img.rotate(-angle, expand=True)

        # Lưu đè vào folder processed
        save_path = os.path.join(PROCESSED_FOLDER, filename)
        
        # Giữ nguyên định dạng gốc hoặc mặc định JPEG
        img_format = img.format if img.format else 'JPEG'
        rotated_img.save(save_path, format=img_format)

        return jsonify({"status": "success", "message": f"Saved {filename}"})
    except Exception as e:
        print(f"Lỗi Rotate: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- API MỚI: XÓA ẢNH ---
@app.route('/delete', methods=['POST'])
def delete_image():
    try:
        data = request.json
        filename = data['filename']
        
        # Xóa ở cả 2 thư mục (Gốc và Đã xử lý)
        path_upload = os.path.join(UPLOAD_FOLDER, filename)
        path_processed = os.path.join(PROCESSED_FOLDER, filename)
        
        deleted = False
        
        if os.path.exists(path_upload):
            os.remove(path_upload)
            deleted = True
            
        if os.path.exists(path_processed):
            os.remove(path_processed)
            deleted = True
            
        if deleted:
            return jsonify({"status": "success", "message": f"Deleted {filename}"})
        else:
            return jsonify({"status": "error", "message": "File not found"}), 404
            
    except Exception as e:
        print(f"Lỗi Delete: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/download-all')
def download_all():
    zip_filename = "rotated_images.zip"
    zip_path = os.path.join(BASE_DIR, zip_filename)
    
    # Tạo file zip mới
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Chỉ zip những file trong folder processed
        if not os.path.exists(PROCESSED_FOLDER):
             return "Chưa có ảnh nào được xử lý", 404
             
        files_to_zip = os.listdir(PROCESSED_FOLDER)
        if not files_to_zip:
             return "Folder processed rỗng", 404

        for file in files_to_zip:
            file_path = os.path.join(PROCESSED_FOLDER, file)
            zipf.write(file_path, file)
            
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
