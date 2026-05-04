import pygame
import time
import math
from text_extractor import get_zhaomai_fragments
from color_mapping import ZhaoMaiEmotionalState
from emotion_net import ThreeLevelEmotionNet

# 1. 全局配置 (强制使用项目相对路径，便于跨平台部署)
DOC_PATH = "./data/最后的篝火晚会.docx"
BG_PATH = "./assets/background.jpg"
FONT_SIZE = 33
TEXT_WIDTH = 1000

def draw_minimalist_text(surface, text, font, color, center_pos):
    """前端渲染：极简文本渲染流（处理自动换行与居中对齐）"""
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
    """视觉特效：计算波形位移并渲染带外发光效果的物理级波纹"""
    points = []

    for x in range(0, 1285, 5):
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
    
    # 初始化数据流
    raw_fragments = get_zhaomai_fragments(DOC_PATH)
    print(f"成功加载文本切片: {len(raw_fragments)} 段。")
    if not raw_fragments:
        return

    # 启动网络拓扑分析
    print("正在实例化三级情感提取网络...")
    emotion_net = ThreeLevelEmotionNet(raw_fragments, engine)
    fragments = emotion_net.processed_fragments
    print(f"全局网络基调已锁定: RGB {emotion_net.get_global_net_color()}")
    print("启动图形渲染引擎...")

    # Pygame 上下文初始化
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("ZhaoMai Emotion Engine: Runtime Visualization")

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

    # 物理引擎时钟与状态缓存
    clock = pygame.time.Clock()
    global_offset = 0.0
    current_pen_color = list(emotion_net.get_global_net_color())
    current_bg_color = list(emotion_net.get_global_net_color()) 
    current_rate = 5.0
    current_amp = 20.0

    # 运行时主循环
    for item in fragments:
        section_id = item['section_id']

        target_bg_color = emotion_net.get_middle_net_color(section_id)  
        target_color = emotion_net.get_fused_small_color(item['words'], target_bg_color)

        target_rate = engine.get_pulse_rate(item['words'])
        target_amp, _, _ = engine.get_wave_params(item['words'], target_rate)

        # 动态展示时长控制：给予足够的情绪沉淀时间
        display_duration = max(3.5, len(item['text']) * 0.12)
        start_time = time.time()

        while time.time() - start_time < display_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            dt = clock.tick(60) / 1000.0
            global_offset += current_rate * 2 * dt

            # 执行双重线性插值，平滑色彩切换
            for i in range(3):
                current_pen_color[i] += (target_color[i] - current_pen_color[i]) * 0.05
                current_bg_color[i] += (target_bg_color[i] - current_bg_color[i]) * 0.03

            draw_rgb = (int(current_pen_color[0]), int(current_pen_color[1]), int(current_pen_color[2]))
            draw_bg_rgb = (int(current_bg_color[0]), int(current_bg_color[1]), int(current_bg_color[2]))

            current_rate += (target_rate - current_rate) * 0.03
            current_amp += (target_amp - current_amp) * 0.03

            # 屏幕渲染管道
            screen.blit(bg, (0, 0))

            emotion_overlay = pygame.Surface((1280, 720))
            emotion_overlay.fill(draw_bg_rgb)
            emotion_overlay.set_alpha(150)
            screen.blit(emotion_overlay, (0, 0))

            screen.blit(bg_mask, (0, 0))
            
            draw_heartbeat_line(screen, draw_rgb, current_rate, current_amp, global_offset)

            text_color = [224, 224, 224]
            draw_minimalist_text(screen, item['text'], font, text_color, (640, 360))

            pygame.display.flip()

if __name__ == "__main__":
    main()
