import docx
import os

def load_keywords(txt_path):
    """
    从本地加载特征词典并进行数据清洗 (去除空行与空白符)
    """
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()] 
    except FileNotFoundError:
        print(f"⚠️ 未找到词典文件: {txt_path}")
        return []

# 使用相对路径，确保工程可移植性
# 规范要求：在主程序目录下建立 data 文件夹
txt_path = "./data/keywords.txt"
ZHAO_FEATURES = load_keywords(txt_path)

def get_zhaomai_fragments(file_path):
    """
    解析源文档，抽离非结构化文本，并基于词典标记特征片段
    """
    try:
        doc = docx.Document(file_path) 
    except Exception as e:
        print(f"❌ 读取文档失败: {e}")
        return []

    fragments = []

    for p in doc.paragraphs: 
        text = p.text.strip()
        if not text:
            continue

        # 特征提取：匹配段落内有效的高敏感情绪词
        matched_words = [w for w in ZHAO_FEATURES if w in text] 

        fragments.append({
            "text": text,
            "words": matched_words
        })                                          

    return fragments
