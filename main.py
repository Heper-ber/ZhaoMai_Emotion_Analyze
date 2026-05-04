import pygame
import time
import math
import random
from text_extractor import get_zhaomai_fragments
from color_mapping import ZhaoMaiEmotionalState
from emotion_net import ThreeLevelEmotionNet

# 系统常量与路径配置
DOC_PATH = "./data/最后的篝火晚会.docx"
BG_PATH = "./assets/background.jpg"
FONT_SIZE = 33
TEXT_WIDTH = 1000

def draw_minimalist_text(surface, text, font, color, center_pos):
    """前端渲染：实现极简主义的文字自动换行与居中对齐排版"""
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        w, _ = font.size(test_line)
        if w <= TEXT_WIDTH:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line: lines.append(current_line)

    line_height = font.get_linesize()
    total_height = line_height * len(lines)
    start_y = center_pos[1] - total_height // 2

    for line in lines:
        temp_surface = font.render(line, True, color)
        line_rect = temp_surface.get_rect(center=(center_pos[0], start_y + line_height // 2))
        surface.blit(temp_surface, line_rect)
        start_y += line_height

def draw_heartbeat_line(surface, color, pulse_rate, amp, offset):
    """
    🌊 物理波纹渲染器：基于微观张力无级变速
    引入了平滑噪音因子(noise_factor)，当张力极高时，波浪会产生连贯的心悸感，而非生硬抽搐。
    """
    points = []

    # 计算一个噪音因子：心率越快，噪音平滑增加
    noise_factor = max(0, (pulse_rate - 6) / 10.0)

    for x in range(0, 1285, 5):
        y = 650 + math.sin(x * 0.04 + offset) * amp
        if noise_factor > 0:
            # 噪音受张力因子严格控制
            y += (math.sin(x * 0.15) * amp * 0.5 * noise_factor)
        points.append((x, y))

    if len(points) > 1:
        # 渲染底层的高级外发光辉光效果
        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        glow_color = (*color, 100)
        pygame.draw.lines(glow_surf, glow_color, False, points, width=12)
        surface.blit(glow_surf, (0, 0))
        # 渲染清晰的主心电图线条
        pygame.draw.lines(surface, color, False, points, width=5)

def draw_narrative_arc(surface, macro_tensions, current_section, font):
    """
    📊 上帝视角：渲染宏观叙事张力弧（剧本心电图）
    直观展示小说命运的起承转合。
    """
    if not macro_tensions: return
    max_t = max(macro_tensions)
    if max_t == 0: max_t = 1

    start_x = 980
    start_y = 150
    max_h = 80
    bar_w = 15
    gap = 8

    # 渲染图表标题
    try:
        small_font = pygame.font.SysFont("arial", 16)
        title_surf = small_font.render("Macro Narrative Arc (Section Tension)", True, (180, 180, 180))
        surface.blit(title_surf, (start_x - 10, start_y - max_h - 25))
    except:
        pass

    # 渲染张力柱状图
    for i, t in enumerate(macro_tensions):
        h = (t / max_t) * max_h
        rect_x = start_x + i * (bar_w + gap)
        rect_y = start_y - h

        # 进度指示器：当前章节标红高亮
        if (i + 1) == current_section:
            pygame.draw.rect(surface, (255, 80, 80), (rect_x, rect_y, bar_w, h))
        else:
            s = pygame.Surface((bar_w, h))
            s.set_alpha(90)
            s.fill((150, 150, 150))
            surface.blit(s, (rect_x, rect_y))

def main():
    # 1. 启动情绪特征映射引擎
    engine = ZhaoMaiEmotionalState()
    raw_fragments = get_zhaomai_fragments(DOC_PATH)
    if not raw_fragments:
        return

    # 2. 将文本灌入三级嵌套网络，完成全书的张力微积分运算
    emotion_net = ThreeLevelEmotionNet(raw_fragments, engine)
    fragments = emotion_net.processed_fragments
    macro_tensions = emotion_net.macro_tensions

    # 3. 初始化 Pygame 放映机
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("ZhaoMai: Dual-Layer Expectation Engine (Minimalist Ver.)")

    try:
        font = pygame.font.SysFont(["microsoftyahei", "SimHei"], FONT_SIZE)
    except:
        font = pygame.font.SysFont("arial", FONT_SIZE)

    try:
        bg = pygame.image.load(BG_PATH).convert_alpha()
        bg = pygame.transform.scale(bg, (1280, 720))
    except:
        bg = pygame.Surface((1280, 720))
        bg.fill((20, 24, 35))

    bg_mask = pygame.Surface((1280, 720)).convert_alpha()
    bg_mask.fill((10, 12, 18, 110))

    clock = pygame.time.Clock()
    global_offset = 0.0
    current_pen_color = list(emotion_net.get_global_net_color())
    current_bg_color = list(emotion_net.get_global_net_color())

    # 🔥 初始状态：设定为极其平静的微波起伏
    current_rate = 2.0
    current_amp = 8.0

    # 4. 进入核心渲染流
    for item in fragments:
        section_id = item['section_id']
        target_bg_color = emotion_net.get_middle_net_color(section_id)
        target_color = emotion_net.get_fused_small_color(item['words'], target_bg_color)

        # 实时获取当前句子的微观张力
        micro_tension = emotion_net.get_micro_tension(target_color, target_bg_color)

        # 🔥 柔和映射：用微观张力动态计算目标波浪的频率和振幅
        target_rate = max(1.5, min(12.0, 1.5 + micro_tension / 15.0))
        target_amp = max(8.0, min(35.0, 8.0 + micro_tension / 4.0))

        display_duration = max(3.5, len(item['text']) * 0.12)
        start_time = time.time()

        while time.time() - start_time < display_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            dt = clock.tick(60) / 1000.0
            global_offset += current_rate * 2 * dt

            # 色彩的阻尼平滑插值（呼吸感过渡）
            for i in range(3):
                current_pen_color[i] += (target_color[i] - current_pen_color[i]) * 0.05
                current_bg_color[i] += (target_bg_color[i] - current_bg_color[i]) * 0.03

            draw_rgb = (int(current_pen_color[0]), int(current_pen_color[1]), int(current_pen_color[2]))
            draw_bg_rgb = (int(current_bg_color[0]), int(current_bg_color[1]), int(current_bg_color[2]))

            # 波浪物理参数的平滑插值过渡
            current_rate += (target_rate - current_rate) * 0.015
            current_amp += (target_amp - current_amp) * 0.015

            # ---------------- 图像绘制 ----------------
            screen.blit(bg, (0, 0))
            
            # 动态环境滤镜层
            emotion_overlay = pygame.Surface((1280, 720))
            emotion_overlay.fill(draw_bg_rgb)
            emotion_overlay.set_alpha(150)
            screen.blit(emotion_overlay, (0, 0))
            screen.blit(bg_mask, (0, 0))

            text_pos = (640, 360)

            # 渲染各个图层
            draw_heartbeat_line(screen, draw_rgb, current_rate, current_amp, global_offset)
            draw_minimalist_text(screen, item['text'], font, [224, 224, 224], text_pos)
            draw_narrative_arc(screen, macro_tensions, section_id, font)

            pygame.display.flip()

if __name__ == "__main__":
    main()
