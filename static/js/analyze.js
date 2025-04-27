document.addEventListener('DOMContentLoaded', function () {
    const analyzeForm = document.querySelector('.analyze__form');
    const fileInput = document.getElementById('fileInput');
    const textInput = document.getElementById('textInput');
    const uploadArea = document.getElementById('uploadArea');
    const resultsContainer = document.getElementById('resultsContainer');
    const analyzeSubmit = document.querySelector('.analyze__submit');

    if (!analyzeForm || !fileInput || !textInput || !uploadArea || !resultsContainer || !analyzeSubmit) {
        console.error('One or more required elements are missing');
        return;
    }

    function showLoadingState() {
        resultsContainer.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Обработка документа...</p>
            </div>
        `;
    }

    function showError(message) {
        resultsContainer.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Произошла ошибка</h3>
                <p>${message}</p>
                <button class="btn btn--outline" onclick="location.reload()">Попробовать снова</button>
            </div>
        `;
    }

    function showSuccess(results, downloadUrl) {
        const showSummary = document.getElementById('summary').checked;
        const showSpelling = document.getElementById('spelling').checked;
        const showToc = document.getElementById('toc').checked;

        let resultsHTML = `
            <div class="results__content">
                <h2 class="section-title">Результаты анализа</h2>
        `;
    
        if (showSummary && results.short_content_gigachat) {
            resultsHTML += `
                <div class="result-item">
                    <h3><i class="fas fa-file-contract"></i> Краткое содержание:</h3>
                    <div class="result-content">${results.short_content_gigachat}</div>
                </div>
            `;
        }
    
        if (showToc && results.check_create_content_gigachat) {
            resultsHTML += `
                <div class="result-item">
                    <h3><i class="fas fa-file-contract"></i> Предполагаемое оглавление:</h3>
                    <div class="result-content">${results.check_create_content_gigachat}</div>
                </div>
            `;
        }
    
        if (showSpelling && results.check_spelling) {
            const spelling = results.check_spelling;
            resultsHTML += `
                <div class="result-item">
                    <h3><i class="fas fa-spell-check"></i> Проверка орфографии:</h3>
                    <div class="result-content">
                        <p>Найдено ошибок: ${spelling.error_count}</p>
                        ${spelling.error_count > 0 ? spelling.details.map(e => `
                            <div class="spelling-error">
                                <span class="error-word">${e.word}</span>
                                <i class="fas fa-arrow-right"></i>
                                <span class="suggestions">${e.suggestions.join(', ')}</span>
                            </div>
                        `).join('') : '<p>Ошибок не найдено</p>'}
                    </div>
                </div>
            `;
        }

        if (showSpelling && results.check_punctuation_gigachat) {
            resultsHTML += `
                <div class="result-item">
                    <h3><i class="fas fa-file-contract"></i> Проверка пунктуации:</h3>
                    <div class="result-content">${results.check_punctuation_gigachat}</div>
                </div>
            `;
        }

        if (downloadUrl) {
            resultsHTML += `
                <div class="result-item">
                    <h3><i class="fas fa-download"></i> Исправленный файл:</h3>
                    <a href="${downloadUrl}" class="btn btn--primary" download>
                        <i class="fas fa-download"></i> Скачать
                    </a>
                </div>
            `;
        }
    
        resultsHTML += `</div>`;
        resultsContainer.innerHTML = resultsHTML;
    }
    async function handleFormSubmit(e) {
        e.preventDefault();

        if (fileInput.files.length === 0 && textInput.value.trim() === '') {
            showError('Пожалуйста, загрузите файл или введите текст');
            return;
        }

        showLoadingState();

        const formData = new FormData();
        if (fileInput.files.length > 0) {
            formData.append('file', fileInput.files[0]);
        }
        if (textInput.value.trim() !== '') {
            formData.append('text', textInput.value.trim());
        }

        formData.append('summary', document.getElementById('summary').checked ? 'on' : 'off');
        formData.append('spelling', document.getElementById('spelling').checked ? 'on' : 'off');
        formData.append('toc', document.getElementById('toc').checked ? 'on' : 'off'); 

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            if (data.success) {
                showSuccess(data.results, data.download_url);
            } else {
                showError(data.error || 'Ошибка при анализе документа');
            }
        } catch (error) {
            showError(error.message);
            console.error('Error:', error);
        }
    }

    analyzeSubmit.addEventListener('click', handleFormSubmit);

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        uploadArea.classList.add('highlight');
    }

    function unhighlight() {
        uploadArea.classList.remove('highlight');
    }

    uploadArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length) {
            const file = files[0];
            if (!allowedFile(file.name)) {
                showError('Неподдерживаемый тип файла. Разрешены только .doc, .docx, .txt');
                return;
            }

            const fileName = file.name;
            const fileSize = (file.size / 1024 / 1024).toFixed(2);

            uploadArea.innerHTML = `
                <i class="fas fa-file-alt"></i>
                <h3 class="upload-area__title">${fileName}</h3>
                <p class="upload-area__text">${fileSize} MB</p>
                <button class="btn btn--outline change-file">
                    <i class="fas fa-sync-alt"></i> Изменить файл
                </button>
            `;

            document.querySelector('.change-file').addEventListener('click', function (e) {
                e.stopPropagation();
                resetUploadArea();
                fileInput.value = '';
            });
        }
    }

    function resetUploadArea() {
        uploadArea.innerHTML = `
            <i class="fas fa-cloud-upload-alt"></i>
            <h3 class="upload-area__title">Перетащите файл сюда</h3>
            <p class="upload-area__text">или</p>
            <label for="fileInput" class="btn btn--primary">
                <i class="fas fa-folder-open"></i> Выберите файл
            </label>
            <p class="upload-area__hint">Поддерживаются: DOC, DOCX, TXT</p>
        `;
    }

    function allowedFile(filename) {
        return filename.match(/\.(docx?|txt)$/i);
    }

    fileInput.addEventListener('change', function() {
        if (this.files.length) {
            handleFiles(this.files);
        }
    });

    console.log('Analyze script initialized successfully');
});