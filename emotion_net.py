import jieba.analyse
import math

# ==========================================
# 📍 情节锚点 (Plot Anchors)
# 用于将长文本自动切分为 10 个“中网”章节。
# ==========================================
PLOT_ANCHORS = {
    1: ["海浪", "礁石", "泡沫", "滨海路"],
    2: ["客栈", "篝火", "木柴", "酒精", "老板"],
    3: ["最炫民族风", "衣袖", "老人们"],
    4: ["秋之提亚娜", "tiara", "王冠", "口红", "公主", "紫罗兰色", "银杏树叶"],
    5: ["哲学家", "灯塔", "棕色大衣", "马拉松", "过期橘子", "霉菌"],
    6: ["画", "额头", "巫师", "甘油", "小女孩", "纽扣"],
    7: ["心跳声", "海浪拍打", "呼吸", "万米之下", "焦黑的木块", "世界"],
    8: ["沉默", "天气预报", "上班", "早间新闻", "Nike运动鞋", "跨海大桥",
        "绿皮火车", "威士忌", "0和1", "真空", "代码", "黏糊糊", "泥泞"],
    9: ["睡觉", "拧绞", "闹钟", "凉水澡"],
    10: ["满脸冷汗", "3：46", "金字塔", "柴火", "理查德", "螺丝松掉",
         "旧粮仓", "特斯拉", "朝霞", "狡猾", "左转"]
}

class ThreeLevelEmotionNet:
    """
    🧠 三级嵌套特征融合网络 (Three-Level Emotion Net)
    负责文本的情感织网、多层特征提取，以及基于计算叙事学的“张力（期望偏差）”建模。
    """

    def __init__(self, fragments, engine):
        self.engine = engine
        self.processed_fragments = self._partition_fragments(fragments)
        
        # 1. 构建大网：提取全书宿命底色
        self.global_base = self._build_global_net()
        
        # 2. 构建中网：提取每个章节的环境氛围
        self.middle_nets = {}
        self._build_middle_nets()

        # 🔥 3. 宏观张力预计算：在初始化时，直接把全书的“剧本心电图”算好并存储
        self.macro_tensions = self._build_macro_tensions()

    def _partition_fragments(self, raw_fragments):
        """根据锚点词，将零散的文本片段映射到对应的章节 ID"""
        current_section = 1
        processed = []
        for f in raw_fragments:
            text = f["text"]
            for sec_id, anchors in PLOT_ANCHORS.items():
                if any(anchor in text for anchor in anchors) and sec_id >= current_section:
                    current_section = sec_id
                    break
            f["section_id"] = current_section
            processed.append(f)
        return processed

    def _build_global_net(self):
        """大网计算：扫描全书，提取 Top50 核心意象，融合出全书的基准 RGB（宿命底色）"""
        all_text = "".join([f["text"] for f in self.processed_fragments])
        keywords = jieba.analyse.extract_tags(all_text, topK=50)
        matched_colors = [self.engine.color_db[w] for w in keywords if w in self.engine.color_db]
        if matched_colors:
            avg_r = sum(c[0] for c in matched_colors) // len(matched_colors)
            avg_g = sum(c[1] for c in matched_colors) // len(matched_colors)
            avg_b = sum(c[2] for c in matched_colors) // len(matched_colors)
            return [avg_r, avg_g, avg_b]
        return [112, 128, 144] # 默认冷灰蓝色

    def _build_middle_nets(self):
        """中网计算：提取各个章节的局部背景色，并与大网底色进行 7:3 加权融合"""
        section_texts = {i: "" for i in range(1, 11)}
        for f in self.processed_fragments:
            sid = f["section_id"]
            if sid in section_texts:
                section_texts[sid] += f["text"]

        for sid, text in section_texts.items():
            if not text:
                self.middle_nets[sid] = self.global_base
                continue

            keywords = jieba.analyse.extract_tags(text, topK=10)
            matched_colors = [self.engine.color_db[w] for w in keywords if w in self.engine.color_db]

            if matched_colors:
                local_r = sum(c[0] for c in matched_colors) // len(matched_colors)
                local_g = sum(c[1] for c in matched_colors) // len(matched_colors)
                local_b = sum(c[2] for c in matched_colors) // len(matched_colors)

                core_weight = 0.3  # 30% 宿命底色牵制
                local_weight = 0.7 # 70% 当前章节氛围主导

                final_r = int((self.global_base[0] * core_weight) + (local_r * local_weight))
                final_g = int((self.global_base[1] * core_weight) + (local_g * local_weight))
                final_b = int((self.global_base[2] * core_weight) + (local_b * local_weight))
                self.middle_nets[sid] = [final_r, final_g, final_b]
            else:
                self.middle_nets[sid] = self.global_base

    def _build_macro_tensions(self):
        """
        🔥 核心算法：双重引力宏观张力计算 (Dual-Gravity Macro Tension)
        基于色彩空间的欧几里得距离，量化文学作品的宏观“期望偏差”。
        """
        tensions = []
        middle_colors = [self.get_middle_net_color(i) for i in range(1, 11)]

        # 权重分配：70% 受上一章剧情惯性影响，30% 受全书宿命底色影响
        w_past = 0.7
        w_fate = 0.3

        for i in range(len(middle_colors)):
            c_current = middle_colors[i]

            # 1. 宿命张力 (Fate Tension)：当前环境偏离全书主旨的距离
            dist_fate = math.sqrt(sum((a - b) ** 2 for a, b in zip(c_current, self.global_base)))

            # 2. 剧情张力 (Past Tension)：当前环境与上一章的反差程度
            if i == 0:
                # 第一章的“过去”即为这个世界的初始状态（大网），保持数学对称
                dist_past = dist_fate
            else:
                c_prev = middle_colors[i - 1]
                dist_past = math.sqrt(sum((a - b) ** 2 for a, b in zip(c_current, c_prev)))

            # 3. 加权融合：得出最终的宏观叙事偏差值
            final_tension = (dist_past * w_past) + (dist_fate * w_fate)
            tensions.append(final_tension)

        return tensions

    # ================= 供外部渲染调用的 API 接口 =================

    def get_global_net_color(self):
        return self.global_base

    def get_middle_net_color(self, section_id):
        return self.middle_nets.get(section_id, self.global_base)

    def get_small_net_color(self, words):
        """将当前文本句子转化为基础 RGB 颜色"""
        hex_color = self.engine.update(words)
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
        return rgb

    def get_fused_small_color(self, words, current_mid_color):
        """小网融合：将当前动作颜色与场景中网颜色以 8:2 融合，得到最终画笔颜色"""
        raw_small = self.get_small_net_color(words)
        s_w, m_w = 0.8, 0.2
        fused_color = [
            int(current_mid_color[0] * m_w + raw_small[0] * s_w),
            int(current_mid_color[1] * m_w + raw_small[1] * s_w),
            int(current_mid_color[2] * m_w + raw_small[2] * s_w)
        ]
        return fused_color

    def get_micro_tension(self, small_color, mid_color):
        """
        🔥 核心逻辑：计算微观内部期待 (Micro Tension)
        计算：小网颜色（动作/情绪）与 中网颜色（环境氛围）的欧几里得距离。
        该值将直接驱动前端波浪的震动频率与振幅。
        """
        dr = small_color[0] - mid_color[0]
        dg = small_color[1] - mid_color[1]
        db = small_color[2] - mid_color[2]
        return math.sqrt(dr ** 2 + dg ** 2 + db ** 2)
