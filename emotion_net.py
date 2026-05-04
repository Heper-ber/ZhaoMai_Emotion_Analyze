import jieba.analyse

# 场景意象锚点 (Plot Anchors) 用于边界探测
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
    架构设计：三级嵌套特征融合网络 (3-Tier Hierarchical Emotion Network)
    层级说明：
    - 大网 (Global Net)：提取全书性格底色 (Base Context)
    - 中网 (Middle Net)：提取各切片情节的氛围光 (Scene Atmosphere)
    - 小网 (Small Net)：即时情绪跳动融合 (Instantaneous Fluctuation)
    """
    def __init__(self, fragments, engine):
        self.engine = engine
        # 1. 初始化模块：片段分词与章节边界探测
        self.processed_fragments = self._partition_fragments(fragments)
        # 2. 全局层：计算宏观叙事基调
        self.global_base = self._build_global_net()
        # 3. 局部层：计算特定场景环境影响向量
        self.middle_nets = {}
        self._build_middle_nets()

    def _partition_fragments(self, raw_fragments):
        """叙事边界识别：基于意象锚点自动为文本切片打标 (section_id)"""
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
        """构建大网：利用 TF-IDF (jieba.analyse) 提取全局性格底色"""
        all_text = "".join([f["text"] for f in self.processed_fragments])
        keywords = jieba.analyse.extract_tags(all_text, topK=50)
        matched_colors = [self.engine.color_db[w] for w in keywords if w in self.engine.color_db]

        if matched_colors:
            avg_r = sum(c[0] for c in matched_colors) // len(matched_colors)
            avg_g = sum(c[1] for c in matched_colors) // len(matched_colors)
            avg_b = sum(c[2] for c in matched_colors) // len(matched_colors)
            return [avg_r, avg_g, avg_b]
        return [112, 128, 144]

    def _build_middle_nets(self):
        """构建中网：计算章节局部色彩，并执行 Alpha Blending 融合机制"""
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

                # 核心机制：环境基因渗透 (Alpha Blending)
                # 算法假设：人物情绪受"宿命底色(30%)"与"当前境遇(70%)"共同影响
                core_weight = 0.3
                local_weight = 0.7

                final_r = int((self.global_base[0] * core_weight) + (local_r * local_weight))
                final_g = int((self.global_base[1] * core_weight) + (local_g * local_weight))
                final_b = int((self.global_base[2] * core_weight) + (local_b * local_weight))

                self.middle_nets[sid] = [final_r, final_g, final_b]
            else:
                self.middle_nets[sid] = self.global_base

    # ================= 供外部渲染调用的接口 =================

    def get_global_net_color(self):
        """获取全书宿命底色"""
        return self.global_base

    def get_middle_net_color(self, section_id):
        """获取章节当前境遇氛围色"""
        return self.middle_nets.get(section_id, self.global_base)

    def get_small_net_color(self, words):
        """获取单句瞬时跳动色"""
        hex_color = self.engine.update(words)
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5)) 
        return rgb

    def get_fused_small_color(self, words, current_mid_color):
        """
        三级融合输出：计算中网环境约束下的小网瞬时爆发表现
        """
        raw_small = self.get_small_net_color(words)
        
        # 权重配比：保留 80% 瞬时灵敏度，施加 20% 环境平滑约束
        s_w, m_w = 0.8, 0.2

        fused_color = [
            int(current_mid_color[0] * m_w + raw_small[0] * s_w),
            int(current_mid_color[1] * m_w + raw_small[1] * s_w),
            int(current_mid_color[2] * m_w + raw_small[2] * s_w)
        ]
        return fused_color
