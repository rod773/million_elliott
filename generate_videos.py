"""
AUD/USD Elliott Wave + MACD Course — Video Generator
Generates one MP4 per module using Pillow (slides) + gTTS (narration) + MoviePy
"""

import os
import re
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from gtts import gTTS
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
)

# ── Configuration ────────────────────────────────────────────────────────────
OUTPUT_DIR   = Path("videos")
TEMP_DIR     = Path("temp")
WIDTH, HEIGHT = 1280, 720
FPS           = 24
LANG          = "en"   # gTTS language

# ── Colors ────────────────────────────────────────────────────────────────────
BG_DARK      = (15,  20,  35)
BG_SLIDE     = (20,  27,  50)
ACCENT_GOLD  = (212, 175,  55)
ACCENT_BLUE  = ( 64, 156, 255)
ACCENT_GREEN = ( 72, 199, 142)
ACCENT_RED   = (255,  80,  80)
WHITE        = (255, 255, 255)
GRAY         = (160, 170, 195)
DARK_LINE    = ( 40,  50,  80)

# ── Font helpers ──────────────────────────────────────────────────────────────
def get_font(size: int, bold: bool = False):
    candidates_bold   = ["arialbd.ttf", "Arial_Bold.ttf", "DejaVuSans-Bold.ttf"]
    candidates_normal = ["arial.ttf",   "Arial.ttf",      "DejaVuSans.ttf"]
    candidates = candidates_bold if bold else candidates_normal
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()

FONT_TITLE   = get_font(52, bold=True)
FONT_HEADING = get_font(36, bold=True)
FONT_BODY    = get_font(26)
FONT_SMALL   = get_font(20)
FONT_LABEL   = get_font(18, bold=True)


# ── Drawing helpers ───────────────────────────────────────────────────────────
def new_slide() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_SLIDE)
    d   = ImageDraw.Draw(img)
    # top accent bar
    d.rectangle([(0, 0), (WIDTH, 6)], fill=ACCENT_GOLD)
    # bottom bar
    d.rectangle([(0, HEIGHT - 4), (WIDTH, HEIGHT)], fill=DARK_LINE)
    return img, d


def draw_text_wrapped(d, text, x, y, font, color, max_width, line_spacing=8):
    """Draw text with word-wrap. Returns the y position after the last line."""
    words  = text.split()
    lines  = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        bbox = d.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    for line in lines:
        d.text((x, y), line, font=font, fill=color)
        bbox = d.textbbox((0, 0), line, font=font)
        y   += (bbox[3] - bbox[1]) + line_spacing
    return y


def draw_logo(d):
    """Small branding tag bottom-right."""
    d.text((WIDTH - 320, HEIGHT - 32), "AUD/USD Million Dollar Course",
           font=FONT_SMALL, fill=GRAY)


