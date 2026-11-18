#!/usr/bin/env python3
"""
Generate Pure Icon Pack style ("轻雨转绘风格") lossless WebP icons for the 17 uncovered
third-party / module / icon-pack apps on Nothing A059:
  1. sing_box.webp                  -> sing-box (io.nekohasekai.sfa)
  2. muntashirakon_app_manager.webp -> App Manager (io.github.muntashirakon.AppManager)
  3. neo_store.webp                 -> Neo Store (com.machiav3lli.fdroid)
  4. webui_x.webp                   -> WebUI X (com.dergoogler.mmrl.wx/.ui.activity.MainActivity)
  5. webui_x_explorer.webp          -> WX Explorer (com.dergoogler.mmrl.wx/.ui.activity.FileExplorerActivity)
  6. estkme.webp                    -> ESTKme (me.estk.lpa)
  7. club_sim.webp                  -> Club Sim (com.pccw.clubsim)
  8. simple_live.webp               -> Simple Live (com.xycz.simple_live)
  9. zhihu_plus.webp                -> 知乎++ (com.github.zly2006.zhplus)
 10. reweibo.webp                   -> ReWeibo LSPosed Module (com.tianqianguai.reweibo)
 11. quiethupu.webp                 -> 虎扑静净 LSPosed Module (io.github.fengwenhua.quiethupu)
 12. tiebaquiet.webp                -> 贴吧静净 LSPosed Module (io.github.yigenhuobah.tiebaquiet)
 13. quietbox.webp                  -> 静盒 LSPosed Module (io.github.yigenhuobah.quietbox)
 14. global_icon_pack.webp          -> Global Icon Pack (com.richardluo.globalIconPack)
 15. arcticons.webp                 -> Arcticons (com.donnnno.arcticons)
 16. lawnicons.webp                 -> Lawnicons (app.lawnchair.lawnicons*)
 17. delta_icon_pack.webp           -> Delta Icon Pack (website.leifs.delta)

Uses Pure Icon Pack's exact 192x192 circular plate + ambient shadow formula derived from vpoints.webp,
combined with 4x supersampled Chromium Skia SVG vector rasterization (768x768 -> 192x192 BOX AA).
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
NODPI_DIR = ROOT / "app" / "src" / "main" / "res" / "drawable-nodpi"
EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CANVAS = 192
SS = 4
CELL = CANVAS * SS  # 768x768 per icon cell


def load_master_plate_profile() -> list[list[tuple[float, int]]]:
    """
    Extract (circle_color_weight f in [0,1], total_alpha A in [0,255]) per pixel from vpoints.webp.
    For any solid RGB=(R,G,B), pixel (round(f*R), round(f*G), round(f*B), A) reproduces Pure Icon Pack's
    exact 174px anti-aliased circle + outer ambient drop shadow to within <=1 LSB!
    """
    ref = Image.open(NODPI_DIR / "vpoints.webp").convert("RGBA")
    px = ref.load()
    grid: list[list[tuple[float, int]]] = []
    for y in range(CANVAS):
        row: list[tuple[float, int]] = []
        for x in range(CANVAS):
            if (x - 96) ** 2 + (y - 96) ** 2 <= 78**2:
                row.append((1.0, 255))
            else:
                r, _, _, a = px[x, y]
                f = min(1.0, max(0.0, r / 250.0))
                row.append((f, a))
        grid.append(row)
    return grid


def make_pure_plate(
    profile: list[list[tuple[float, int]]], rgb: tuple[int, int, int]
) -> Image.Image:
    im = Image.new("RGBA", (CANVAS, CANVAS))
    px = im.load()
    r0, g0, b0 = rgb
    for y in range(CANVAS):
        row = profile[y]
        for x in range(CANVAS):
            f, a = row[x]
            if a == 0:
                px[x, y] = (0, 0, 0, 0)
            elif f >= 1.0:
                px[x, y] = (r0, g0, b0, a)
            elif f <= 0.0:
                px[x, y] = (0, 0, 0, a)
            else:
                px[x, y] = (int(round(r0 * f)), int(round(g0 * f)), int(round(b0 * f)), a)
    return im


# ==============================================================================
# 17 Bespoke Pure Icon Pack Flat Material SVG Specifications (192x192 viewBox)
# ==============================================================================

ICON_SPECS: list[tuple[str, tuple[int, int, int], str]] = [
    # 1. sing-box: #ECEFF1 Blue Grey 50 circle + flat isometric package box
    (
        "sing_box",
        (236, 239, 241),
        """
        <g transform="translate(96,96) scale(0.162) translate(-512,-537)">
          <path d="M512,262 754.5,402 512,542 269.5,402Z" fill="#455A64"/>
          <path d="M269.5,402 512,542 512,812 269.5,672Z" fill="#263238"/>
          <path d="M512,542 754.5,402 754.5,672 512,812Z" fill="#37474F"/>
          <path d="M390.75,472 633.25,332" stroke="#1C262B" stroke-width="6"/>
          <path d="M356.8,351.6 390.75,332 633.25,472 599.3,491.6Z" fill="#B0BEC5"/>
          <path d="M390.75,332 424.7,312.4 667.2,452.4 633.25,472Z" fill="#FAFAFA"/>
          <path d="M599.3,491.6 633.25,472 633.25,592 599.3,611.6Z" fill="#90A4AE"/>
          <path d="M633.25,472 667.2,452.4 667.2,572.4 633.25,592Z" fill="#CFD8DC"/>
        </g>
        """,
    ),
    # 2. App Manager: #212121 circle + warm Material Gold calligraphic 'A' (apex & optical mass aligned)
    (
        "muntashirakon_app_manager",
        (33, 33, 33),
        """
        <g transform="translate(94.5,93.0) scale(0.84) translate(-52.5,-50.5)">
          <path fill="#E0B370" d="m49.76,17.96c-0.2,1.58 -1.1,5.66 -1.63,8.13 -0.49,2.47 -1.67,5.9 -2.52,9.27 -0.81,3.32 -1.96,7.03 -3.46,11.12 -1.5,4.09 -3.22,8.3 -5.17,12.64 -1.94,4.29 -4.44,8.91 -7.47,13.85 -3,4.9 -6.3,9.62 -9.9,14.16 -1.62,2.03 -3.3,3.93 -5.04,5.71 -4.35,4.53 -7.42,7.31 -14.09,12.97 -2.41,2.57 5.25,-0.3 6.89,-1.08 3.79,-1.81 4.45,-2.22 7.7,-4.44 3,-2.31 5.81,-5.05 7.17,-6.35 1.5,-1.42 3.85,-4.09 7.05,-8.02 7.25,-3.61 23.1,-6.48 31.48,-6.24 13.43,0.34 18.96,3.34 23.12,11.46 0.93,2.11 2.06,4.52 3.08,6.75 1.05,2.23 2.31,4.27 3.77,6.14 1.5,1.9 2.9,2.86 4.19,2.86 1.26,0 2.98,-0.63 5.17,-1.88 2.19,-1.22 4.11,-2.57 5.77,-4.07 1.7,-1.46 2.17,-2.31 2.17,-3 0,-0.2 -0.06,-0.34 -0.18,-0.43 -0.08,-0.08 -0.22,-0.1 -0.43,-0.06 -0.16,0 -0.34,0.02 -0.55,0.06 -0.2,0.04 -0.05,-0.12 -0.29,-0.04 -0.2,0.04 -0.38,0.06 -0.55,0.06 -1.94,0 -4.44,-2.37 -7.47,-7.11 -3,-4.78 -6.18,-10.9 -9.54,-18.35 -3.32,-7.45 -6.64,-15.07 -9.97,-22.85 -3.28,-7.78 -7,-15.18 -10.41,-22.63 -3.4,-7.45 -6.22,-12.86 -8.45,-16.23 -1.91,-2.94 -6.26,-11.52 -8.04,-8.66 -0.93,6.82 -0.82,6.53 -2.38,16.27zM57.15,30.86c-0.19,0.31 3.59,6.93 9.66,20.78 6.08,13.85 9.11,21 9.11,21.45l-0.12,0.06c-0.12,0 -0.73,-0.1 -1.82,-0.3 -1.09,-0.24 -2.59,-0.49 -4.5,-0.73 -1.9,-0.24 -3.91,-0.36 -6.02,-0.36 -9.52,0 -19.14,2.37 -28.86,7.11 3.28,-4.46 6.28,-9.16 8.99,-14.1 2.75,-4.94 4.9,-9.34 6.44,-13.19 1.58,-3.85 2.9,-7.39 3.95,-10.63 1.09,-3.24 1.86,-5.73 2.31,-7.47 0.49,-1.74 0.89,-2.68 0.85,-2.61z"/>
        </g>
        """,
    ),
    # 3. Neo Store: #FAFAFA circle + flat Material Blue & Green infinity-bugdroid (true x=82.68..487.32, mid=285.0)
    (
        "neo_store",
        (250, 250, 250),
        """
        <g transform="translate(96,97.5) scale(0.252) translate(-285.0,-280.0)">
          <path fill="#1E88E5" d="m237.84,294h-90c-4.97,0 -9,-4.03 -9,-9s4.03,-9 9,-9h90c4.97,0 9,4.03 9,9s-4.03,9 -9,9Z"/>
          <path fill="#1E88E5" d="m222.7,255.25h-60c-4.97,0 -9,-4.03 -9,-9s4.03,-9 9,-9h60c4.97,0 9,4.03 9,9s-4.03,9 -9,9Z"/>
          <path fill="#1E88E5" d="m222.7,332.75h-60c-4.97,0 -9,-4.03 -9,-9s4.03,-9 9,-9h60c4.97,0 9,4.03 9,9s-4.03,9 -9,9Z"/>
          <path fill="#43A047" d="m344.7,179.33 l-6.84,-12.93c-1.6,-2.25 -1.07,-5.37 1.18,-6.97 2.25,-1.6 5.37,-1.07 6.97,1.18l7.18,13.45c1.94,3.96 2.19,3.06 -3.92,4.83 -3.31,1.12 -3.59,1.84 -4.57,0.45z"/>
          <path fill="#43A047" d="m407.72,178.83 l6.84,-12.93c1.6,-2.25 1.07,-5.37 -1.18,-6.97 -2.25,-1.6 -5.37,-1.07 -6.97,1.18l-7.18,13.45c-1.94,3.96 -2.19,3.06 3.92,4.83 3.31,1.12 3.59,1.84 4.57,0.45z"/>
          <path fill="#43A047" d="m377.16,395.16c-29.6,0 -55.81,-11.97 -75.78,-34.61 -20.41,-23.15 -29.75,-51.83 -33.99,-71.81 -7.99,-37.66 -31.76,-77.89 -74.55,-77.89 -40.89,0 -74.16,33.27 -74.16,74.16s33.27,74.16 74.16,74.16c19.81,0 38.43,-7.71 52.44,-21.72 7.03,-7.03 18.43,-7.03 25.46,0 7.03,7.03 7.03,18.43 0,25.46 -20.81,20.81 -48.47,32.27 -77.89,32.27 -60.74,0 -110.16,-49.42 -110.16,-110.16s49.42,-110.16 110.16,-110.16c29.5,0 55.78,12.25 76,35.43 15.94,18.27 27.93,43.49 33.77,71 3.88,18.27 20.7,77.89 74.55,77.89 40.89,0 74.16,-33.27 74.16,-74.16s-33.27,-74.16 -74.16,-74.16c-19.81,0 -38.43,7.71 -52.44,21.72 -7.03,7.03 -18.43,7.03 -25.46,0 -7.03,-7.03 -7.03,-18.43 0,-25.46 20.81,-20.81 48.47,-32.27 77.89,-32.27 60.74,0 110.16,49.42 110.16,110.16s-49.42,110.16 -110.16,110.16Z"/>
          <path fill="#2E7D32" d="m268.84,210.27c15.94,18.27 27.93,43.49 33.77,71 2.24,10.57 8.82,34.97 24.38,53.67l-25.61,25.61c-20.41,-23.15 -29.75,-51.83 -33.99,-71.81 -3.98,-18.76 -11.88,-38.17 -24.1,-52.92l25.55,-25.55Z"/>
          <path fill="#1E88E5" d="m398.29,327.98c-3.01,0 -5.94,-1.5 -7.65,-4.24 -2.63,-4.22 -1.34,-9.77 2.88,-12.4 9.17,-5.71 14.64,-15.55 14.64,-26.34 0,-17.09 -13.91,-31 -31,-31s-31,13.91 -31,31c0,10.78 5.47,20.63 14.64,26.34 4.22,2.63 5.51,8.18 2.88,12.4 -2.63,4.22 -8.18,5.51 -12.4,2.88 -14.48,-9.02 -23.12,-24.58 -23.12,-41.62 0,-27.02 21.98,-49 49,-49s49,21.98 49,49c0,17.04 -8.64,32.6 -23.12,41.62 -1.48,0.92 -3.13,1.36 -4.75,1.36Z"/>
          <circle cx="357.03" cy="194.84" r="9.5" fill="#FAFAFA"/>
          <circle cx="397.29" cy="194.84" r="9.5" fill="#FAFAFA"/>
        </g>
        """,
    ),
    # 4. WebUI X: #0277BD Ocean Blue circle + crisp #FAFAFA sandbox-mallet
    (
        "webui_x",
        (2, 119, 189),
        """
        <g transform="translate(96,96) scale(4.35) translate(-12,-11.5)" fill="none" stroke="#FAFAFA" stroke-width="2.05" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19.953,8.017l1.047,6.983v2a3,3 0,0 1,-3 3h-12a3,3 0,0 1,-3 -3v-2l1.245,-8.297a2,2 0,0 1,1.977 -1.703h3.778"/>
          <path d="M3,15h18"/>
          <path d="M13,3l5.5,1.5"/>
          <path d="M15.75,3.75l-2,7"/>
          <path d="M7,10.5c1.667,-0.667 3.333,-0.667 5,0c1.667,0.667 3.333,0.667 5,0"/>
        </g>
        """,
    ),
    # 5. WX Explorer: #0277BD Ocean Blue circle + crisp #FAFAFA stacked documents
    (
        "webui_x_explorer",
        (2, 119, 189),
        """
        <g transform="translate(96,96) scale(4.35) translate(-12.5,-12)" fill="none" stroke="#FAFAFA" stroke-width="2.05" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15,3v4a1,1 0,0 0,1 1h4"/>
          <path d="M18,17h-7a2,2 0,0 1,-2 -2v-10a2,2 0,0 1,2 -2h4l5,5v7a2,2 0,0 1,-2 2z"/>
          <path d="M16,17v2a2,2 0,0 1,-2 2h-7a2,2 0,0 1,-2 -2v-10a2,2 0,0 1,2 -2h2"/>
        </g>
        """,
    ),
    # 6. ESTKme: #212121 circle + subtle flat SIM-chip lines + crisp #FAFAFA cut-corner SIM 'e' monogram
    (
        "estkme",
        (33, 33, 33),
        """
        <g stroke="#2E2E2E" stroke-width="3.5" fill="none">
          <line x1="20" y1="68" x2="54" y2="68"/>
          <line x1="20" y1="96" x2="54" y2="96"/>
          <line x1="20" y1="124" x2="54" y2="124"/>
          <line x1="138" y1="68" x2="172" y2="68"/>
          <line x1="138" y1="96" x2="172" y2="96"/>
          <line x1="138" y1="124" x2="172" y2="124"/>
        </g>
        <g transform="translate(96,96) scale(0.5833) translate(-216,-216)">
          <path fill="#FAFAFA" d="
            M156,144 H252 L276,168 V288 H156 V190 H230 V212 H178 V226 H230 V248 H178 V266 H254 V177 L243,166 H156 Z
          "/>
        </g>
        """,
    ),
    # 7. Club Sim: #7B1FA2 Material Purple 700 circle + crisp 15x15 C-L-U-B SIM-chip labyrinth
    (
        "club_sim",
        (123, 31, 162),
        """
        <g transform="translate(54.75,54.75) scale(5.5)" fill="none" stroke="#FAFAFA" stroke-width="1.02" stroke-linecap="square" stroke-linejoin="miter">
          <path d="M14.5,14.5 H0.5 V0.5 H12.2 L14.5,2.8 V10.5 H4.5 V2.5"/>
          <path d="M2.5,2.5 V12.5 H14.5"/>
          <path d="M6.5,2.5 H11.3 L12.5,3.7 V8.5 H6.5 Z"/>
          <path d="M6.5,5.5 H12.5"/>
        </g>
        """,
    ),
    # 8. Simple Live: #FAFAFA circle + #29B6F6 Material Light Blue rounded TV screen + optically centered play triangle
    (
        "simple_live",
        (250, 250, 250),
        """
        <rect x="51" y="60" width="90" height="72" rx="20" fill="#29B6F6"/>
        <path d="M85,83.0 C85,80.7 87.5,79.3 89.5,80.5 L110.5,93.5 C112.4,94.7 112.4,97.3 110.5,98.5 L89.5,111.5 C87.5,112.7 85,111.3 85,109.0 Z" fill="#263238"/>
        """,
    ),
    # 9. Zhihu++ (知乎++): #FAFAFA circle + Liu 看山 arctic fox + translucent Material Blue '++' cross
    (
        "zhihu_plus",
        (250, 250, 250),
        """
        <g transform="translate(96,99) scale(0.255) translate(-308,-308)">
          <path fill="#1E88E5" fill-opacity="0.58" d="M223.79,324.3c-15.32,0 -27.74,-12.42 -27.74,-27.74v-44.32L151.73,252.24c-15.32,0 -27.74,-12.42 -27.74,-27.74s12.42,-27.74 27.74,-27.74L223.79,196.76c15.32,0 27.74,12.42 27.74,27.74v72.06c0,15.32 -12.42,27.74 -27.74,27.74Z"/>
          <path fill="#1E88E5" fill-opacity="0.58" d="M295.85,252.24L223.79,252.24c-15.32,0 -27.74,-12.42 -27.74,-27.74L196.05,152.44c0,-15.32 12.42,-27.74 27.74,-27.74s27.74,12.42 27.74,27.74v44.32h44.32c15.32,0 27.74,12.42 27.74,27.74s-12.42,27.74 -27.74,27.74Z"/>
          <path fill="#FAFAFA" d="M377.19,340.23s23.04,-42.27 42.07,-63.64c17.36,20.37 39.4,81.58 39.4,81.58l-14.02,-3.78s6.63,1.72 14.46,5.16c7.98,3.51 18.97,7.84 23.69,14.92l7.36,11.1v103.85L158.35,489.42v-102.21s21.04,-13.78 40.66,-22.34c9.45,-4.12 24.78,-11.31 24.67,-8.11 0,0 -21.61,6.53 -22.67,5.71s35.27,-65.95 61.54,-95.33c29.05,23.82 45.33,72.09 45.33,72.09l-22.53,2.38c0.12,0.79 54.1,-4.57 108.53,1.77"/>
          <path fill="#212121" d="M160.94,389.05c-0.98,0 -1.93,-0.4 -2.71,-1.57 -1.07,-1.61 -0.64,-3.78 0.97,-4.85 0.33,-0.22 0.69,-0.38 1.06,-0.48 0.89,-0.45 3.4,-1.92 5.84,-3.34 13.98,-8.16 43.07,-25.14 57.55,-25.69 1.92,-0.09 3.56,1.43 3.63,3.37 0.07,1.93 -1.44,3.56 -3.37,3.63 -12.73,0.48 -41.85,17.48 -54.28,24.74 -2.06,1.2 -3.73,2.18 -4.91,2.84 -1.01,0.57 -2.42,1.36 -3.79,1.36Z"/>
          <path fill="#212121" d="M393.99,345.74c-0.1,0 -0.19,0 -0.29,-0.02 -41.75,-4.87 -82.7,-2.83 -100.19,-1.97 -2.54,0.13 -4.53,0.22 -5.88,0.27 -2.1,0.07 -4.28,0.14 -4.63,-2.17 -0.21,-1.37 0.73,-2.64 2.09,-2.85 0.35,-0.06 0.7,-0.03 1.02,0.05 0.91,0.03 3.82,-0.12 7.16,-0.29 17.61,-0.88 58.86,-2.92 101.02,1.99 1.37,0.16 2.35,1.4 2.19,2.77 -0.15,1.27 -1.23,2.21 -2.48,2.21Z"/>
          <path fill="#212121" d="M198.04,360.68c-0.45,-5.4 1.56,-9.71 4.13,-14.06 2.35,-4.15 4.71,-8.29 7.16,-12.38 7.28,-12.32 15.01,-24.4 23.22,-36.14 8.54,-11.93 17.33,-23.62 27.99,-33.89 1.22,-1.18 3.17,-1.14 4.35,0.09 5.35,5.28 10.16,10.85 14.54,16.7 12.89,17.45 22.28,37.61 31.88,56.98 2.08,4.86 -5.32,7.39 -6.63,2.24 -5.83,-24.88 -23.32,-55.51 -44.23,-70.5l4.83,-0.37c-8.31,11.17 -15.84,23.14 -23.13,35.06 -4.89,8.02 -9.64,16.12 -14.38,24.24 -4.34,7.55 -11.42,20.04 -15.69,27.61 -2.01,3.2 -4.52,6.05 -8,7.81 -2.56,1.33 -5.82,-0.51 -6.03,-3.37Z"/>
          <path fill="#212121" d="M374.22,338.43c3.05,-9.35 7.8,-17.66 12.98,-25.87 5.13,-8.2 10.55,-16.18 16.54,-23.83 4.01,-5.09 8.24,-10.05 13.01,-14.6 1.37,-1.64 3.98,-1.71 5.28,0.06 7.13,9.68 11.85,19.87 16.91,30.44 8.14,17.24 14.8,35.05 23.12,52.23 1.9,4.21 -4.15,7.22 -6.33,3.07 -2.06,-7.5 -4.4,-14.97 -7.24,-22.24 -4.79,-12.21 -10.26,-24.4 -16.44,-35.97 -3.42,-6.5 -7.42,-13.01 -11.84,-18.89 -1.13,-1.41 -2.34,-2.74 -3.49,-4.1l5.28,0.06c-9.12,12.53 -17.53,26.16 -25.65,39.4 -4.9,8.17 -9.81,16.27 -15.99,23.63 -2.5,2.96 -7.3,0.29 -6.11,-3.39Z"/>
          <path fill="#212121" d="M487.23,381.28c-1.13,0 -2.24,-0.55 -2.92,-1.56 -7.07,-10.61 -31.67,-19.55 -40.54,-22.1 -1.86,-0.53 -2.93,-2.47 -2.4,-4.33 0.53,-1.86 2.47,-2.93 4.33,-2.4 1.4,0.4 34.49,10.02 44.44,24.94 1.07,1.61 0.64,3.78 -0.97,4.85 -0.6,0.4 -1.27,0.59 -1.94,0.59Z"/>
          <circle cx="233.04" cy="409.46" r="17.81" fill="#212121"/>
          <ellipse cx="409.02" cy="404.34" rx="13.69" ry="15.36" fill="#212121"/>
          <ellipse cx="324.38" cy="415.47" rx="59.38" ry="53.42" fill="#212121"/>
          <circle cx="305.2" cy="395.0" r="2.8" fill="#FAFAFA"/>
          <circle cx="308.6" cy="407.4" r="2.8" fill="#FAFAFA"/>
          <circle cx="347.3" cy="426.5" r="2.8" fill="#FAFAFA"/>
          <circle cx="336.7" cy="442.2" r="2.8" fill="#FAFAFA"/>
          <circle cx="349.9" cy="399.3" r="2.8" fill="#FAFAFA"/>
          <circle cx="336.7" cy="389.6" r="2.8" fill="#FAFAFA"/>
          <circle cx="300.7" cy="424.0" r="2.8" fill="#FAFAFA"/>
        </g>
        """,
    ),
    # 10. ReWeibo (LSPosed Module): #FFF8E1 warm cream circle + Pure flat geometric Red Panda & Refresh-Arrow Tail
    (
        "reweibo",
        (255, 248, 225),
        """
        <g transform="translate(96,97) scale(0.92) translate(-96,-96)">
          <!-- Curved striped Red Panda refresh-arrow tail balanced symmetrically (x=48..144 around cx=96) -->
          <path d="M62,88 C53,106 60,133 85,139 C104,143 120,135 129,122" fill="none" stroke="#D84315" stroke-width="18" stroke-linecap="round"/>
          <!-- Tail dark rings -->
          <path d="M58,99 C57,105 58,111 61,116" fill="none" stroke="#4E342E" stroke-width="18"/>
          <path d="M72,131 C77,135 83,138 89,139.5" fill="none" stroke="#4E342E" stroke-width="18"/>
          <path d="M106,140 C112,138 118,135 122,131" fill="none" stroke="#4E342E" stroke-width="18"/>
          <!-- Crisp Refresh Arrowhead at tail tip (bottom-right, max x=144) -->
          <polygon points="142,107 144,134 118,123" fill="#FF5722"/>
          <!-- Ears -->
          <path d="M62,68 L55,45 C54,42 58,39 61,41 L81,54 Z" fill="#FAFAFA"/>
          <path d="M65,66 L60,49 L76,58 Z" fill="#4E342E"/>
          <path d="M130,68 L137,45 C138,42 134,39 131,41 L111,54 Z" fill="#FAFAFA"/>
          <path d="M127,66 L132,49 L116,58 Z" fill="#4E342E"/>
          <!-- Red Panda Head -->
          <ellipse cx="96" cy="82" rx="37" ry="32" fill="#FF5722"/>
          <!-- White cheek patches & muzzle -->
          <ellipse cx="73" cy="90" rx="13" ry="10" fill="#FAFAFA"/>
          <ellipse cx="119" cy="90" rx="13" ry="10" fill="#FAFAFA"/>
          <ellipse cx="96" cy="93" rx="15" ry="12" fill="#FAFAFA"/>
          <!-- Tear-drop markings -->
          <path d="M81,82 Q78,92 84,98" fill="none" stroke="#BF360C" stroke-width="4" stroke-linecap="round"/>
          <path d="M111,82 Q114,92 108,98" fill="none" stroke="#BF360C" stroke-width="4" stroke-linecap="round"/>
          <!-- Cute white brow spots -->
          <ellipse cx="83" cy="70" rx="5.5" ry="3.5" transform="rotate(-12 83 70)" fill="#FAFAFA"/>
          <ellipse cx="109" cy="70" rx="5.5" ry="3.5" transform="rotate(12 109 70)" fill="#FAFAFA"/>
          <!-- Eyes & Nose -->
          <circle cx="82" cy="80" r="4.6" fill="#3E2723"/>
          <circle cx="110" cy="80" r="4.6" fill="#3E2723"/>
          <circle cx="80.8" cy="78.6" r="1.5" fill="#FAFAFA"/>
          <circle cx="108.8" cy="78.6" r="1.5" fill="#FAFAFA"/>
          <ellipse cx="96" cy="89" rx="5" ry="3.6" fill="#3E2723"/>
          <path d="M91,95 Q96,99 101,95" fill="none" stroke="#3E2723" stroke-width="2.4" stroke-linecap="round"/>
        </g>
        """,
    ),
    # 11. QuietHupu (虎扑静净 LSPosed Module): #212121 circle + #FAFAFA shield + #F44336 Material Red slash
    (
        "quiethupu",
        (33, 33, 33),
        """
        <g transform="translate(96,97) scale(1.12) translate(-54,-55)">
          <path d="M54,18 L84,30 V54 C84,72 71,86 54,92 C37,86 24,72 24,54 V30 Z" fill="none" stroke="#FAFAFA" stroke-width="6.2" stroke-linejoin="round"/>
          <path d="M38,38 L70,70" fill="none" stroke="#F44336" stroke-width="8.2" stroke-linecap="round"/>
        </g>
        """,
    ),
    # 12. TiebaQuiet (贴吧静净 LSPosed Module): #1976D2 Material Blue 700 circle + #FAFAFA shield with centered check cutout
    (
        "tiebaquiet",
        (25, 118, 210),
        """
        <g transform="translate(96,97.5) scale(1.56) translate(-54,-52)">
          <path fill="#FAFAFA" d="M54,26L34,34v14c0,13.3 8.5,25.7 20,30 11.5,-4.3 20,-16.7 20,-30V34L54,26z"/>
          <path fill="#1976D2" d="M45,54l6,6 12,-12 3.2,3.2 -15.2,15.2 -9.2,-9.2z"/>
        </g>
        """,
    ),
    # 13. QuietBox (静盒 LSPosed Module): #212121 circle + #FAFAFA rounded box with horizontal mute bar
    (
        "quietbox",
        (33, 33, 33),
        """
        <rect x="59" y="59" width="74" height="74" rx="10" fill="#FAFAFA"/>
        <rect x="73" y="90" width="46" height="12" rx="4" fill="#212121"/>
        """,
    ),
    # 14. Global Icon Pack: #4CAF50 Material Green circle + #C8E6C9 mint halo + flat Android head & golden sphere
    (
        "global_icon_pack",
        (76, 175, 80),
        """
        <circle cx="96" cy="96" r="52" fill="#E8F5E9"/>
        <g transform="translate(0,3.5)">
          <!-- Antennae -->
          <line x1="78" y1="68" x2="70" y2="55" stroke="#43A047" stroke-width="5.5" stroke-linecap="round"/>
          <line x1="114" y1="68" x2="122" y2="55" stroke="#43A047" stroke-width="5.5" stroke-linecap="round"/>
          <!-- Upper Green Android Dome -->
          <path d="M62,96 A34,34 0 0,1 130,96 Z" fill="#43A047"/>
          <!-- Lower Amber/Gold Sphere Bowl -->
          <path d="M62,96 A34,34 0 0,0 130,96 Z" fill="#FFB300"/>
          <path d="M72,96 A24,22 0 0,0 120,96 Z" fill="#FFE082"/>
          <!-- Eyes -->
          <circle cx="82" cy="82" r="3.6" fill="#FAFAFA"/>
          <circle cx="110" cy="82" r="3.6" fill="#FAFAFA"/>
        </g>
        """,
    ),
    # 15. Arcticons: #212121 circle + crisp #FAFAFA geometric hexagon-node emblem
    (
        "arcticons",
        (33, 33, 33),
        """
        <g transform="translate(96,96) scale(1.92) translate(-54,-54)" fill="none" stroke="#FAFAFA" stroke-width="2.55" stroke-linecap="round" stroke-linejoin="round">
          <path d="M54,39.92 L41.8,46.96V61.04L54,68.08l12.2,-7.04V46.96Z"/>
          <circle cx="36.96" cy="44.16" r="3.33"/>
          <circle cx="54" cy="34.33" r="3.33"/>
          <circle cx="71.04" cy="44.16" r="3.33"/>
          <circle cx="71.04" cy="63.84" r="3.33"/>
          <circle cx="54" cy="73.67" r="3.33"/>
          <circle cx="36.96" cy="63.84" r="3.33"/>
          <line x1="41.8" y1="61.04" x2="39.84" y2="62.17"/>
          <line x1="54" y1="68.08" x2="54" y2="70.35"/>
          <line x1="54" y1="39.92" x2="54" y2="37.64"/>
          <line x1="66.2" y1="61.04" x2="68.17" y2="62.18"/>
          <line x1="66.2" y1="46.96" x2="68.16" y2="45.83"/>
          <line x1="41.8" y1="46.96" x2="39.83" y2="45.82"/>
          <line x1="54" y1="60.18" x2="54" y2="47.99"/>
        </g>
        """,
    ),
    # 16. Lawnicons: #E8F5E9 soft green circle + 2x2 Material You adaptive icon shapes
    (
        "lawnicons",
        (232, 245, 233),
        """
        <circle cx="76" cy="76" r="16" fill="#2E7D32"/>
        <rect x="100" y="60" width="32" height="32" rx="9" fill="#43A047"/>
        <path d="M76,100 C84.84,100 92,107.16 92,116 L92,128 C92,130.21 90.21,132 88,132 L76,132 C67.16,132 60,124.84 60,116 C60,107.16 67.16,100 76,100 Z" fill="#43A047"/>
        <polygon points="116,103 129,116 116,129 103,116" stroke="#2E7D32" stroke-width="6" stroke-linejoin="round" fill="#2E7D32"/>
        """,
    ),
    # 17. Delta Icon Pack: #37474F Blue Grey 800 circle + iconic 3x3 diamond of 9 flat pastel Material dots
    (
        "delta_icon_pack",
        (55, 71, 79),
        """
        <circle cx="96" cy="56" r="8.2" fill="#FF8A80"/>
        <circle cx="76" cy="76" r="8.2" fill="#FFD180"/>
        <circle cx="116" cy="76" r="8.2" fill="#FF80AB"/>
        <circle cx="56" cy="96" r="8.2" fill="#CCFF90"/>
        <circle cx="96" cy="96" r="8.2" fill="#80D8FF"/>
        <circle cx="136" cy="96" r="8.2" fill="#B388FF"/>
        <circle cx="76" cy="116" r="8.2" fill="#A7FFEB"/>
        <circle cx="116" cy="116" r="8.2" fill="#82B1FF"/>
        <circle cx="96" cy="136" r="8.2" fill="#CFD8DC"/>
        """,
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=Path, help="Optional path to save visual preview board PNG")
    args = ap.parse_args()

    profile = load_master_plate_profile()

    cols = 4
    rows = (len(ICON_SPECS) + cols - 1) // cols
    win_w = cols * CELL
    win_h = rows * CELL + 128  # extra bottom margin so headless viewport never clips last row

    cells_html: list[str] = []
    for name, bg_rgb, inner_svg in ICON_SPECS:
        r, g, b = bg_rgb
        cells_html.append(
            f'<div style="width:{CELL}px;height:{CELL}px;overflow:hidden;background:rgb({r},{g},{b})">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{CELL}" height="{CELL}" viewBox="0 0 192 192">'
            f"{inner_svg}</svg></div>"
        )

    html_doc = (
        "<!doctype html><html><head><meta charset='utf-8'/>"
        "<style>*{box-sizing:border-box;margin:0;padding:0}</style></head>"
        f"<body style='width:{win_w}px;background:#000;display:grid;grid-template-columns:repeat({cols},{CELL}px)'>"
        + "".join(cells_html)
        + "</body></html>"
    )

    with tempfile.TemporaryDirectory() as tmpd:
        tmp_dir = Path(tmpd)
        html_file = tmp_dir / "grid.html"
        shot_file = tmp_dir / "grid.png"
        html_file.write_text(html_doc, encoding="utf-8")

        subprocess.run(
            [
                EDGE_BIN,
                "--headless",
                "--disable-gpu",
                "--force-device-scale-factor=1",
                f"--window-size={win_w},{win_h}",
                f"--screenshot={shot_file}",
                str(html_file),
            ],
            check=True,
        )
        grid_im = Image.open(shot_file).convert("RGBA")

    rendered: list[tuple[str, Image.Image]] = []
    for idx, (name, bg_rgb, _) in enumerate(ICON_SPECS):
        r_idx, c_idx = divmod(idx, cols)
        x0, y0 = c_idx * CELL, r_idx * CELL
        cell_hi = grid_im.crop((x0, y0, x0 + CELL, y0 + CELL))
        cell_192 = cell_hi.resize((CANVAS, CANVAS), resample=Image.Resampling.BOX)

        plate = make_pure_plate(profile, bg_rgb)
        dst_px = plate.load()
        src_px = cell_192.load()
        # Copy interior r <= 83px onto master shadow plate (seamless 0-LSB transition inside r=87 rim)
        for y in range(CANVAS):
            for x in range(CANVAS):
                if (x - 96) ** 2 + (y - 96) ** 2 <= 83**2:
                    sr, sg, sb, _ = src_px[x, y]
                    dst_px[x, y] = (sr, sg, sb, 255)

        out_webp = NODPI_DIR / f"{name}.webp"
        plate.save(out_webp, format="WEBP", lossless=True, quality=100, method=6)
        print(f"Saved {out_webp.relative_to(ROOT)} ({out_webp.stat().st_size} bytes)")
        rendered.append((name, plate))

    if args.preview:
        b_cols = 5
        b_rows = (len(rendered) + b_cols - 1) // b_cols
        pad_cell = 224
        board = Image.new("RGBA", (b_cols * pad_cell, b_rows * pad_cell), (26, 28, 32, 255))
        for idx, (_, icon_im) in enumerate(rendered):
            rr, cc = divmod(idx, b_cols)
            board.alpha_composite(icon_im, (cc * pad_cell + 16, rr * pad_cell + 16))
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        board.save(args.preview)
        print(f"Saved preview board to {args.preview}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
