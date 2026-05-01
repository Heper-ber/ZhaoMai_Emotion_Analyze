import jieba.analyse

# 10个情节的意象锚点
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
    """三层嵌套情绪网架构师"""

    def __init__(self, fragments, engine):
        self.engine = engine

        # 1. 由网自己来划分文本，打上 section_id
        self.processed_fragments = self._partition_fragments(fragments)

        # 2. 【一级网：大网 (Global)】计算全书性格底色
        self.global_base = self._build_global_net()

        # 3. 【二级网：中网 (Middle)】计算 10 个情节各自的氛围光
        self.middle_nets = {}
        self._build_middle_nets()

    def _partition_fragments(self, raw_fragments):
        """用叙事锚点给纯净的片段划分情节，打上 section_id"""
        current_section = 1
        processed = []

        for f in raw_fragments:
            text = f["text"]
            # 探测中网边界
            for sec_id, anchors in PLOT_ANCHORS.items():
                if any(anchor in text for anchor in anchors) and sec_id >= current_section:
                    current_section = sec_id
                    break

            f["section_id"] = current_section
            processed.append(f)

        return processed

    def _build_global_net(self):
        """编织大网：提取全篇性格底色"""
        all_text = "".join([f["text"] for f in self.processed_fragments])
        keywords = jieba.analyse.extract_tags(all_text, topK=50)
        matched_colors = [self.engine.color_db[w] for w in keywords if w in self.engine.color_db]
        # 这里是在对齐我自己选出来的情感字典

        if matched_colors:
            avg_r = sum(c[0] for c in matched_colors) // len(matched_colors)
            avg_g = sum(c[1] for c in matched_colors) // len(matched_colors)
            avg_b = sum(c[2] for c in matched_colors) // len(matched_colors)
            return [avg_r, avg_g, avg_b]

        return [112, 128, 144]

    def _build_middle_nets(self):
        """编织中网：用 jieba 提取每个情节的特征"""
        section_texts = {i: "" for i in range(1, 11)}

        for f in self.processed_fragments:
            sid = f["section_id"]
            if sid in section_texts:
                section_texts[sid] += f["text"]


        # 轮流检查这 10 个纸箱。如果某个箱子是空的（没提取到字），
        # 为了防止程序报错，就直接给它涂上大网的全局底色，然后跳过去看下一个箱子。
        for sid, text in section_texts.items():
            if not text:
                self.middle_nets[sid] = self.global_base
                continue

            keywords = jieba.analyse.extract_tags(text, topK=10)
            matched_colors = [self.engine.color_db[w] for w in keywords if w in self.engine.color_db]
            # 中网也要和我的字典对应

            if matched_colors:
                # 1. 先算出当前情节纯粹的局部颜色
                local_r = sum(c[0] for c in matched_colors) // len(matched_colors)
                local_g = sum(c[1] for c in matched_colors) // len(matched_colors)
                local_b = sum(c[2] for c in matched_colors) // len(matched_colors)

                # ==========================================
                # 核心魔法：大网晶核的基因渗透 (Alpha Blending)
                # 设定：宿命底色（大网）占 30%，当前境遇（中网）占 70%
                # ==========================================
                core_weight = 0.3
                local_weight = 0.7

                final_r = int((self.global_base[0] * core_weight) + (local_r * local_weight))
                final_g = int((self.global_base[1] * core_weight) + (local_g * local_weight))
                final_b = int((self.global_base[2] * core_weight) + (local_b * local_weight))

                self.middle_nets[sid] = [final_r, final_g, final_b]
            else:
                self.middle_nets[sid] = self.global_base

    # ================= 对外提供的“取色”接口 =================

    def get_global_net_color(self):
        """获取大网颜色 (全书底色)"""
        return self.global_base

    def get_middle_net_color(self, section_id):
        """获取中网颜色 (当前情节氛围)"""
        return self.middle_nets.get(section_id, self.global_base)

    def get_small_net_color(self, words):
        """获取小网颜色 (单句瞬时跳动)"""
        hex_color = self.engine.update(words)
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5)) # 把十六进制转换成了十进制的 RGB 元组。
        return rgb

    def get_fused_small_color(self, words, current_mid_color):
        """
        核心逻辑：中网对小网的基因渗透
        words: 当前句子的分词列表
        current_mid_color: 已经包含大网背景色的中网当前颜色
        """
        # 1. 算出小网极其纯粹、敏锐的瞬时原始色
        raw_small = self.get_small_net_color(words)

        # 2. 设定 80/20 渗透比例（小网占 80% 保证灵敏度，中网占 20% 提供环境约束）
        s_w, m_w = 0.8, 0.2

        # 3. 颜色基因融合
        fused_color = [
            int(current_mid_color[0] * m_w + raw_small[0] * s_w),
            int(current_mid_color[1] * m_w + raw_small[1] * s_w),
            int(current_mid_color[2] * m_w + raw_small[2] * s_w)
        ]
        return fused_color

