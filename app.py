import os
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
# from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from urllib.parse import quote, unquote

app = Flask(__name__)

# 为 CSRF 保护设置一个密钥。这应该是一个复杂的、保密的值。
# 在生产环境中，建议从环境变量或配置文件中加载。
app.config['SECRET_KEY'] = 'opm2zOLF/IQu5bf6Yy7t+zQKD5DcJ1YF'
csrf = CSRFProtect(app)

# 配置文件夹路径
TEXT_FOLDER = 'saved_texts'
UPLOAD_FOLDER = 'uploaded_files'
DOWNLAOD_FOLDER = 'downloads'

# 如果文件夹不存在，则创建
os.makedirs(TEXT_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLAOD_FOLDER, exist_ok=True)

# 设置上传文件夹和允许的文件类型
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页：包含文本保存和文件上传的表单"""
    return render_template('index.html')

@app.route('/sign')
def sign():
    """签名页：用 metamssk 钱包给相关消息签名"""
    return render_template('sign.html')

@app.route('/save-text', methods=['POST'])
@csrf.exempt # 对于 AJAX 请求，我们手动处理，所以暂时排除 CSRF 检查
def save_text():
    """处理文本保存请求"""
    data = request.json
    text_to_save = data.get('text', '')
    
    if not text_to_save:
        return jsonify({'status': 'error', 'message': '文本内容不能为空。'}), 400
    
    file_path = os.path.join(TEXT_FOLDER, 'output.txt')
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(text_to_save + '\n')
        return jsonify({'status': 'success', 'message': '文本已成功保存。'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'保存失败: {e}'}), 500

@app.route('/upload-file', methods=['POST'])
@csrf.exempt # 对于 AJAX 请求，我们手动处理，所以暂时排除 CSRF 检查
def upload_file():
    """处理文件上传请求，支持中文文件名"""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有文件部分。'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件。'}), 400
    
    # 获取原始文件名
    original_filename = file.filename

    # if file and allowed_file(original_filename):
    if file:
        # 对文件名进行 URL 编码，以保证文件系统安全
        encoded_filename = quote(original_filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], encoded_filename)
        
        # 检查文件是否已存在，避免覆盖
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_filename)
            encoded_filename = quote(f"{name}_{counter}{ext}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], encoded_filename)
            counter += 1

        file.save(file_path)
        return jsonify({'status': 'success', 'message': f'文件 {original_filename} 上传成功。'})
    else:
        return jsonify({'status': 'error', 'message': '不允许的文件类型。'}), 400

@app.route('/files')
def list_files():
    """文件浏览页：显示所有已保存的文本和上传文件"""
    saved_texts_encoded = os.listdir(TEXT_FOLDER)    
    saved_texts_decoded = [unquote(filename) for filename in saved_texts_encoded]    
    uploaded_files_encoded = os.listdir(UPLOAD_FOLDER)
    uploaded_files_decoded = [unquote(filename) for filename in uploaded_files_encoded]
    download_files_encoded = os.listdir(DOWNLAOD_FOLDER)
    download_files_decoded = [unquote(filename) for filename in download_files_encoded]
    return render_template('files.html', 
                           saved_texts=zip(saved_texts_encoded, saved_texts_decoded),
                           uploaded_files=zip(uploaded_files_encoded, uploaded_files_decoded),
                           download_files=zip(download_files_encoded, download_files_decoded))                                                     

@app.route('/files/<filename>')
def serve_file(filename):
    """提供文件预览功能"""
    # decoded_filename = unquote(filename)    
    # 优先在上传文件夹中查找
    if filename in os.listdir(UPLOAD_FOLDER):
        return send_from_directory(UPLOAD_FOLDER, filename)
    # 其次在文本文件夹中查找
    elif filename in os.listdir(TEXT_FOLDER):
        return send_from_directory(TEXT_FOLDER, filename)
    else:
        return "File not found.", 404
    
@app.route('/download/<filename>')
def download_file(filename):
    """
    提供文件下载功能。    
    """
    # 对文件名进行 URL 解码
    # decoded_filename = unquote(filename)
    # if filename in os.listdir(DOWNLAOD_FOLDER):
    if True:
        # 从文本文件夹下载
        return send_from_directory(DOWNLAOD_FOLDER, filename, as_attachment=True)    
    else:
        return "File not found.", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)