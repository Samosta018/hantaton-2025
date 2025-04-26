from gigachat import GigaChat
from dotenv import load_dotenv
import os
import requests
from typing import List, Dict
from docx import Document
import openpyxl
import re
import json
from urllib.parse import quote

load_dotenv()

class GigaCheck:
    def __init__(self):
        self.token = os.getenv("TOKEN_GIGACHAT")
        self.giga = GigaChat(credentials=self.token, verify_ssl_certs=False)
        self.functions = {
            "short_content_gigachat": "Составь краткое описание документа. Ответ в формате: Краткое содержание: *краткое содержимое*. Ничего лишнего!", # Краткое содержание
            "check_spelling": "", # Проверка орфографии
            "check_punctuation_gigachat": "Найди в документе пунктуационные ошибки и исправь их. В ответе присылай только исправленные предложения и ничего более!", # Проверка пунктуации
        }
    
    def extract_text_from_docx(self, path_to_docx): # КОНВЕРТ ИЗ ДОК В СТРОКУ
        doc = Document(path_to_docx)
        full_text = []
        
        for para in doc.paragraphs:
            if not para.text.strip(): 
                continue

            cleaned_text = re.sub(
                r'[a-zA-Z]',
                '', 
                para.text
            )
            cleaned_text = re.sub(
                r'[^а-яА-ЯёЁ0-9\s!?.,:]',
                '', 
                cleaned_text
            )
            
            sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
            valid_sentences = [s.strip() for s in sentences if s.strip()]
            full_text.extend(valid_sentences)
        
        return ' '.join(full_text)
    
    def check_file(self, path_to_file): # ПРОВЕРКА РАСШИРЕНИЯ ФАЙЛА
        if path_to_file.endswith('.docx'):
            text = self.extract_text_from_docx(path_to_file)
            type_file = 'docx'
        # elif path_to_file.endswith('.xlsx'):
        #     text = extract_text_from_xlsx(path_to_file)
        return text, type_file

    def spell_change_to_docx(self, path_to_file, corrections):
        doc = Document(path_to_file)

        def replace_in_runs(runs, corrections):
            if not runs:
                return

            full_text = ''.join(run.text for run in runs)

            for wrong_word, correction in corrections.items():
                full_text = full_text.replace(wrong_word, correction)

            runs[0].text = full_text
            for run in runs[1:]:
                run.text = ''

        for paragraph in doc.paragraphs:
            replace_in_runs(paragraph.runs, corrections)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        replace_in_runs(paragraph.runs, corrections)

        for section in doc.sections:
            header = section.header
            footer = section.footer

            for paragraph in header.paragraphs:
                replace_in_runs(paragraph.runs, corrections)
            
            for paragraph in footer.paragraphs:
                replace_in_runs(paragraph.runs, corrections)

        doc.save(path_to_file)

    def spelling_processing(self, text, path_to_file, file_type):
        url = os.getenv("YANDEX_SPELLER_API")
        
        data = {'text': text}
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            result = response.json()
            
            if not result:
                return "Ошибок не найдено!"
            
            errors = []
            corrections = {}
            
            for item in result:
                wrong_word = item['word']
                if item['s']:
                    correction = item['s'][0]
                    errors.append(f"{wrong_word} → {correction}")
                    corrections[wrong_word] = correction
            
            if not errors:
                return "Ошибок не найдено!"
            
            if file_type == "docx":
                self.spell_change_to_docx(path_to_file, corrections)
            else:
                with open(path_to_file, 'w', encoding='utf-8') as f:
                    for wrong_word, correction in corrections.items():
                        text = text.replace(wrong_word, correction)
                    f.write(text)
            
            return "; ".join(errors)
                
        except Exception as e:
            return {"status": "error", "message": f"Непредвиденная ошибка: {str(e)}"}
    
    
    def delete_file(self, fileid: str) -> None: # УДАЛЕНИЕ ФАЙЛА ИЗ ХРАНИЛИЩА ГИГАЧАТА
        url = f"https://gigachat.devices.sberbank.ru/api/v1/files/{fileid}/delete"
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        response = requests.post(url, headers=headers, data={}, verify=False)
        return response.json()
    
    def analysis_file(self, path_to_file: str, analysis_flags: Dict[str, bool]) -> Dict[str, str]:
        results = {} 
        
        for analysis_type, should_analyze in analysis_flags.items():
            if not should_analyze:
                continue
                
            if "gigachat" in analysis_type:
                file = self.giga.upload_file(open(path_to_file, "rb"))
                fileid = file.id_
                result = self.giga.chat({
                    "messages": [
                        {
                            "role": "user",
                            "content": self.functions[analysis_type],
                            "attachments": [fileid],
                        }
                    ],
                    "temperature": 0.1
                })
                    
                results[analysis_type] = result.choices[0].message.content
                self.delete_file(fileid)
                
            elif analysis_type == "check_spelling":
                text, type_file = self.check_file(path_to_file)
                results[analysis_type] = self.spelling_processing(text, path_to_file, type_file)

        return results
    

gigacheck = GigaCheck()

