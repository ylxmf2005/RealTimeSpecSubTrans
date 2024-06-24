import json
import re
import difflib

class TextMatcher:
    def __init__(self, file_path="./data/lines_zh.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.text_library = json.load(f)
            
        for entry in self.text_library:
            entry['clean_text'] = self.clean_text(entry['text'])
            entry['length'] = len(entry['clean_text'])

    def clean_text(self, text):
        if not isinstance(text, str):
            text = str(text)
        return re.sub(r'[^a-zA-Z\u4e00-\u9fa5]', '', text).lower()

    def find_best_match(self, ocr_text):
        ocr_text_clean = self.clean_text(ocr_text)
        ocr_length = len(ocr_text_clean)
        best_match = None
        second_match = None
        best_match_index = None
        highest_similarity = 0
        second_highest_similarity = 0  

        for i, entry in enumerate(self.text_library):
            text_clean = entry['clean_text']
            if entry['length'] >= ocr_length:
                candidate = text_clean[:ocr_length]
            else:
                candidate = text_clean

            similarity = difflib.SequenceMatcher(None, ocr_text_clean, candidate).ratio()
            
            if similarity == 1:
                return entry['text'], i
            
            if similarity > highest_similarity:
                second_highest_similarity = highest_similarity
                second_match = best_match
                highest_similarity = similarity
                best_match = entry['text']
                best_match_index = i
            elif similarity > second_highest_similarity:
                second_highest_similarity = similarity
                second_match = entry['text']

        similarity_threshold = 0.5
        confusion_threshold = 0.05
        print(f"highest_similarity: {highest_similarity}")
        print(f"second_highest_similarity: {second_highest_similarity}")
        print(f"best match: {best_match}")
        print(f"second match: {second_match}")
        
        if highest_similarity < similarity_threshold:
            return None, None

        best_second_similarity = difflib.SequenceMatcher(None, best_match, second_match).ratio()
                
        if highest_similarity - second_highest_similarity < confusion_threshold and best_second_similarity < 0.8:
            return None, None
                    
        return best_match, best_match_index

    def find_by_path(self, path):
        synonyms = {"march_7th": "mar7th"}
        for synonym in synonyms:
            path = path.replace(synonym, synonyms[synonym])
        for i, entry in enumerate(self.text_library):
            entry_path = entry['path']
            for synonym in synonyms:
                entry_path = entry_path.replace(synonym, synonyms[synonym])
            if entry_path == path:
                return entry['text'], i
        return None, None
