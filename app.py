import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
import logging
from service.main import gigacheck

app = Flask(__name__)

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed_files'
ALLOWED_EXTENSIONS = {'docx', 'xslx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Создаем папки, если их нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Проверяем наличие файла или текста
        if 'file' not in request.files and 'text' not in request.form:
            logger.error("No file or text provided in request")
            return jsonify({'success': False, 'error': 'No file or text provided'}), 400

        # Обработка файла, если он есть
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                logger.error("No selected file")
                return jsonify({'success': False, 'error': 'No selected file'}), 400
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                logger.info(f"File saved to: {file_path}")
            else:
                logger.error(f"File type not allowed: {file.filename}")
                return jsonify({'success': False, 'error': 'File type not allowed'}), 400

        # Обработка текста, если он есть
        elif 'text' in request.form and request.form['text'].strip():
            text = request.form['text'].strip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"text_input_{timestamp}.txt"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Text saved to file: {file_path}")

        # Получаем флаги анализа
        analysis_flags = {
            "short_content_gigachat": 'summary' in request.form,
            "check_spelling": 'spelling' in request.form,
            "check_punctuation_gigachat": 'spelling' in request.form,
            "check_create_content_gigachat": 'toc' in request.form,
        }

        if not any(analysis_flags.values()):
            logger.error("No analysis options selected")
            return jsonify({'success': False, 'error': 'No analysis options selected'}), 400

        # Выполняем анализ
        try:
            logger.info(f"Starting analysis for file: {file_path}")
            results = gigacheck.analysis_file(file_path, analysis_flags)
            logger.info(f"Analysis completed. Results: {results}")

            # Генерируем имя для обработанного файла
            processed_filename = f"processed_{os.path.basename(file_path)}"
            processed_filepath = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)

            # Копируем файл в папку processed_files (или обрабатываем его)
            import shutil
            shutil.copy2(file_path, processed_filepath)
            logger.info(f"Processed file saved to: {processed_filepath}")

            # Формируем URL для скачивания
            download_url = f"/download/{processed_filename}"

            # Форматируем результаты для ответа
            formatted_results = {
                'short_content_gigachat': results.get('short_content_gigachat', ''),
                'check_create_content_gigachat': results.get('check_create_content_gigachat', ''),
                'check_punctuation_gigachat': results.get('check_punctuation_gigachat', ''),
                'check_spelling': {
                    'error_count': len(results.get('check_spelling', '').split('; ')) if results.get('check_spelling') else 0,
                    'details': [
                        {'word': e.split(' → ')[0], 'suggestions': [e.split(' → ')[1]]} 
                        for e in results.get('check_spelling', '').split('; ') 
                        if ' → ' in e
                    ]
                } if results.get('check_spelling') else {'error_count': 0, 'details': []}
            }
            return jsonify({
                'success': True,
                'results': formatted_results,
                'download_url': download_url
            })

        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        logger.info(f"Download requested for file: {filename}")
        return send_from_directory(
            app.config['PROCESSED_FOLDER'],
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)