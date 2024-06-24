import pandas as pd
import json
from text_matcher import TextMatcher
import pickle

def xlsx2json(file_path):
    xls = pd.ExcelFile(file_path)

    all_characters = []

    nick_name = "开拓者"

    for sheet_name in xls.sheet_names:
        if sheet_name != "总览数据":
            df = pd.read_excel(xls, sheet_name=sheet_name)
            for _, row in df.iterrows():
                character_entry = {
                    "name": sheet_name,
                    "path": row["原始路径"],
                    "audio_path": row["语音文件"],
                    "text": row["文本"],
                }
                all_characters.append(character_entry)

    json_data = json.dumps(all_characters, ensure_ascii=False, indent=4)

    if "en" in file_path:
        output_path = './data/lines_en.json'
    elif "zh" in file_path:
        output_path = './data/lines_zh.json'
        
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json_file.write(json_data)
        
        
xlsx2json(file_path="./data/lines_zh.xlsx")
xlsx2json(file_path="./data/lines_en.xlsx")
    