document.addEventListener('DOMContentLoaded', function() {
    // Бургер меню
    const burger = document.getElementById('burger');
    const nav = document.querySelector('.nav');
    const headerAuth = document.querySelector('.header__auth');
    
    burger.addEventListener('click', function() {
        nav.classList.toggle('active');
        headerAuth.classList.toggle('active');
        burger.classList.toggle('active');
    });
    
    // Drag and drop для загрузки файлов
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
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
        handleFiles(files);
    }
    
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    function handleFiles(files) {
        if (files.length) {
            const file = files[0];
            const fileName = file.name;
            const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
            
            uploadArea.innerHTML = `
                <i class="fas fa-file-alt"></i>
                <h3 class="upload-area__title">${fileName}</h3>
                <p class="upload-area__text">${fileSize} MB</p>
                <button class="btn btn--outline change-file">
                    <i class="fas fa-sync-alt"></i> Изменить файл
                </button>
            `;
            
            document.querySelector('.change-file').addEventListener('click', function(e) {
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
            <p class="upload-area__hint">Поддерживаются: DOC, DOCX, XLS, XLSX, TXT</p>
        `;
        
        uploadArea.addEventListener('click', function() {
            fileInput.click();
        });
    }
    
    // Анимация при скролле
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.feature-card, .analyze__form, .results__placeholder');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.3;
            
            if (elementPosition < screenPosition) {
                element.classList.add('animated');
            }
        });
    };
    
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Инициализация при загрузке
});