def pill(d, x, y, w, h, color, radius=12):
    """Rounded rectangle."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=color)


# ── Slide builders ────────────────────────────────────────────────────────────
def slide_title(title: str, subtitle: str, module_num: str) -> Image.Image:
    img, d = new_slide()
    # dark overlay gradient effect (horizontal band)
    d.rectangle([(0, 200), (WIDTH, 520)], fill=(10, 15, 28))
    # module badge
    pill(d, 60, 220, 200, 44, ACCENT_GOLD, radius=22)
    d.text((70, 228), module_num, font=FONT_LABEL, fill=BG_DARK)
    # title
    draw_text_wrapped(d, title, 60, 290, FONT_TITLE, WHITE, WIDTH - 120)
    # subtitle
    draw_text_wrapped(d, subtitle, 60, 390, FONT_HEADING, ACCENT_BLUE, WIDTH - 120)
    # decorative lines
    d.rectangle([(60, 460), (400, 464)], fill=ACCENT_GOLD)
    d.rectangle([(60, 470), (280, 473)], fill=ACCENT_BLUE)
    draw_logo(d)
    return img


def slide_section(heading: str, bullets: list[str],
                  accent=ACCENT_GOLD) -> Image.Image:
    img, d = new_slide()
    # heading bar
    d.rectangle([(0, 60), (WIDTH, 130)], fill=(25, 35, 65))
    d.text((60, 75), heading, font=FONT_HEADING, fill=accent)
    # bullets
    y = 158
    for b in bullets:
        # bullet dot
        d.ellipse([(60, y + 8), (72, y + 20)], fill=accent)
        y = draw_text_wrapped(d, b, 88, y, FONT_BODY, WHITE, WIDTH - 150)
        y += 10
    draw_logo(d)
    return img


def slide_table(heading: str, headers: list[str],
                rows: list[list[str]], accent=ACCENT_GOLD) -> Image.Image:
    img, d = new_slide()
    d.rectangle([(0, 60), (WIDTH, 130)], fill=(25, 35, 65))
    d.text((60, 75), heading, font=FONT_HEADING, fill=accent)

    col_w = (WIDTH - 120) // len(headers)
    y = 148
    # header row
    for i, h in enumerate(headers):
        x = 60 + i * col_w
        d.rectangle([(x, y), (x + col_w - 6, y + 38)], fill=accent)
        d.text((x + 8, y + 6), h, font=FONT_LABEL, fill=BG_DARK)
    y += 46

    for ri, row in enumerate(rows):
        row_bg = (28, 38, 68) if ri % 2 == 0 else (22, 30, 55)
        d.rectangle([(60, y), (WIDTH - 60, y + 36)], fill=row_bg)
        for i, cell in enumerate(row):
            x = 60 + i * col_w
            d.text((x + 8, y + 6), str(cell), font=FONT_BODY, fill=WHITE)
        y += 38

    draw_logo(d)
    return img


def slide_code(heading: str, code_lines: list[str],
               accent=ACCENT_GOLD) -> Image.Image:
    img, d = new_slide()
    d.rectangle([(0, 60), (WIDTH, 130)], fill=(25, 35, 65))
    d.text((60, 75), heading, font=FONT_HEADING, fill=accent)
    # code block bg
    d.rectangle([(50, 140), (WIDTH - 50, HEIGHT - 60)], fill=(12, 16, 30))
    y = 155
    for line in code_lines:
        color = ACCENT_GREEN if line.startswith("→") or line.startswith("#") \
                else ACCENT_GOLD if ":" in line[:20] \
                else WHITE
        d.text((70, y), line, font=FONT_BODY, fill=color)
        y += 34
        if y > HEIGHT - 80:
            break
    draw_logo(d)
    return img


def slide_rule(rule_text: str, detail: str, accent=ACCENT_RED) -> Image.Image:
    img, d = new_slide()
    pill(d, 60, 80, 180, 50, accent, radius=25)
    d.text((74, 92), "⚠  RULE", font=FONT_LABEL, fill=WHITE)
    draw_text_wrapped(d, rule_text, 60, 165, FONT_TITLE, WHITE, WIDTH - 120)
    draw_text_wrapped(d, detail,    60, 320, FONT_BODY,  GRAY,  WIDTH - 120)
    d.rectangle([(60, 290), (WIDTH - 60, 293)], fill=accent)
    draw_logo(d)
    return img


# ── Audio helpers ─────────────────────────────────────────────────────────────
def make_audio(text: str, path: Path) -> float:
    """Generate TTS audio, return duration in seconds."""
    tts = gTTS(text=text, lang=LANG, slow=False)
    tts.save(str(path))
    clip = AudioFileClip(str(path))
    dur  = clip.duration
    clip.close()
    return dur


def img_to_clip(img: Image.Image, duration: float,
                audio_path: Path | None = None):
    """Convert a PIL image to a MoviePy clip with optional audio."""
    arr  = np.array(img)
    clip = ImageClip(arr, duration=duration)
    if audio_path and audio_path.exists():
        audio = AudioFileClip(str(audio_path)).subclip(0, duration)
        clip  = clip.set_audio(audio)
    return clip.set_fps(FPS)


# ── Module content ────────────────────────────────────────────────────────────
MODULES = [

  # ── MODULE 1 ─────────────────────────────────────────────────────────────
  {
    "id": "01",
    "title": "Foundations: Understanding AUD/USD",
    "subtitle": "What drives the pair, best sessions & chart setup",
    "slides": [
      {
        "type": "section",
        "heading": "What is AUD/USD?",
        "bullets": [
            "Represents the Australian Dollar vs the US Dollar",
            "1 AUD = X USD  —  e.g. 0.6500 means 1 AUD buys 0.65 USD",
            "Top-5 most traded currency pair globally",
            "~$300 billion+ traded every single day",
            "Ideal for Elliott Wave: clean, trending structure",
        ],
        "narration": (
            "Welcome to Module 1. AUD slash USD is one of the world's most liquid "
            "currency pairs, trading over 300 billion dollars daily. "
            "When the rate is 0.65, one Australian Dollar buys 65 US cents. "
            "Its strong trending nature makes it perfect for Elliott Wave analysis."
        ),
      },
      {
        "type": "table",
        "heading": "Why Trade AUD/USD?",
        "headers": ["Advantage", "Why It Matters"],
        "rows": [
            ["High Liquidity",      "Tight spreads, minimal slippage"],
            ["Clear Trends",        "Elliott Wave structures form cleanly"],
            ["MACD Reliability",    "Trending market = quality divergences"],
            ["Commodity Link",      "Gold & iron ore give macro context"],
            ["Two Active Sessions", "Asia/London and NY overlap"],
        ],
        "narration": (
            "AUD slash USD is ideal for our system for five key reasons. "
            "It is highly liquid, meaning tight spreads. "
            "It trends clearly, making Elliott Wave counts reliable. "
            "MACD divergences are high quality in trending markets. "
            "Being linked to commodities like gold gives us fundamental context. "
            "And two overlapping sessions provide good intraday volume."
        ),
      },
      {
        "type": "section",
        "heading": "What Drives AUD/USD — Bullish Factors",
        "accent": ACCENT_GREEN,
        "bullets": [
            "Rising commodity prices: gold, iron ore, coal",
            "Strong Australian economic data: GDP, CPI, employment",
            "RBA raising interest rates (hawkish)",
            "Risk-ON global sentiment — AUD is a risk currency",
            "Weak US Dollar (falling DXY index)",
        ],
        "narration": (
            "The Australian Dollar rises when commodities like gold and iron ore rally, "
            "when Australian economic data is strong, "
            "when the Reserve Bank of Australia raises interest rates, "
            "when global investors are in risk-on mode, "
            "or when the US Dollar is weakening."
        ),
      },
      {
        "type": "section",
        "heading": "What Drives AUD/USD — Bearish Factors",
        "accent": ACCENT_RED,
        "bullets": [
            "Falling commodity prices",
            "Weak Australian economic data",
            "RBA cutting rates or dovish tone",
            "Risk-OFF sentiment: recession fears, global crises",
            "Strong US Dollar (rising DXY / Fed hiking rates)",
        ],
        "narration": (
            "Conversely, AUD slash USD falls when commodities drop, "
            "when Australian data disappoints, "
            "when the RBA cuts rates or sounds dovish, "
            "during risk-off periods such as recessions or geopolitical crises, "
            "or when the US Dollar strengthens due to Fed rate hikes."
        ),
      },
      {
        "type": "table",
        "heading": "Best Trading Sessions for AUD/USD",
        "headers": ["Session", "Time UTC", "Quality"],
        "rows": [
            ["Asian Session",      "00:00 – 08:00", "High"],
            ["London Open",        "07:00 – 09:00", "Very High"],
            ["NY / London Overlap","13:00 – 17:00", "High"],
            ["Dead Zone",          "20:00 – 23:00", "Low — avoid"],
        ],
        "narration": (
            "AUD slash USD is most active during Asian hours since Australia is a Pacific economy. "
            "The London open at 7 AM UTC brings a volatility spike — very high quality. "
            "The New York London overlap from 1 PM to 5 PM UTC is also excellent. "
            "Avoid the dead zone from 8 PM to 11 PM UTC — low volume and poor price action."
        ),
      },
      {
        "type": "code",
        "heading": "Top-Down Timeframe Approach",
        "accent": ACCENT_BLUE,
        "lines": [
            "Monthly  →  Big picture Elliott Wave degree",
            "Weekly   →  Primary wave count & trend direction",
            "Daily    →  Wave sub-structure & trade planning",
            "4-Hour   →  Entry timing & MACD divergences",
            "1-Hour   →  Fine-tuned entry & stop placement",
            "",
            "# Golden Rule:",
            "→ Higher timeframe wave count is ALWAYS the boss",
            "→ Never fight the higher timeframe trend",
        ],
        "narration": (
            "We use a top-down approach. "
            "Start on the monthly chart for the big picture wave degree, "
            "then the weekly for primary trend direction, "
            "then the daily for wave sub-structure and planning, "
            "then the four-hour chart for MACD divergence entries, "
            "and finally the one-hour chart for precise entry and stop placement. "
            "The golden rule: the higher timeframe wave count is always the boss."
        ),
      },
    ],
  },

  # ── MODULE 2 ─────────────────────────────────────────────────────────────
  {
    "id": "02",
    "title": "Elliott Wave Theory Mastery",
    "subtitle": "Rules, guidelines, Fibonacci & practical wave counting",
    "slides": [
      {
        "type": "section",
        "heading": "The Core Concept",
        "bullets": [
            "Developed by Ralph Nelson Elliott in the 1930s",
            "Markets move in repetitive, fractal wave patterns",
            "Patterns are driven by crowd psychology",
            "Two wave types: Impulse (5 waves) and Corrective (3 waves)",
            "Complete cycle = 5 impulse waves + 3 corrective waves",
        ],
        "narration": (
            "Elliott Wave Theory was developed by Ralph Nelson Elliott in the 1930s. "
            "It states that financial markets move in repetitive, fractal wave patterns "
            "driven by collective human psychology. "
            "There are two types of waves: impulse waves that move with the trend in 5 waves, "
            "and corrective waves that move against the trend in 3 waves. "
            "The complete market cycle consists of 5 impulse waves followed by 3 corrective waves."
        ),
      },
      {
        "type": "code",
        "heading": "The 5-Wave Impulse Structure",
        "accent": ACCENT_BLUE,
        "lines": [
            "           3",
            "          / \\",
            "         /   \\",
            "        1     \\    5",
            "       / \\     \\  / \\",
            "      /   2     \\/   \\",
            "     /          4    \\",
            "  Start              End",
            "",
            "→ Wave 1: First move — few notice the new trend",
            "→ Wave 2: Deep pullback (50–61.8% of Wave 1)",
            "→ Wave 3: STRONGEST — where most money is made",
            "→ Wave 4: Shallow pullback (38.2% of Wave 3)",
            "→ Wave 5: Final push — MACD divergence forms here",
        ],
        "narration": (
            "The five-wave impulse structure is the foundation of Elliott Wave. "
            "Wave 1 is the initial move — few traders notice it. "
            "Wave 2 pulls back deeply, typically 50 to 61.8 percent of Wave 1, shaking out weak hands. "
            "Wave 3 is the strongest and most powerful wave — this is where the most money is made. "
            "Wave 4 is a shallower pullback, typically 38.2 percent of Wave 3. "
            "Wave 5 is the final push — and this is where MACD divergence almost always appears."
        ),
      },
      {
        "type": "slide_rule",
        "rule": "The 3 Hard Rules of Elliott Wave",
        "detail": (
            "Rule 1: Wave 2 NEVER retraces more than 100% of Wave 1\n"
            "Rule 2: Wave 3 is NEVER the shortest impulse wave\n"
            "Rule 3: Wave 4 NEVER overlaps Wave 1 territory"
        ),
        "narration": (
            "There are three hard rules in Elliott Wave that can never be broken. "
            "First: Wave 2 never retraces more than 100 percent of Wave 1 — "
            "it never goes below the start of Wave 1 in a bull move. "
            "Second: Wave 3 is never the shortest impulse wave — "
            "it is almost always the longest. "
            "Third: Wave 4 never overlaps Wave 1's price territory. "
            "If any of your wave counts violates these rules, the count is wrong. Start over."
        ),
      },
      {
        "type": "table",
        "heading": "Key Fibonacci Levels",
        "headers": ["Level", "Used For"],
        "rows": [
            ["38.2%",  "Wave 4 retracement; Take Profit 1"],
            ["50.0%",  "Wave 2 retracement"],
            ["61.8%",  "Wave 2 deep retrace — Golden Ratio"],
            ["100%",   "Wave C = Wave A; Wave 5 = Wave 1"],
            ["161.8%", "Wave 3 extension — most common"],
            ["261.8%", "Extended Wave 3 target"],
        ],
        "narration": (
            "Fibonacci is the mathematical backbone of Elliott Wave. "
            "38.2 percent is the most common Wave 4 retracement and your first profit target. "
            "50 percent is typical for Wave 2. "
            "61.8 percent — the Golden Ratio — is the deep Wave 2 retracement level. "
            "100 percent extension means Wave C equals Wave A, or Wave 5 equals Wave 1. "
            "The 161.8 percent extension is the most common Wave 3 target. "
            "Always draw Fibonacci from the start to the end of Wave 1 to project these levels."
        ),
      },
      {
        "type": "section",
        "heading": "Corrective Wave Patterns",
        "bullets": [
            "Zigzag (5-3-5): Sharp A down, partial B up, C equals A down",
            "Flat (3-3-5): A down, B near 100% retrace of A, C = A",
            "Triangle (3-3-3-3-3): A-B-C-D-E converging — appears as W4 or WB",
            "Complex: Double/Triple Threes — W-X-Y patterns",
            "After correction → new impulse begins in original direction",
        ],
        "narration": (
            "After a 5-wave impulse, price corrects in several possible patterns. "
            "A Zigzag is a sharp A-B-C where C typically equals A. "
            "A Flat has a Wave B that nearly retraces all of Wave A before C drops sharply. "
            "A Triangle forms five converging overlapping waves and usually appears as Wave 4 or Wave B. "
            "Complex corrections are double or triple three patterns labeled W-X-Y. "
            "In all cases, once the correction is complete, a new impulse wave begins in the original direction."
        ),
      },
      {
        "type": "section",
        "heading": "Practical Wave Counting — Step by Step",
        "accent": ACCENT_BLUE,
        "bullets": [
            "Step 1: Weekly chart — find the dominant swing high and low",
            "Step 2: Count 5 waves in the direction of trend, label 1-2-3-4-5",
            "Step 3: Use Fibonacci to validate — W2 at 50-61.8%, W3 at 161.8%",
            "Step 4: Daily chart — refine sub-waves within each major wave",
            "Step 5: 4H chart — look for MACD divergence at wave completion",
        ],
        "narration": (
            "Here is the practical wave counting process. "
            "Start on the weekly chart and find the most obvious swing high and low over the last 2 to 5 years. "
            "Count the five waves in the direction of the dominant trend and label them 1 through 5. "
            "Use Fibonacci to validate: Wave 2 should retrace 50 to 61.8 percent of Wave 1, "
            "and Wave 3 should extend to 161.8 percent of Wave 1. "
            "Drop to the daily chart to refine sub-waves, then to the 4-hour chart "
            "where you look for MACD divergence to time your entry."
        ),
      },
    ],
  },

  # ── MODULE 3 ─────────────────────────────────────────────────────────────
  {
    "id": "03",
    "title": "MACD Divergence Mastery",
    "subtitle": "Regular vs hidden divergence, quality filters & false signals",
    "slides": [
      {
        "type": "section",
        "heading": "What is the MACD?",
        "bullets": [
            "Moving Average Convergence Divergence — developed by Gerald Appel",
            "Settings we use: Fast 12 / Slow 26 / Signal 9",
            "MACD Line = 12 EMA minus 26 EMA",
            "Signal Line = 9-period EMA of the MACD line",
            "Histogram = MACD Line minus Signal Line",
        ],
        "narration": (
            "The MACD, or Moving Average Convergence Divergence, was developed by Gerald Appel. "
            "We use the standard settings: fast period 12, slow period 26, signal period 9. "
            "The MACD line is the 12 EMA minus the 26 EMA. "
            "The signal line is a 9-period EMA of the MACD line itself. "
            "The histogram shows the difference between the MACD line and the signal line — "
            "and this histogram is what we use to identify divergence."
        ),
      },
      {
        "type": "table",
        "heading": "The Four Types of Divergence",
        "headers": ["Type", "Price", "MACD", "Signal"],
        "rows": [
            ["Regular Bearish",  "Higher High ↑", "Lower High ↓",  "SELL — reversal"],
            ["Regular Bullish",  "Lower Low ↓",   "Higher Low ↑",  "BUY — reversal"],
            ["Hidden Bullish",   "Higher Low ↑",  "Lower Low ↓",   "BUY — continuation"],
            ["Hidden Bearish",   "Lower High ↓",  "Higher High ↑", "SELL — continuation"],
        ],
        "narration": (
            "There are four types of divergence. "
            "Regular bearish divergence occurs when price makes a higher high but MACD makes a lower high — "
            "this signals a reversal to the downside. "
            "Regular bullish divergence occurs when price makes a lower low but MACD makes a higher low — "
            "signaling a reversal to the upside. "
            "Hidden bullish divergence is price making a higher low while MACD makes a lower low — "
            "this is a trend continuation buy signal. "
            "Hidden bearish divergence is the opposite — a trend continuation sell signal. "
            "For our system, we primarily use regular divergence for reversals at Wave 5 and Wave C."
        ),
      },
      {
        "type": "table",
        "heading": "Divergence Quality Rating",
        "headers": ["Factor", "High Quality", "Low Quality"],
        "rows": [
            ["Timeframe",         "Daily / 4H / Weekly", "15-min / 5-min"],
            ["Gap between peaks", "Wide (20+ candles)",  "Narrow (<10 candles)"],
            ["Wave position",     "Wave 5 or Wave C end","Random wave position"],
            ["Fibonacci level",   "Price at key level",  "No Fibonacci nearby"],
            ["S/R confluence",    "Yes",                  "No"],
        ],
        "narration": (
            "Not all divergences are equal — you must rate the quality before trading. "
            "High quality divergence appears on the daily, four-hour, or weekly chart — "
            "not on 5 or 15 minute charts. "
            "The gap between the two price peaks should span at least 20 candles. "
            "The divergence must occur at a meaningful wave position — Wave 5 or the end of Wave C. "
            "Price should be at a key Fibonacci level, and ideally at a known support or resistance zone. "
            "Only trade divergences that score high on at least three of these five factors."
        ),
      },
      {
        "type": "section",
        "heading": "MACD at Key Elliott Wave Positions",
        "accent": ACCENT_GOLD,
        "bullets": [
            "End of Wave 5 → Regular BEARISH divergence → SELL",
            "End of Wave C → Regular BULLISH divergence → BUY",
            "End of Wave 2 → Bullish divergence or zero-line bounce → BUY",
            "End of Wave 4 → Hidden BULLISH divergence → BUY continuation",
            "End of Wave B → Bearish divergence → SELL Wave C begins",
        ],
        "narration": (
            "The power of our system comes from combining MACD divergence with Elliott Wave position. "
            "At the end of Wave 5, regular bearish divergence appears — this is our sell signal. "
            "At the end of Wave C, regular bullish divergence signals the start of a new impulse — our buy. "
            "At the end of Wave 2, bullish divergence or a MACD zero-line bounce confirms Wave 3 is starting. "
            "At the end of Wave 4, hidden bullish divergence confirms continuation into Wave 5. "
            "At the end of Wave B, bearish divergence warns that Wave C is about to begin."
        ),
      },
      {
        "type": "section",
        "heading": "The MACD Zero Line — Often Overlooked",
        "accent": ACCENT_BLUE,
        "bullets": [
            "Zero line = equilibrium between bulls and bears",
            "MACD crosses above zero → bullish momentum confirmed",
            "MACD holds above zero on pullback → bullish trend intact",
            "MACD crosses below zero → bearish momentum confirmed",
            "In strong Wave 3: MACD pulls back toward zero but does NOT cross — buy signal",
        ],
        "narration": (
            "The MACD zero line is often overlooked but extremely valuable. "
            "It represents the equilibrium point between bulls and bears. "
            "When MACD crosses above zero, bullish momentum is confirmed. "
            "If MACD pulls back toward zero during a correction but does not cross below it, "
            "the bullish trend is still intact — this is typical of a strong Wave 3. "
            "This zero-line bounce is one of the highest-confidence continuation signals in the system."
        ),
      },
    ],
  },
]


MODULES += [

  # ── MODULE 4 ─────────────────────────────────────────────────────────────
  {
    "id": "04",
    "title": "Combining Elliott Wave + MACD",
    "subtitle": "The two core setups and the 5-step analysis process",
    "slides": [
      {
        "type": "section",
        "heading": "Why Combine Both Systems?",
        "bullets": [
            "Elliott Wave alone: ambiguous — multiple valid counts exist",
            "MACD divergence alone: false signals without wave context",
            "Together: Wave tells WHERE, MACD tells WHEN",
            "Result: High-probability, high-reward trade setups",
            "Target: 3 to 6 quality setups per month on AUD/USD",
        ],
        "narration": (
            "Neither Elliott Wave nor MACD divergence is reliable on its own. "
            "Wave counts can be ambiguous, and divergences produce false signals. "
            "But combined, they become extremely powerful. "
            "Elliott Wave tells you where in the market cycle you are. "
            "MACD divergence tells you when that wave is ending. "
            "Together they produce three to six high-probability setups per month on AUD slash USD."
        ),
      },
      {
        "type": "code",
        "heading": "Setup A — Wave 5 Reversal Trade",
        "accent": ACCENT_RED,
        "lines": [
            "Conditions (ALL required):",
            "→ Clear 5-wave structure on Daily / 4H",
            "→ Wave 5 at Fibonacci target (61.8–100% of Wave 1)",
            "→ MACD bearish divergence on 4H or Daily",
            "→ Reversal candlestick (pin bar or engulfing)",
            "→ Price at known resistance level",
            "",
            "Entry:    After reversal candle close",
            "Stop:     Above Wave 5 high + buffer",
            "Target 1: Wave A = 38.2% retracement",
            "Target 2: Wave C = 61.8% retracement",
        ],
        "narration": (
            "Setup A is the Wave 5 reversal trade. "
            "All five conditions must be present. "
            "First, a clear 5-wave structure on the daily or 4-hour chart. "
            "Second, Wave 5 must have reached a Fibonacci target between 61.8 and 100 percent of Wave 1. "
            "Third, MACD bearish divergence on the 4-hour or daily chart. "
            "Fourth, a reversal candlestick such as a pin bar or bearish engulfing. "
            "Fifth, price at a known resistance level. "
            "Enter after the reversal candle closes. "
            "Stop goes above Wave 5 high. "
            "Target 1 is the Wave A level at 38.2 percent retracement. "
            "Target 2 is the Wave C level at 61.8 percent retracement."
        ),
      },
      {
        "type": "code",
        "heading": "Setup B — Wave C / Wave 2 Entry",
        "accent": ACCENT_GREEN,
        "lines": [
            "Conditions (ALL required):",
            "→ Prior 5-wave impulse clearly completed",
            "→ A-B-C correction complete at Fibonacci support/resistance",
            "→ Wave C = Wave A in length",
            "→ MACD regular divergence at Wave C",
            "→ Reversal candlestick confirmed",
            "",
            "Entry:    After reversal candle close",
            "Stop:     Below Wave C low (long) / above Wave C high (short)",
            "Target 1: New Wave 1 of impulse (100% of correction)",
            "Target 2: New Wave 3 = 161.8% extension",
        ],
        "narration": (
            "Setup B is the Wave C or Wave 2 entry — trading the start of a new impulse. "
            "The prior 5-wave impulse must be clearly complete. "
            "The A-B-C correction must be complete, with Wave C equaling Wave A in length "
            "and price reaching a key Fibonacci support or resistance level. "
            "MACD regular divergence must be present at the Wave C turning point. "
            "A reversal candlestick confirms the entry. "
            "Stop goes below the Wave C low for a long trade. "
            "Target 1 is the 100 percent extension of the correction. "
            "Target 2 is the 161.8 percent extension, which is where Wave 3 of the new impulse targets."
        ),
      },
      {
        "type": "section",
        "heading": "The 5-Step Analysis Process",
        "accent": ACCENT_BLUE,
        "bullets": [
            "Step 1 — Weekly: Establish macro wave count and trend direction",
            "Step 2 — Daily: Identify current wave position (3? 4? 5? C?)",
            "Step 3 — 4H: Look for MACD divergence at current position",
            "Step 4 — 1H: Time the exact entry candle and stop placement",
            "Step 5 — Execute: Pre-define stop, targets, position size FIRST",
        ],
        "narration": (
            "Follow this exact five-step process for every single trade. "
            "Step 1: Weekly chart to establish the macro wave count and dominant trend. "
            "Step 2: Daily chart to identify which specific wave we are currently in. "
            "Step 3: Four-hour chart to look for MACD divergence at that wave's completion zone. "
            "Step 4: One-hour chart to time the exact entry candle and place the stop. "
            "Step 5: Execute the trade only after defining your stop, all targets, "
            "and position size before clicking the button."
        ),
      },
    ],
  },

  # ── MODULE 5 ─────────────────────────────────────────────────────────────
  {
    "id": "05",
    "title": "Trade Management & Risk Framework",
    "subtitle": "Position sizing, stops, scaling out & hard limits",
    "slides": [
      {
        "type": "table",
        "heading": "The 1–2% Risk Rule",
        "headers": ["Account", "1% Risk", "2% Risk"],
        "rows": [
            ["$10,000",  "$100",   "$200"],
            ["$25,000",  "$250",   "$500"],
            ["$50,000",  "$500",   "$1,000"],
            ["$100,000", "$1,000", "$2,000"],
            ["$250,000", "$2,500", "$5,000"],
        ],
        "narration": (
            "The foundation of risk management is the 1 to 2 percent rule. "
            "Never risk more than 1 to 2 percent of your total account on any single trade. "
            "On a $10,000 account, that is $100 to $200 per trade. "
            "On a $50,000 account, $500 to $1,000. "
            "Start at 0.5 percent while learning. "
            "This protects you from a losing streak destroying your account. "
            "Ten consecutive losses at 1 percent risk equals only a 10 percent drawdown — "
            "something you can absolutely recover from."
        ),
      },
      {
        "type": "code",
        "heading": "Position Sizing Formula",
        "accent": ACCENT_GOLD,
        "lines": [
            "Formula:",
            "  Lots = Risk $ / (Stop Pips × Pip Value)",
            "",
            "AUD/USD Pip Values:",
            "  Standard Lot (100k) = $10 per pip",
            "  Mini Lot (10k)      = $1  per pip",
            "  Micro Lot (1k)      = $0.10 per pip",
            "",
            "Example: $50,000 account, 1% risk, 50-pip stop",
            "  Risk $ = $500",
            "  Lots   = $500 / (50 × $10) = 1.0 Standard Lot",
            "",
            "→ ALWAYS define stop first, THEN calculate size",
        ],
        "narration": (
            "The position sizing formula is: Lots equals risk dollars divided by "
            "stop pips multiplied by pip value. "
            "For AUD slash USD, one standard lot is worth 10 dollars per pip. "
            "Example: a $50,000 account risking 1 percent gives us $500 risk. "
            "With a 50-pip stop, that is $500 divided by 500, equals 1.0 standard lot. "
            "The critical rule: always define your stop first, then calculate position size. "
            "Never do it the other way around."
        ),
      },
      {
        "type": "code",
        "heading": "Scaling Out — The 40 / 40 / 20 Method",
        "accent": ACCENT_GREEN,
        "lines": [
            "Position: 1.0 Standard Lot",
            "",
            "Target 1 (38.2% / Wave A):",
            "  → Close 40% of position (0.4 lots)",
            "  → Move remaining stop to BREAKEVEN",
            "",
            "Target 2 (61.8% / Wave C start):",
            "  → Close 40% of position (0.4 lots)",
            "  → Trail stop using wave structure",
            "",
            "Target 3 (Full wave target):",
            "  → Close final 20% (0.2 lots)",
            "  → Maximum profit, minimum remaining risk",
        ],
        "narration": (
            "Never exit your entire position at one target. Use the 40-40-20 method. "
            "At Target 1, close 40 percent of the position and move your stop to breakeven. "
            "The trade is now risk-free on the remaining 60 percent. "
            "At Target 2, close another 40 percent and begin trailing your stop. "
            "Let the final 20 percent run to the full wave target for maximum reward. "
            "This method locks in profits early, removes emotional pressure, "
            "and still allows for home-run trades on the remaining position."
        ),
      },
      {
        "type": "section",
        "heading": "Hard Limits — Non-Negotiable",
        "accent": ACCENT_RED,
        "bullets": [
            "Daily max loss: 3% of account → Stop trading for the day",
            "After 3 consecutive losses → Stop trading for the day",
            "Monthly max drawdown: 8% → Stop, review journal, reduce size",
            "Minimum R:R on every trade: 1:2 (prefer 1:3 or better)",
            "No trading 2 hours before or after high-impact news",
        ],
        "narration": (
            "These hard limits are non-negotiable. "
            "If you lose 3 percent of your account in a single day, stop trading. Close your screens. "
            "After three consecutive losses, also stop for the day regardless of dollar amount. "
            "Your mindset is compromised after consecutive losses. "
            "Monthly maximum drawdown is 8 percent — if hit, stop trading for the month and review. "
            "Every trade must have a minimum risk-reward of 1 to 2, with 1 to 3 preferred. "
            "Never hold through high-impact news without a plan — the RBA and US NFP "
            "can move AUD slash USD 100 pips in seconds."
        ),
      },
    ],
  },

  # ── MODULE 6 ─────────────────────────────────────────────────────────────
  {
    "id": "06",
    "title": "The Million Dollar Plan",
    "subtitle": "Compounding, scaling protocol & the year-by-year roadmap",
    "slides": [
      {
        "type": "section",
        "heading": "The Compounding Philosophy",
        "bullets": [
            "$1,000,000 is a compounding target — NOT a lottery ticket",
            "Conservative target: 3% per month (achievable with this system)",
            "Based on 4 trades/month, 45% win rate, 1:2.5 average R:R",
            "Starting capital of $10K–$100K puts you in range",
            "The fastest traders blow up. Patient compounders win.",
        ],
        "narration": (
            "One million dollars is a compounding target, not a lucky trade. "
            "Our conservative target is 3 percent per month — "
            "achievable with just 4 trades per month at a 45 percent win rate "
            "and an average risk-reward of 1 to 2.5. "
            "Starting capital between $10,000 and $100,000 puts you well within range. "
            "The traders who blow up are chasing fast money. "
            "The traders who succeed are patient compounders who let math do the work."
        ),
      },
      {
        "type": "table",
        "heading": "Compounding to $1,000,000 (3% Monthly)",
        "headers": ["Start Capital", "Year 1", "Year 2", "Year 3", "Hits $1M"],
        "rows": [
            ["$10,000",  "$34,000",  "$115,000", "$393,000", "~4 yrs"],
            ["$25,000",  "$85,000",  "$289,000", "$983,000", "~3 yrs"],
            ["$50,000",  "$170,000", "$579,000", "$1M+",     "~2.7 yrs"],
            ["$100,000", "$340,000", "$1M+",     "—",        "~2 yrs"],
        ],
        "narration": (
            "Here is how compounding at 3 percent per month grows your account. "
            "Starting with $10,000, you reach $34,000 after year 1, "
            "$115,000 after year 2, $393,000 after year 3, and $1 million around year 4. "
            "Starting with $25,000 gets you there in about 3 years. "
            "With $50,000 you reach $1 million in roughly 2.7 years. "
            "And with $100,000 starting capital, compounding takes you to $1 million in approximately 2 years. "
            "These numbers assume consistent 3 percent monthly returns with no withdrawals."
        ),
      },
      {
        "type": "section",
        "heading": "The Scaling Protocol",
        "accent": ACCENT_BLUE,
        "bullets": [
            "Learning ($10K–$25K): 0.5% risk per trade — master the strategy",
            "Growing ($25K–$100K): 1.0% risk — prove consistency first",
            "Scaling ($100K–$500K): 1.5% risk — systems and discipline",
            "Advanced ($500K+): 1.5–2.0% — capital preservation is priority",
            "Rule: NEVER increase risk % before 3 consecutive profitable months",
        ],
        "narration": (
            "The scaling protocol is structured in four stages. "
            "During the learning phase with $10,000 to $25,000, risk only 0.5 percent per trade. "
            "Focus entirely on mastering strategy execution. "
            "In the growing phase, increase to 1 percent only after proving consistency. "
            "In the scaling phase above $100,000, move to 1.5 percent. "
            "Above $500,000, capital preservation becomes the priority. "
            "The non-negotiable rule: never increase your risk percentage "
            "before completing 3 consecutive profitable months."
        ),
      },
      {
        "type": "section",
        "heading": "Year-by-Year Roadmap",
        "accent": ACCENT_GOLD,
        "bullets": [
            "Year 0: Complete course, 3+ months demo, 30 documented trades",
            "Year 1 (live): Execute system correctly, target 2–3% monthly",
            "Year 2: Increase to 1% risk, master complex corrections, 3–4%/mo",
            "Year 3: Full mastery, 1–1.5% risk, approach the $1M target",
            "Key: Treat trading as a business from Day 1 — journal everything",
        ],
        "narration": (
            "The year-by-year roadmap is straightforward. "
            "Before going live, complete this course, spend at least 3 months on demo, "
            "and document 30 trades with full analysis. "
            "In Year 1 on live funds, focus entirely on correct execution and target 2 to 3 percent monthly. "
            "In Year 2, increase to 1 percent risk and develop mastery of complex corrections, targeting 3 to 4 percent monthly. "
            "By Year 3, you should have full system mastery at 1 to 1.5 percent risk, "
            "with the million-dollar target within reach. "
            "From day one, treat trading as a business: journal every trade, review weekly, improve constantly."
        ),
      },
    ],
  },

  # ── MODULE 7 ─────────────────────────────────────────────────────────────
  {
    "id": "07",
    "title": "Psychology & Discipline",
    "subtitle": "The mental edge that separates winners from losers",
    "slides": [
      {
        "type": "section",
        "heading": "The 5 Psychological Enemies",
        "accent": ACCENT_RED,
        "bullets": [
            "FOMO — entering trades without setup conditions because price is moving",
            "Revenge Trading — trading immediately after a loss to win it back",
            "Moving Your Stop — widening stops to avoid accepting a loss",
            "Exiting Winners Early — closing profitable trades before targets",
            "Overconfidence — increasing size or skipping rules after winners",
        ],
        "narration": (
            "90 percent of traders who have a good strategy still fail — because of psychology. "
            "The five psychological enemies are FOMO, revenge trading, moving your stop, "
            "exiting winners early, and overconfidence after a winning streak. "
            "FOMO causes late entries with poor risk-reward. "
            "Revenge trading turns small losses into account-destroying ones. "
            "Moving stops means accepting larger losses than planned. "
            "Exiting early destroys the risk-reward that makes the system profitable. "
            "And overconfidence after winners leads to oversized losses that wipe out multiple gains."
        ),
      },
      {
        "type": "section",
        "heading": "Process vs Outcome Thinking",
        "accent": ACCENT_BLUE,
        "bullets": [
            "WRONG: Judging a trade by whether it made money",
            "RIGHT: Judging a trade by whether you followed the process",
            "A perfect process trade can still lose — that is normal",
            "A broken-rules trade that wins builds dangerous habits",
            "Score yourself: Did I follow all 5 rules? Y/N for each",
        ],
        "narration": (
            "One of the most important mindset shifts in trading: "
            "judge yourself on process, not outcome. "
            "Any single trade can lose even if you followed every rule perfectly. "
            "The market has randomness — you cannot control outcomes of individual trades. "
            "You CAN control whether you followed your process. "
            "A trade that followed all rules and lost is a perfect trade. "
            "A trade that broke rules and won is a dangerous trade that builds bad habits. "
            "Over hundreds of trades, perfect process equals positive expectancy."
        ),
      },
      {
        "type": "code",
        "heading": "Think in R — Not Dollars",
        "accent": ACCENT_GOLD,
        "lines": [
            "R = 1 unit of risk (your stop loss amount in dollars)",
            "",
            "Instead of: 'I lost $500 today'",
            "Think:       'I lost 1R today'",
            "",
            "Instead of: 'I made $1,500'",
            "Think:       'I made 3R'",
            "",
            "→ Dollars trigger emotion",
            "→ R is a neutral performance metric",
            "→ Target: +2R to +4R per month consistently",
            "→ Track R in your journal alongside dollar P&L",
        ],
        "narration": (
            "Stop thinking in dollars — think in R. "
            "One R equals the dollar amount you risked on a trade. "
            "Instead of saying you lost $500, say you lost 1R. "
            "Instead of saying you made $1,500, say you made 3R. "
            "Dollars trigger strong emotions — euphoria when winning, devastation when losing. "
            "R is a neutral performance metric. "
            "A loss of 1R is simply a data point in your performance statistics. "
            "Target 2 to 4R per month consistently and let the dollars take care of themselves."
        ),
      },
      {
        "type": "section",
        "heading": "Routines That Build Discipline",
        "accent": ACCENT_GREEN,
        "bullets": [
            "Pre-market (15 min): Check news, update wave count, set alerts",
            "Post-trade (10 min): Journal immediately, screenshot chart",
            "Weekly review (30 min): P&L, best/worst decision, next week setup",
            "Losing streak protocol: Cut size 50%, best setups only, get a peer",
            "The 2-second rule: Before every click — setup or emotion?",
        ],
        "narration": (
            "Discipline is built through routines. "
            "Before each session: 15 minutes to check the economic calendar, "
            "update your wave count on all timeframes, and set price alerts. "
            "After each trade: 10 minutes to journal immediately and screenshot the chart. "
            "Every weekend: 30 minutes to review the week — calculate R performance, "
            "identify your best and worst decision, and plan the coming week. "
            "During losing streaks: cut size by 50 percent and only take maximum-confluence setups. "
            "And use the 2-second rule: before clicking any order button, pause 2 seconds "
            "and ask — is this a setup or is this emotion?"
        ),
      },
    ],
  },

  # ── MODULE 8 ─────────────────────────────────────────────────────────────
  {
    "id": "08",
    "title": "Live Trade Examples & Setups",
    "subtitle": "Full worked examples with entries, stops, targets & R:R",
    "slides": [
      {
        "type": "code",
        "heading": "Example Trade 1 — Setup A Wave 5 Sell",
        "accent": ACCENT_RED,
        "lines": [
            "Wave Count (Daily):",
            "  W1: 0.6200→0.6550  (+350 pips)",
            "  W2: 0.6550→0.6350  (57% retrace ✓)",
            "  W3: 0.6350→0.6980  (1.8× W1, longest ✓)",
            "  W4: 0.6980→0.6820  (25% retrace, alternation ✓)",
            "  W5: 0.6820→0.7085  (at 61.8% Fib extension ✓)",
            "",
            "4H MACD: Peak1 histogram +0.0048 → Peak2 +0.0029 ✓",
            "Entry: 0.7078 SELL  |  Stop: 0.7120 (42 pips)",
            "T1: 0.6820 (+258 pips) R:R = 6.1:1",
            "T2: 0.6580 (+498 pips) R:R = 11.9:1",
        ],
        "narration": (
            "Example Trade 1 is a classic Setup A Wave 5 sell on AUD slash USD. "
            "The daily chart shows a clear 5-wave impulse from 0.6200 to 0.7085. "
            "Wave 3 is the longest wave — the hard rule is satisfied. "
            "Wave 4 is shallow, alternating with the deeper Wave 2 — guideline confirmed. "
            "Wave 5 reaches the 61.8 percent Fibonacci extension target. "
            "On the 4-hour chart, MACD shows bearish divergence: "
            "the second price peak at 0.7085 is higher, but the MACD histogram is lower at 0.0029 versus 0.0048. "
            "We sell at 0.7078 after a bearish pin bar. Stop at 0.7120. "
            "Target 1 gives a 6.1 to 1 risk-reward. Target 2 gives nearly 12 to 1."
        ),
      },
      {
        "type": "code",
        "heading": "Example Trade 2 — Setup B Wave C Sell",
        "accent": ACCENT_RED,
        "lines": [
            "Context: 5-wave decline completed at 0.6150",
            "A-B-C counter-trend rally underway:",
            "  Wave A: 0.6150→0.6600  (+450 pips)",
            "  Wave B: 0.6600→0.6350  (56% retrace ✓)",
            "  Wave C: 0.6350→0.6812  (= Wave A length ✓)",
            "",
            "At 0.6812: price at 61.8% retrace of 5-wave decline ✓",
            "4H MACD bearish divergence confirmed ✓",
            "Entry: 0.6802 SELL  |  Stop: 0.6855 (53 pips)",
            "T1: 0.6600 (+202p) R:R = 3.8:1",
            "T2: 0.6350 (+452p) R:R = 8.5:1",
        ],
        "narration": (
            "Example Trade 2 is a Setup B — shorting the end of a counter-trend Wave C. "
            "A 5-wave decline completed at 0.6150. "
            "Price then rallied in an A-B-C correction. "
            "Wave C reaches 0.6812, which is exactly equal to Wave A in length, "
            "and also sits at the 61.8 percent retracement of the entire 5-wave decline — powerful confluence. "
            "The 4-hour MACD shows bearish divergence at this level. "
            "We sell at 0.6802 after a bearish engulfing candle. Stop at 0.6855. "
            "Target 1 at 0.6600 gives 3.8 to 1 risk-reward. "
            "Target 2 at 0.6350 gives 8.5 to 1."
        ),
      },
      {
        "type": "code",
        "heading": "Example Trade 3 — Setup B Wave 2 Buy",
        "accent": ACCENT_GREEN,
        "lines": [
            "Context: New bullish impulse started from 0.6200",
            "  Wave 1 up: 0.6200→0.6500  (+300 pips, clean impulse)",
            "",
            "Wave 2 pullback watching zone:",
            "  50.0% Fib = 0.6350",
            "  61.8% Fib = 0.6315",
            "",
            "Price pulls to 0.6320 — between 50% and 61.8% ✓",
            "4H MACD bullish divergence at 0.6320 ✓",
            "Entry: 0.6328 BUY  |  Stop: 0.6275 (53 pips)",
            "T1: 0.6500 (+172p) R:R = 3.2:1",
            "T2: Wave 3 at 161.8% ext = 0.6985  R:R = 12.4:1",
        ],
        "narration": (
            "Example Trade 3 is a Setup B buy — entering at the end of Wave 2 for the Wave 3 run. "
            "A new bullish impulse started from 0.6200. "
            "Wave 1 moved cleanly up to 0.6500 — 300 pips. "
            "We draw Fibonacci from 0.6200 to 0.6500. "
            "The 61.8 percent retracement is at 0.6315 and the 50 percent is at 0.6350. "
            "Price pulls back to 0.6320 — right in our target zone. "
            "The 4-hour MACD shows bullish divergence at this low. "
            "We buy at 0.6328 after a bullish pin bar. Stop at 0.6275. "
            "Target 1 back at Wave 1 high gives 3.2 to 1. "
            "Target 2, the Wave 3 extension at 161.8 percent, gives a massive 12.4 to 1 risk-reward."
        ),
      },
      {
        "type": "section",
        "heading": "Your Daily Trading Routine",
        "accent": ACCENT_GOLD,
        "bullets": [
            "Sunday: Update weekly wave count, set price alerts for the week",
            "Each morning (15 min): Check news, refine daily wave position",
            "When alert triggers: Run 5-step analysis, check confluence score",
            "Score 7+/12: Plan the trade. Score below 7: Watch and wait",
            "After every trade: Journal immediately — process before next trade",
        ],
        "narration": (
            "Here is your daily trading routine. "
            "Every Sunday, spend 20 minutes updating the weekly wave count "
            "and setting price alerts at key Fibonacci levels for the coming week. "
            "Each morning, spend 15 minutes checking the economic calendar "
            "and refining the daily wave position. "
            "When a price alert triggers, run the full 5-step analysis "
            "and check your confluence score on the 12-factor checklist. "
            "A score of 7 or more means plan the trade and execute. "
            "A score below 7 means watch and wait for better confirmation. "
            "After every trade, journal immediately — before doing anything else. "
            "This routine takes 20 minutes per day. Nothing more is needed."
        ),
      },
    ],
  },
]


# ── Video renderer ────────────────────────────────────────────────────────────
def build_slide(slide: dict) -> Image.Image:
    t = slide["type"]
    if t == "section":
        return slide_section(
            slide["heading"],
            slide["bullets"],
            accent=slide.get("accent", ACCENT_GOLD),
        )
    elif t == "table":
        return slide_table(
            slide["heading"],
            slide["headers"],
            slide["rows"],
            accent=slide.get("accent", ACCENT_GOLD),
        )
    elif t == "code":
        return slide_code(
            slide["heading"],
            slide["lines"],
            accent=slide.get("accent", ACCENT_GOLD),
        )
    elif t == "slide_rule":
        return slide_rule(slide["rule"], slide["detail"],
                          accent=slide.get("accent", ACCENT_RED))
    else:
        return slide_section(slide.get("heading", ""), slide.get("bullets", []))


def render_module(mod: dict):
    mid   = mod["id"]
    print(f"\n{'='*60}")
    print(f"  Rendering Module {mid}: {mod['title']}")
    print(f"{'='*60}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

    clips = []

    # ── Title slide ──────────────────────────────────────────────────────
    title_img  = slide_title(mod["title"], mod["subtitle"], f"Module {mid}")
    title_narr = (
        f"Module {mid}: {mod['title']}. "
        f"{mod['subtitle']}. "
        "Let's get started."
    )
    audio_path = TEMP_DIR / f"m{mid}_title.mp3"
    print(f"  [title] Generating audio…")
    dur = make_audio(title_narr, audio_path)
    dur = max(dur, 4.0)
    clips.append(img_to_clip(title_img, dur, audio_path))

    # ── Content slides ───────────────────────────────────────────────────
    for si, slide in enumerate(mod["slides"], start=1):
        print(f"  [slide {si}/{len(mod['slides'])}] {slide.get('heading','')[:50]}")
        img        = build_slide(slide)
        audio_path = TEMP_DIR / f"m{mid}_s{si}.mp3"
        narration  = slide.get("narration", slide.get("heading", ""))
        dur        = make_audio(narration, audio_path)
        dur        = max(dur, 5.0)
        clips.append(img_to_clip(img, dur, audio_path))

    # ── Outro slide ──────────────────────────────────────────────────────
    outro      = slide_title(
        "Module Complete",
        f"Module {mid} — {mod['title']}",
        "Next Module →",
    )
    outro_narr = (
        f"That concludes Module {mid}: {mod['title']}. "
        "Complete the action step in the course notes before moving on. "
        "See you in the next module."
    )
    audio_path = TEMP_DIR / f"m{mid}_outro.mp3"
    print(f"  [outro] Generating audio…")
    dur = make_audio(outro_narr, audio_path)
    dur = max(dur, 4.0)
    clips.append(img_to_clip(outro, dur, audio_path))

    # ── Concatenate & export ─────────────────────────────────────────────
    out_path = OUTPUT_DIR / f"module_{mid}_{mod['title'].replace(' ','_').replace('/','')[:40]}.mp4"
    print(f"  Concatenating {len(clips)} clips…")
    final = concatenate_videoclips(clips, method="compose")
    print(f"  Writing → {out_path}")
    final.write_videofile(
        str(out_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(TEMP_DIR / f"m{mid}_temp_audio.m4a"),
        remove_temp=True,
        logger=None,
    )
    final.close()
    for c in clips:
        c.close()
    print(f"  ✅ Module {mid} done → {out_path}")
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate AUD/USD course videos"
    )
    parser.add_argument(
        "--module", type=str, default="all",
        help="Module ID to render (e.g. 01, 03) or 'all' for every module"
    )
    args = parser.parse_args()

    targets = (
        MODULES if args.module == "all"
        else [m for m in MODULES if m["id"] == args.module.zfill(2)]
    )

    if not targets:
        print(f"Module '{args.module}' not found. Available: "
              + ", ".join(m["id"] for m in MODULES))
        raise SystemExit(1)

    print("\n🎬  AUD/USD Million Dollar Course — Video Generator")
    print(f"   Rendering {len(targets)} module(s)…\n")

    generated = []
    for mod in targets:
        path = render_module(mod)
        generated.append(path)

    print("\n" + "="*60)
    print("✅  All done! Videos saved to:")
    for p in generated:
        print(f"   {p}")
    print("="*60)
