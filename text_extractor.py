import docx

def load_keywords(txt_path):
    """从txt加载关键词，并过滤掉空行"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()] # 移除头尾的空格
# 原材料：f（文件里的每一行）。

# 加工动作：line.strip()（去掉每一行前后的空格或换行符）。

# 筛选条件：if line.strip()（只有处理后不是空行的，才留下来）。

# 成品柜：最外层的 []，把所有加工好的合格品装进一个列表里返回。

    except FileNotFoundError:   # 没找到文件
        return []

# 1. 动态加载关键词
# 确保你的 keywords.txt 文件和这个 py 文件在同一个目录下
txt_path = "C:/My_profiles/sophomore_spring/emotion_analyze/keywords.txt"
ZHAO_FEATURES = load_keywords(txt_path)

import os
print(f"当前工作目录: {os.getcwd()}")
print(f"关键词库内容: {ZHAO_FEATURES}") # 如果这里打印出 []，说明 keywords.txt 没读到

def get_zhaomai_fragments(file_path):
    try:
        doc = docx.Document(file_path)  # docx.Document('gfg.docx'): Opens an existing Word document named gfg.docx.
    except Exception as e:
        print(f"❌ 读取Word文档失败: {e}")
        return []

    fragments = []

    for p in doc.paragraphs:     # returns a list of all paragraph objects within a Word document
        text = p.text.strip()
        if not text:        # 跳过空行
            continue

        # 核心逻辑：从当前段落中提取出所有命中的特征词
        matched_words = [w for w in ZHAO_FEATURES if w in text]  # w在 ZHAO_FEATURES 且在 text

        # 只要这一段有关键词，就记录下来
        # 即使没有关键词，如果你想保持色彩的“连续性”，也可以选择记录
        # 但目前我们只记录有“情绪波动”的段落

        fragments.append({
            "text": text,
            "words": matched_words
        })                                      # 如果没有关键词，可以降低情绪波动 改！！！

    return fragments