from flask import Flask, render_template, request, jsonify, send_file
import os
from tempfile import mkdtemp
from werkzeug.utils import secure_filename
from io import BytesIO
from service.main import GigaCheck

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')
app.config['UPLOAD_FOLDER'] = mkdtemp()
ALLOWED_EXTENSIONS = {'doc', 'docx', 'txt'}

gigacheck = GigaCheck()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files and 'text' not in request.form:
            return jsonify(success=False, error='Необходимо загрузить файл или ввести текст'), 400

        file_path = None
        original_filename = None
        is_txt = False

        # Обработка файла
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify(success=False, error='Файл не выбран'), 400
            
            if not allowed_file(file.filename):
                return jsonify(success=False, error='Неподдерживаемый формат файла'), 400

            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            file_path = f"/uploads/{original_filename}"
            file.save(file_path)

        # Обработка текста
        elif 'text' in request.form:
            text = request.form['text'].strip()
            if not text:
                return jsonify(success=False, error='Текст не может быть пустым'), 400
            
            original_filename = 'text_input.txt'
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            is_txt = True

        # Определение параметров анализа
        analysis_flags = {
            "short_content_gigachat": request.form.get('summary') == 'on',
            "check_spelling": request.form.get('spelling') == 'on'
        }

        # Выполнение анализа и модификация файла
        results = gigacheck.analysis_file(file_path, analysis_flags)
        
        # Подготовка ответа
        response = {
            'success': True,
            'results': {
                'short_content_gigachat': results.get('short_content_gigachat', ''),
                'check_spelling': {
                    'error_count': len(results.get('check_spelling', '').split('; ')) if results.get('check_spelling') else 0,
                    'details': [{'word': e.split(' → ')[0], 'suggestions': [e.split(' → ')[1]]} 
                              for e in results.get('check_spelling', '').split('; ') if ' → ' in e]
                }
            }
        }

        return jsonify(response)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500
    finally:
        # Удаление временного файла после отправки
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)