"""Generate a single self-contained HTML file (double-click to open in browser)."""
import base64
import json
from pathlib import Path

BASE = Path(__file__).parent
PNG_PATH = BASE / "debug_vector_buildings_points.png"
JSON_PATH = BASE / "animation_data.json"
OUT_PATH = BASE / "居民出行轨迹动画.html"

HTML_HEAD = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>居民出行轨迹动画 · VAST 2022</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #0f1923 0%, #1a2a32 100%);
            color: #e8eef2;
            min-height: 100vh;
            padding: 20px;
        }
        .header { max-width: 1600px; margin: 0 auto 16px; }
        h1 { font-size: 1.4rem; font-weight: 600; margin-bottom: 4px; }
        .subtitle { font-size: 0.85rem; color: #8aa4b4; }
        .controls {
            max-width: 1600px; margin: 0 auto 16px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 14px; padding: 14px 18px;
            display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
        }
        .ctrl-group {
            display: flex; align-items: center; gap: 8px;
            background: rgba(0,0,0,0.25); padding: 6px 12px;
            border-radius: 20px; font-size: 0.85rem;
        }
        label { color: #a0b8c8; white-space: nowrap; }
        select { background: #0d1520; color: #fff; border: 1px solid #3a5566; border-radius: 8px; padding: 5px 10px; cursor: pointer; }
        button {
            background: #2d6a4f; color: #fff; border: none; border-radius: 20px;
            padding: 8px 18px; font-size: 0.9rem; font-weight: 600; cursor: pointer;
        }
        button:hover { background: #40916c; }
        button.secondary { background: #3a5068; }
        button.secondary:hover { background: #4a6888; }
        .time-display { font-family: Consolas, monospace; font-size: 0.95rem; color: #7ec8a4; min-width: 200px; }
        .maps { max-width: 1600px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        @media (max-width: 1100px) { .maps { grid-template-columns: 1fr; } }
        .map-panel {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px; overflow: hidden;
        }
        .map-header {
            padding: 10px 14px; background: rgba(0,0,0,0.3);
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .map-header h2 { font-size: 1rem; font-weight: 600; }
        .trip-info { font-size: 0.75rem; color: #8aa4b4; max-width: 55%; text-align: right; }
        canvas { display: block; width: 100%; height: auto; background: #eef2e6; }
        .legend {
            max-width: 1600px; margin: 16px auto 0;
            display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.78rem; color: #9ab;
        }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .legend-dot { width: 14px; height: 4px; border-radius: 2px; }
        .status-bar { max-width: 1600px; margin: 10px auto 0; font-size: 0.8rem; color: #6a8898; }
    </style>
</head>
<body>
<div class="header">
    <h1>居民出行轨迹动画</h1>
    <p class="subtitle">独立版 · 双击即可打开 · 居民 35 &amp; 195 出行轨迹</p>
</div>

<div class="controls">
    <button id="playBtn">▶ 播放</button>
    <button id="restartBtn" class="secondary">↺ 重播</button>
    <div class="ctrl-group">
        <label>日期</label>
        <select id="dateSelect"></select>
    </div>
    <div class="ctrl-group">
        <label>速度</label>
        <input type="range" id="speedRange" min="1" max="20" step="1" value="5">
        <span id="speedLabel">5×</span>
    </div>
    <div class="time-display" id="globalTime">--:--:--</div>
    <div class="ctrl-group" id="durationHint" style="color:#7ec8a4; font-size:0.8rem;"></div>
</div>

<div class="maps">
    <div class="map-panel">
        <div class="map-header">
            <h2>居民 35</h2>
            <div class="trip-info" id="info35">等待播放...</div>
        </div>
        <canvas id="canvas35" width="1514" height="1570"></canvas>
    </div>
    <div class="map-panel">
        <div class="map-header">
            <h2>居民 195</h2>
            <div class="trip-info" id="info195">等待播放...</div>
        </div>
        <canvas id="canvas195" width="1514" height="1570"></canvas>
    </div>
</div>

<div class="legend">
    <div class="legend-item"><span class="legend-dot" style="background:#FF6B6B"></span>通勤上班</div>
    <div class="legend-item"><span class="legend-dot" style="background:#4ECDC4"></span>外出用餐</div>
    <div class="legend-item"><span class="legend-dot" style="background:#FFE66D"></span>社交娱乐</div>
    <div class="legend-item"><span class="legend-dot" style="background:#FF9F4A"></span>用餐返回</div>
    <div class="legend-item"><span class="legend-dot" style="background:#9B5DE5"></span>回家</div>
    <div class="legend-item"><span style="color:#ffd966">●</span> 当前位置</div>
</div>
<p class="status-bar" id="statusBar">正在加载...</p>

<script>
"""

HTML_JS = r"""
const MAP_W = 1514, MAP_H = 1570;
const PURPOSE_COLORS = {
    "Work/Home Commute": "#FF6B6B",
    "Eating": "#4ECDC4",
    "Recreation (Social Gathering)": "#FFE66D",
    "Coming Back From Restaurant": "#FF9F4A",
    "Going Back to Home": "#9B5DE5",
    "default": "#AAAAAA"
};
const PURPOSE_LABELS = {
    "Work/Home Commute": "通勤上班",
    "Eating": "外出用餐",
    "Recreation (Social Gathering)": "社交娱乐",
    "Coming Back From Restaurant": "用餐返回",
    "Going Back to Home": "回家",
    "default": "出行"
};
const LINE_WIDTH = 6;
const REAL_TO_ANIM = 60 / 1.5;
const MIN_SEGMENT_MS = 2000;
const MAX_SEGMENT_MS = 12000;
const PAUSE_MS = 600;
const PARTICIPANTS = ["35", "195"];
const canvases = {}, ctxs = {};
let animData = null, bgImage = null;
let playing = false, animStart = 0, savedElapsed = 0, totalDuration = 0;
let dayTrips = {}, rafId = null, cachedAnimators = {};

function segmentAnimMs(realDurationMs) {
    const scaled = realDurationMs / REAL_TO_ANIM;
    return Math.min(Math.max(scaled, MIN_SEGMENT_MS), MAX_SEGMENT_MS);
}

class Animator {
    constructor(trips) {
        this.events = [];
        let offset = 0;
        for (const t of trips) {
            const travelMs = segmentAnimMs(t.durationMs);
            this.events.push({ type: "travel", trip: t, startMs: offset, endMs: offset + travelMs, travelMs });
            offset += travelMs + PAUSE_MS;
        }
        this.totalMs = Math.max(offset - PAUSE_MS, 0);
    }
    getState(elapsed) {
        const completed = [];
        let current = null, x = 0, y = 0;
        if (!this.events.length) return { x, y, completed, current };
        x = this.events[0].trip.startPx;
        y = this.events[0].trip.startPy;
        for (const ev of this.events) {
            if (elapsed >= ev.endMs) {
                completed.push(ev.trip);
                x = ev.trip.endPx; y = ev.trip.endPy;
            } else if (elapsed >= ev.startMs) {
                current = ev.trip;
                const p = (elapsed - ev.startMs) / ev.travelMs;
                const ease = p < 0.5 ? 2*p*p : 1 - Math.pow(-2*p+2,2)/2;
                x = ev.trip.startPx + (ev.trip.endPx - ev.trip.startPx) * ease;
                y = ev.trip.startPy + (ev.trip.endPy - ev.trip.startPy) * ease;
                break;
            } else break;
        }
        return { x, y, completed, current };
    }
}

function initCanvases() {
    for (const pid of PARTICIPANTS) {
        canvases[pid] = document.getElementById("canvas" + pid);
        ctxs[pid] = canvases[pid].getContext("2d");
    }
}

function drawBackground(ctx) {
    ctx.clearRect(0, 0, MAP_W, MAP_H);
    if (bgImage && bgImage.complete) ctx.drawImage(bgImage, 0, 0, MAP_W, MAP_H);
    else { ctx.fillStyle = "#eef2e6"; ctx.fillRect(0, 0, MAP_W, MAP_H); }
}

function purposeLabel(purpose) {
    return PURPOSE_LABELS[purpose] || PURPOSE_LABELS.default;
}

function drawArrow(ctx, x1, y1, x2, y2, color) {
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
    ctx.strokeStyle = color; ctx.lineWidth = LINE_WIDTH; ctx.lineCap = "round";
    ctx.globalAlpha = 0.9; ctx.stroke(); ctx.globalAlpha = 1;
    const angle = Math.atan2(y2-y1, x2-x1), hl = 14;
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - hl*Math.cos(angle-0.35), y2 - hl*Math.sin(angle-0.35));
    ctx.lineTo(x2 - hl*Math.cos(angle+0.35), y2 - hl*Math.sin(angle+0.35));
    ctx.closePath(); ctx.fillStyle = color; ctx.globalAlpha = 0.9; ctx.fill(); ctx.globalAlpha = 1;
}

function drawPurposeLabel(ctx, x, y, purpose, color, large) {
    const text = purposeLabel(purpose);
    const fontSize = large ? 15 : 12;
    const padX = 8, padY = 5;
    ctx.font = "bold " + fontSize + "px Microsoft YaHei, Segoe UI, sans-serif";
    const tw = ctx.measureText(text).width;
    const bw = tw + padX * 2, bh = fontSize + padY * 2;
    let lx = x + 14, ly = y - bh - 10;
    if (lx + bw > MAP_W - 4) lx = x - bw - 14;
    if (ly < 4) ly = y + 16;
    if (lx < 4) lx = 4;
    ctx.fillStyle = "rgba(255,255,255,0.92)";
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.roundRect(lx, ly, bw, bh, 6);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#1a1a1a";
    ctx.textBaseline = "middle";
    ctx.fillText(text, lx + padX, ly + bh / 2);
}

function drawMidpointLabel(ctx, trip, color) {
    const mx = (trip.startPx + trip.endPx) / 2;
    const my = (trip.startPy + trip.endPy) / 2;
    drawPurposeLabel(ctx, mx, my, trip.purpose, color, false);
}

function drawFrame(animators, elapsed) {
    for (const pid of PARTICIPANTS) {
        const ctx = ctxs[pid], state = animators[pid].getState(elapsed);
        drawBackground(ctx);
        for (const trip of state.completed) {
            const c = PURPOSE_COLORS[trip.purpose] || PURPOSE_COLORS.default;
            drawArrow(ctx, trip.startPx, trip.startPy, trip.endPx, trip.endPy, c);
            drawMidpointLabel(ctx, trip, c);
        }
        if (state.current) {
            const t = state.current, c = PURPOSE_COLORS[t.purpose] || PURPOSE_COLORS.default;
            drawArrow(ctx, t.startPx, t.startPy, state.x, state.y, c);
            const pulse = 1 + 0.3 * Math.sin(Date.now()/150);
            ctx.beginPath(); ctx.arc(state.x, state.y, 11*pulse, 0, Math.PI*2);
            ctx.fillStyle = "rgba(255,217,102,0.35)"; ctx.fill();
            ctx.beginPath(); ctx.arc(state.x, state.y, 7, 0, Math.PI*2);
            ctx.fillStyle = "#ffd966"; ctx.strokeStyle = "#333"; ctx.lineWidth = 2; ctx.fill(); ctx.stroke();
            drawPurposeLabel(ctx, state.x, state.y, t.purpose, c, true);
            document.getElementById("info"+pid).textContent =
                purposeLabel(t.purpose) + " · " + t.startTime.slice(11,16) + " → " + t.endTime.slice(11,16);
        } else if (state.completed.length) {
            document.getElementById("info"+pid).textContent =
                "已完成 " + state.completed.length + "/" + dayTrips[pid].length + " 段行程";
        }
    }
}

function getSpeed() { return parseFloat(document.getElementById("speedRange").value); }

function formatDuration(ms) {
    const sec = Math.round(ms / 1000);
    if (sec < 60) return sec + " 秒";
    return Math.floor(sec / 60) + " 分 " + (sec % 60) + " 秒";
}

function updateDurationHint() {
    rebuildAnimators();
    document.getElementById("durationHint").textContent =
        "预计时长（" + getSpeed() + "×）：" + formatDuration(totalDuration / getSpeed());
}

function rebuildAnimators() {
    cachedAnimators = {};
    for (const pid of PARTICIPANTS) cachedAnimators[pid] = new Animator(dayTrips[pid]);
    totalDuration = Math.max(...PARTICIPANTS.map(p => cachedAnimators[p].totalMs));
}

function animateFrame(timestamp) {
    if (!playing) return;
    if (!animStart) animStart = timestamp - savedElapsed / getSpeed();
    const speed = getSpeed(), elapsed = (timestamp - animStart) * speed;
    const animators = cachedAnimators;
    if (elapsed >= totalDuration) {
        drawFrame(animators, totalDuration);
        playing = false;
        document.getElementById("playBtn").textContent = "▶ 播放";
        document.getElementById("globalTime").textContent = "播放完成";
        return;
    }
    drawFrame(animators, elapsed);
    let displayTime = "";
    for (const pid of PARTICIPANTS) {
        for (const ev of animators[pid].events) {
            if (elapsed >= ev.startMs && elapsed < ev.endMs) {
                const t0 = new Date(ev.trip.startTime), t1 = new Date(ev.trip.endTime);
                const frac = (elapsed - ev.startMs) / ev.travelMs;
                const cur = new Date(t0.getTime() + frac * (t1.getTime() - t0.getTime()));
                displayTime = cur.toISOString().slice(0,19).replace("T"," ");
                break;
            }
        }
        if (displayTime) break;
    }
    document.getElementById("globalTime").textContent = displayTime || "播放中...";
    rafId = requestAnimationFrame(animateFrame);
}

function startPlay() {
    if (playing) {
        playing = false;
        savedElapsed = (performance.now() - animStart) * getSpeed();
        cancelAnimationFrame(rafId);
        document.getElementById("playBtn").textContent = "▶ 播放";
        return;
    }
    playing = true;
    document.getElementById("playBtn").textContent = "⏸ 暂停";
    if (savedElapsed >= totalDuration) { animStart = 0; savedElapsed = 0; }
    rafId = requestAnimationFrame(animateFrame);
}

function restart() {
    playing = false; cancelAnimationFrame(rafId);
    animStart = 0; savedElapsed = 0;
    document.getElementById("playBtn").textContent = "▶ 播放";
    document.getElementById("globalTime").textContent = "--:--:--";
    rebuildAnimators();
    for (const pid of PARTICIPANTS) {
        document.getElementById("info"+pid).textContent = dayTrips[pid].length + " 段行程待播放";
    }
    updateDurationHint();
    drawFrame(cachedAnimators, 0);
}

function loadDay(date) {
    playing = false; cancelAnimationFrame(rafId);
    animStart = 0; savedElapsed = 0;
    document.getElementById("playBtn").textContent = "▶ 播放";
    dayTrips = {};
    for (const pid of PARTICIPANTS) {
        dayTrips[pid] = animData.participants[pid].trips.filter(t => t.date === date);
        document.getElementById("info"+pid).textContent = dayTrips[pid].length + " 段行程 · " + date;
    }
    restart();
}

function populateDates() {
    const dates = new Set();
    for (const pid of PARTICIPANTS) animData.participants[pid].dates.forEach(d => dates.add(d));
    const sorted = [...dates].sort();
    const sel = document.getElementById("dateSelect");
    sel.innerHTML = sorted.map(d => '<option value="'+d+'">'+d+'</option>').join("");
    sel.value = sorted[0] || "";
    sel.addEventListener("change", () => loadDay(sel.value));
}

function loadData() {
    initCanvases();
    animData = EMBEDDED_ANIM_DATA;
    bgImage = new Image();
    bgImage.onload = function() {
        populateDates();
        loadDay(document.getElementById("dateSelect").value);
        document.getElementById("statusBar").textContent =
            "数据已加载 · 居民35: " + animData.participants["35"].tripCount +
            " 段 · 居民195: " + animData.participants["195"].tripCount + " 段 · 点击播放";
    };
    bgImage.onerror = function() {
        document.getElementById("statusBar").textContent = "底图加载失败";
        populateDates();
        loadDay(document.getElementById("dateSelect").value);
    };
    bgImage.src = EMBEDDED_MAP_IMAGE;
}

document.getElementById("playBtn").addEventListener("click", startPlay);
document.getElementById("restartBtn").addEventListener("click", restart);
document.getElementById("speedRange").addEventListener("input", e => {
    document.getElementById("speedLabel").textContent = e.target.value + "×";
    updateDurationHint();
});

loadData();
</script>
</body>
</html>
"""


def main():
    if not JSON_PATH.exists():
        raise SystemExit("请先运行 build_animation.py 生成 animation_data.json")

    print("Reading PNG...")
    png_b64 = base64.b64encode(PNG_PATH.read_bytes()).decode("ascii")
    map_var = f'const EMBEDDED_MAP_IMAGE = "data:image/png;base64,{png_b64}";'

    print("Reading JSON...")
    anim_data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    json_str = json.dumps(anim_data, ensure_ascii=False, separators=(",", ":"))
    data_var = f"const EMBEDDED_ANIM_DATA = {json_str};"

    print("Writing HTML...")
    content = HTML_HEAD + map_var + "\n" + data_var + "\n" + HTML_JS
    OUT_PATH.write_text(content, encoding="utf-8")

    size_mb = OUT_PATH.stat().st_size / (1024 * 1024)
    print(f"Done: {OUT_PATH}")
    print(f"File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
