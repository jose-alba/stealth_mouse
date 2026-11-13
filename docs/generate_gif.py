"""
Script to generate demo.gif for GitHub README.md.
Renders high-quality animated frames in English with minimal text and sleek aesthetics.
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def get_font(size: int, bold: bool = False):
    windir = os.environ.get("WINDIR", "C:/Windows")
    font_name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = os.path.join(windir, "Fonts", font_name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    alt = os.path.join(windir, "Fonts", "arialbd.ttf" if bold else "arial.ttf")
    if os.path.exists(alt):
        return ImageFont.truetype(alt, size)
    return ImageFont.load_default()


def generate_human_stroke(x0, y0, x1, y1, steps, bend_factor=24, tremor_amp=3.0):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        bend = math.sin(t * math.pi) * bend_factor * math.sin(t * 1.4)
        tremor = (math.sin(t * 38) + math.cos(t * 54)) * tremor_amp * math.sin(t * math.pi)

        dx = x1 - x0
        dy = y1 - y0
        length = math.hypot(dx, dy) or 1.0
        nx = -dy / length
        ny = dx / length

        px = x0 + dx * t + nx * (bend + tremor)
        py = y0 + dy * t + ny * (bend + tremor)
        pts.append((px, py))
    return pts


def draw_cursor(draw, x, y):
    pts = [
        (x, y),
        (x, y + 16),
        (x + 4, y + 13),
        (x + 8, y + 20),
        (x + 11, y + 18),
        (x + 7, y + 11),
        (x + 13, y + 11),
    ]
    draw.polygon(pts, fill="#ffffff", outline="#11111b")


def draw_target(draw, x, y, label="", is_hit=False):
    c_out = "#a6e3a1" if is_hit else "#89b4fa"
    c_mid = "#cdd6f4"
    c_in = "#a6e3a1" if is_hit else "#f38ba8"

    draw.ellipse([x - 18, y - 18, x + 18, y + 18], fill="#1e1e2e", outline=c_out, width=2)
    draw.ellipse([x - 11, y - 11, x + 11, y + 11], fill="#313244", outline=c_mid, width=1)
    draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=c_in)

    draw.line([x - 8, y, x + 8, y], fill="#ffffff", width=1)
    draw.line([x, y - 8, x, y + 8], fill="#ffffff", width=1)

    if label:
        font_sm = get_font(11, bold=True)
        draw.text((x, y + 22), label, fill="#cdd6f4", font=font_sm, anchor="mt")


def create_base_canvas(width=760, height=390):
    img = Image.new("RGB", (width, height), color="#0f111a")
    draw = ImageDraw.Draw(img)

    # Grid
    for gx in range(0, width, 38):
        draw.line([gx, 0, gx, height], fill="#181825", width=1)
    for gy in range(0, height, 38):
        draw.line([0, gy, width, gy], fill="#181825", width=1)

    # Frame
    draw.rectangle([12, 12, width - 12, height - 12], outline="#313244", width=1)
    return img, draw


def draw_header_nav(draw, active_step, width=760):
    tabs = [
        "1. Record Dataset",
        "2. 3D KDTree Search",
        "3. Conformal Transform",
        "4. Spline & Timing",
        "5. Mouse Dispatch",
    ]
    font_tab = get_font(11, bold=True)
    tab_w = (width - 48) // len(tabs)
    start_x = 24

    for i, tab in enumerate(tabs, start=1):
        x0 = start_x + (i - 1) * tab_w
        x1 = x0 + tab_w - 6
        y0, y1 = 20, 48

        is_act = (i == active_step)
        is_done = (i < active_step)

        bg = "#1e1e2e" if is_act else "#11111b"
        border = "#89b4fa" if is_act else ("#a6e3a1" if is_done else "#313244")
        text_col = "#89b4fa" if is_act else ("#a6e3a1" if is_done else "#6c7086")

        draw.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=bg, outline=border, width=2 if is_act else 1)
        draw.text(((x0 + x1) // 2, (y0 + y1) // 2), tab, fill=text_col, font=font_tab, anchor="mm")


def draw_footer_badge(draw, text, color="#89b4fa", width=760, height=390):
    font_foot = get_font(12, bold=True)
    box_w = 460
    bx0 = (width - box_w) // 2
    bx1 = bx0 + box_w
    by0 = height - 44
    by1 = height - 18
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=6, fill="#181825", outline=color, width=1)
    draw.text(((bx0 + bx1) // 2, (by0 + by1) // 2), text, fill=color, font=font_foot, anchor="mm")


def main():
    print("Generating demo.gif frames...")
    width, height = 760, 390
    frames = []

    # Segments for Step 1
    seg1 = generate_human_stroke(80, 280, 270, 160, 20, 24, 3.5)
    seg2 = generate_human_stroke(270, 160, 480, 300, 20, -26, 3.2)
    seg3 = generate_human_stroke(480, 300, 680, 180, 20, 22, 3.0)
    segs = [seg1, seg2, seg3]
    seg_colors = ["#89b4fa", "#a6e3a1", "#f9e2af"]

    # Base stroke for Steps 2-5
    target_a = (110, 290)
    target_b = (650, 150)
    base_stroke = generate_human_stroke(110, 290, 650, 150, 35, 26, 3.5)

    # -------------------------------------------------------------
    # STEP 1: Recording Human Strokes (18 frames)
    # -------------------------------------------------------------
    num_frames_s1 = 18
    for f in range(num_frames_s1):
        img, draw = create_base_canvas(width, height)
        draw_header_nav(draw, active_step=1, width=width)

        prog = f / (num_frames_s1 - 1)
        active_seg_idx = min(len(segs) - 1, int(prog * len(segs)))
        local_prog = (prog * len(segs)) - active_seg_idx

        # Completed segments
        for s in range(active_seg_idx):
            pts = segs[s]
            draw.line(pts, fill=seg_colors[s], width=3)
            # Click point
            cx, cy = pts[-1]
            draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=seg_colors[s])
            draw.text((cx + 8, cy - 8), f"Click #{s+1}", fill=seg_colors[s], font=get_font(10, bold=True))

        # Active segment
        cur_seg = segs[active_seg_idx]
        cur_pts_count = max(2, int(local_prog * len(cur_seg)))
        cur_pts = cur_seg[:cur_pts_count]
        draw.line(cur_pts, fill=seg_colors[active_seg_idx], width=3)

        cur_x, cur_y = cur_pts[-1]
        draw_cursor(draw, cur_x, cur_y)

        draw_footer_badge(
            draw,
            f"Recording OS mouse hook (125-250 Hz) • Click-to-click segmentation (#{active_seg_idx+1})",
            color="#89b4fa", width=width, height=height
        )
        frames.append(img)

    # -------------------------------------------------------------
    # STEP 2: 3D KDTree Search (14 frames)
    # -------------------------------------------------------------
    num_frames_s2 = 14
    for f in range(num_frames_s2):
        img, draw = create_base_canvas(width, height)
        draw_header_nav(draw, active_step=2, width=width)
        prog = f / (num_frames_s2 - 1)

        draw_target(draw, 140, 240, label="Start A (x0, y0)")
        draw_target(draw, 380, 160, label="Target B (x1, y1)")

        draw.line([(140, 240), (380, 160)], fill="#6c7086", width=2)

        # Vector badge
        draw.rounded_rectangle([70, 280, 390, 335], radius=6, fill="#1e1e2e", outline="#313244", width=1)
        draw.text((85, 290), "Vector 3D: [ log(dist), cos(θ), sin(θ) ]", fill="#f9e2af", font=get_font(11, bold=True))
        draw.text((85, 310), "Target displacement: dx = 240 px, dy = -80 px", fill="#89b4fa", font=get_font(10))

        # KDTree Radar Stage
        gx, gy, gw, gh = 450, 80, 270, 240
        draw.rectangle([gx, gy, gx + gw, gy + gh], fill="#181825", outline="#f9e2af", width=1)
        draw.text((gx + 12, gy + 10), "3D Feature Space (cKDTree in C++)", fill="#f9e2af", font=get_font(11, bold=True))

        cloud_pts = [
            (500, 140), (530, 210), (620, 160), (660, 230), (590, 250), (640, 280), (550, 270)
        ]
        for px, py in cloud_pts:
            draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill="#45475a")

        qx, qy = 580, 185
        draw.ellipse([qx - 5, qy - 5, qx + 5, qy + 5], fill="#f38ba8")
        draw.text((qx + 8, qy - 8), "Query", fill="#f38ba8", font=get_font(10, bold=True))

        # Pulse circle
        r_pulse = int(prog * 55)
        if r_pulse > 2:
            draw.ellipse([qx - r_pulse, qy - r_pulse, qx + r_pulse, qy + r_pulse], outline="#f9e2af", width=1)

        if prog > 0.4:
            mx, my = 590, 175
            draw.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill="#a6e3a1")
            draw.text((mx + 10, my - 6), "Match #93 (< 0.1 ms)", fill="#a6e3a1", font=get_font(10, bold=True))

        draw_footer_badge(
            draw,
            "Querying KDTree: sub-millisecond nearest neighbor search (< 0.1 ms)",
            color="#f9e2af", width=width, height=height
        )
        frames.append(img)

    # -------------------------------------------------------------
    # STEP 3: Conformal Transformation (14 frames)
    # -------------------------------------------------------------
    num_frames_s3 = 14
    for f in range(num_frames_s3):
        img, draw = create_base_canvas(width, height)
        draw_header_nav(draw, active_step=3, width=width)
        prog = f / (num_frames_s3 - 1)

        draw_target(draw, target_a[0], target_a[1], label="Start A")
        draw_target(draw, target_b[0], target_b[1], label="Target B")

        # Ghost unrotated stroke
        ghost_pts = [(target_a[0] + pt[0] - base_stroke[0][0], target_a[1] + (pt[1] - base_stroke[0][1]) * 0.7) for pt in base_stroke]
        draw.line(ghost_pts, fill="#313244", width=2)
        draw.text((target_a[0] + 160, target_a[1] - 40), "Original recorded geometry", fill="#6c7086", font=get_font(10))

        # Interpolate between ghost and target
        t_morph = min(1.0, prog * 1.2)
        cur_morph_pts = []
        for i in range(len(base_stroke)):
            gx, gy = ghost_pts[i]
            bx, by = base_stroke[i]
            cur_morph_pts.append((gx + (bx - gx) * t_morph, gy + (by - gy) * t_morph))

        draw.line(cur_morph_pts, fill="#f38ba8", width=3)

        # Endpoint
        ex, ey = cur_morph_pts[-1]
        col_end = "#a6e3a1" if t_morph >= 0.95 else "#f9e2af"
        draw.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=col_end)

        draw_footer_badge(
            draw,
            "Conformal 2D mapping: Rotate & scale to land exactly at Target B",
            color="#f38ba8", width=width, height=height
        )
        frames.append(img)

    # -------------------------------------------------------------
    # STEP 4: Spline & Hybrid Timing (14 frames)
    # -------------------------------------------------------------
    num_frames_s4 = 14
    for f in range(num_frames_s4):
        img, draw = create_base_canvas(width, height)
        draw_header_nav(draw, active_step=4, width=width)
        prog = f / (num_frames_s4 - 1)

        draw_target(draw, target_a[0], target_a[1], label="Start A")
        draw_target(draw, target_b[0], target_b[1], label="Target B")

        # Full spline curve
        draw.line(base_stroke, fill="#cba6f7", width=3)

        # Sampled dots at 60-120 Hz
        num_dots = max(2, int(prog * len(base_stroke)))
        for i in range(num_dots):
            dx, dy = base_stroke[i]
            draw.ellipse([dx - 2.5, dy - 2.5, dx + 2.5, dy + 2.5], fill="#a6e3a1")

        # Info Box
        draw.rounded_rectangle([420, 250, 720, 335], radius=6, fill="#1e1e2e", outline="#cba6f7", width=1)
        draw.text((435, 262), "Hybrid Timing & Continuous Spline:", fill="#f9e2af", font=get_font(11, bold=True))
        draw.text((435, 282), "• Close match: 100% pure human recorded time", fill="#cdd6f4", font=get_font(10))
        draw.text((435, 300), "• Large stretch: Fitts law exponential damping", fill="#cdd6f4", font=get_font(10))
        draw.text((435, 318), "• Evaluated at 60-120 Hz with temporal micro-jitter", fill="#a6e3a1", font=get_font(10))

        draw_footer_badge(
            draw,
            "Cubic spline densification at 60-120 Hz • 100% human muscle timing preserved",
            color="#cba6f7", width=width, height=height
        )
        frames.append(img)

    # -------------------------------------------------------------
    # STEP 5: Mouse Dispatch & isTrusted click (18 frames)
    # -------------------------------------------------------------
    num_frames_s5 = 18
    for f in range(num_frames_s5):
        img, draw = create_base_canvas(width, height)
        draw_header_nav(draw, active_step=5, width=width)
        prog = f / (num_frames_s5 - 1)

        is_hit = (prog >= 0.85)
        draw_target(draw, target_a[0], target_a[1], label="Start")
        draw_target(draw, target_b[0], target_b[1], label="Submit Button", is_hit=is_hit)

        # Path traversed so far
        cur_idx = max(1, min(len(base_stroke) - 1, int(prog * len(base_stroke))))
        draw.line(base_stroke[:cur_idx + 1], fill="#a6e3a1", width=3)

        cur_x, cur_y = base_stroke[cur_idx]
        draw_cursor(draw, cur_x, cur_y)

        if is_hit:
            # Click ripple
            draw.ellipse([target_b[0] - 28, target_b[1] - 28, target_b[0] + 28, target_b[1] + 28], outline="#a6e3a1", width=2)
            draw.text((target_b[0] - 80, target_b[1] - 35), "✓ CLICK! (dwell: 75ms)", fill="#a6e3a1", font=get_font(12, bold=True))

        draw_footer_badge(
            draw,
            "Native OS / Playwright dispatch • isTrusted: true • Anti-bots bypassed",
            color="#a6e3a1", width=width, height=height
        )
        frames.append(img)

    # Save as optimized GIF
    output_path = "demo.gif"
    print(f"Saving {len(frames)} frames to {output_path}...")
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=70,  # ~14 fps
        loop=0,
        optimize=True,
    )
    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"Successfully generated {output_path} ({file_size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
