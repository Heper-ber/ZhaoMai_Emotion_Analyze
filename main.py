import pygame
import time
import math
from text_extractor import get_zhaomai_fragments
from color_mapping import ZhaoMaiEmotionalState
from emotion_net import ThreeLevelEmotionNet

# 1. 配置参数 (请确保路径正确)
DOC_PATH = "C:/My_profiles/sophomore_spring/emotion_analyze/最后的篝火晚会.docx"
BG_PATH = "C:/My_profiles/sophomore_spring/emotion_analyze/background.jpg"
FONT_SIZE = 33
TEXT_WIDTH = 1000


def draw_minimalist_text(surface, text, font, color, center_pos):
    """纯净文本渲染：自动换行 + 居中"""
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
    """带外发光效果的彩色心电图（修复相位跳变版）"""
    points = []

    for x in range(0, 1285, 5):
        # 【修改点】：这里直接用传进来的 offset，彻底解决波浪抽搐
        y = 650 + math.sin(x * 0.04 + offset) * amp
        if pulse_rate > 10:
            y += (math.sin(x * 0.1) * amp * 0.3)
        points.append((x, y))

    if len(points) > 1:
        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        glow_color = (*color, 100)
        pygame.draw.lines(glow_surf, glow_color, False, points, width=12)
        surface.blit(glow_surf, (0, 0))
        pygame.draw.lines(surface, color, False, points, width=5)


def main():
    engine = ZhaoMaiEmotionalState()
    # 1. 获取纯净文本
    raw_fragments = get_zhaomai_fragments(DOC_PATH)

    print(f"成功加载了 {len(raw_fragments)} 段文字。")
    if len(raw_fragments) == 0:
        return

    # 2. 扔给大脑去织网并打标签
    print("正在编织三层情绪网...")
    emotion_net = ThreeLevelEmotionNet(raw_fragments, engine)
    fragments = emotion_net.processed_fragments
    print(f"大网（全书底色）已计算: RGB{emotion_net.get_global_net_color()}")
    print("放映开始！")

    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("赵麦：三级情感显影放映机")

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

    # ==========================================
    # 【新增补漏】：启动物理引擎时钟和波浪位移器
    # ==========================================
    clock = pygame.time.Clock()
    global_offset = 0.0
    # ==========================================
    # 在进入循环前，准备好所有的“记忆画笔”
    # ==========================================
    current_pen_color = list(emotion_net.get_global_net_color())
    current_bg_color = list(emotion_net.get_global_net_color())  # 【新增】给中网背景也加一把“记忆画笔”
    current_rate = 5.0
    current_amp = 20.0

    for item in fragments:
        section_id = item['section_id']

        # 我们的两个“目标颜色”
        target_bg_color = emotion_net.get_middle_net_color(section_id)  # 中网目标色
        # 小网和中网关联
        target_color = emotion_net.get_fused_small_color(item['words'], target_bg_color)

        # 大网和中网都是用来铺“背景”的，只有小网是用来画那条跳动的“心电图”的！

        target_rate = engine.get_pulse_rate(item['words'])
        target_amp, _, _ = engine.get_wave_params(item['words'], target_rate)

        # 【重点修复】：控制文字停留时长！
        # 基础停留3秒，每多一个字增加 0.25 秒。长段落能停顿七八秒，让渐变充分展现。
        display_duration = max(3.5, len(item['text']) * 0.12)
        start_time = time.time()

        while time.time() - start_time < display_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            dt = clock.tick(60) / 1000.0
            global_offset += current_rate * 2 * dt

            # ==========================================
            # 核心魔法：双重线性插值 (Lerp)
            # ==========================================
            for i in range(3):
                # 1. 波浪颜色渐变 (小网)
                current_pen_color[i] += (target_color[i] - current_pen_color[i]) * 0.05
                # 2. 【新增】背景颜色渐变 (中网)！系数 0.02 更慢，像云层一样缓慢变换
                current_bg_color[i] += (target_bg_color[i] - current_bg_color[i]) * 0.03

            draw_rgb = (int(current_pen_color[0]), int(current_pen_color[1]), int(current_pen_color[2]))
            draw_bg_rgb = (int(current_bg_color[0]), int(current_bg_color[1]), int(current_bg_color[2]))

            # 物理波动的缓冲渐变
            current_rate += (target_rate - current_rate) * 0.03
            current_amp += (target_amp - current_amp) * 0.03

            screen.blit(bg, (0, 0))

            # 【应用新增的渐变背景色】
            emotion_overlay = pygame.Surface((1280, 720))
            emotion_overlay.fill(draw_bg_rgb)
            emotion_overlay.set_alpha(150)
            screen.blit(emotion_overlay, (0, 0))

            screen.blit(bg_mask, (0, 0))

            # 画波浪
            draw_heartbeat_line(screen, draw_rgb, current_rate, current_amp, global_offset)

            # 画文字
            text_color = [224, 224, 224]
            draw_minimalist_text(screen, item['text'], font, text_color, (640, 360))

            pygame.display.flip()


if __name__ == "__main__":
    main()