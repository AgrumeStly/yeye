# S3 调试图传：车线检测 + 标注叠加 + 网页遥测
# 板上路径：/sdcard/qoder_scripts/wifi_debug_track.py（本地为副本）
# 算法来自 09_lane_track.py（桌面 328 帧验证过），运行分辨率 320x240 灰度。
# 本脚本只显示 K230 的判定，不接 UART、不发命令，不代表车已执行。
# 停止：MCP canmv_stop_script 或 IDE 停止按钮（循环里有 os.exitpoint()）。
import gc, json, os, socket, time
import network
from media.sensor import Sensor
from media.display import Display

# ---------- 可调参数 ----------
W, H = 320, 240
JPEG_Q = 65
STREAM_FPS = 12        # 带检测的推流帧率；S4 再压测
PORT = 8080
SSID_KEY = b'kunkun'   # 按关键字找热点，用扫描到的原始 ssid 字节连
PASSWORD = '<REDACTED_LOCAL_HOTSPOT_PASSWORD>'
SEND_CHUNK = 8192
STALL_MS = 5000

# 检测参数（与 09_lane_track.py 一致）
TILE_TOP, TILE_H, TILES = 40, 22, 9
OFF = 22
DARK_FRAC_MAX = 0.45
MIN_AREA, MIN_H, MAX_W, MAX_DENSITY = 60, 10, 130, 0.75
LINK_TOL = 38
HZ_MARGIN = 6
HZ_STRIPS = 8
Y_REF = 200            # 读偏移的那一行

TELEM = {'valid': 0, 'pts0': 0, 'pts1': 0, 'x200': -1, 'err': 0,
         'slope': 0.0, 'conf': 0, 'det_ms': 0, 'enc_ms': 0,
         'fps': 0.0, 'ts': 0, 'frames': 0, 'age_ms': 0}

# ---------- WiFi ----------
def wifi_connect():
    w = network.WLAN(network.STA_IF)
    w.active(True)
    if w.isconnected():
        print('[WiFi] 已连接:', w.ifconfig()[0])
        return w.ifconfig()[0]
    aps = w.scan()
    target = None
    for a in aps:
        if SSID_KEY in getattr(a, 'ssid', b''):
            target = a
            break
    if target is None:
        raise RuntimeError('扫描不到热点，请确认手机热点已开')
    print('[WiFi] 找到热点:', target.ssid, 'rssi:', target.rssi)
    w.connect(target.ssid, PASSWORD)
    for _ in range(50):
        if w.isconnected():
            break
        time.sleep_ms(200)
    if not w.isconnected():
        raise RuntimeError('WiFi 连接失败')
    ip = w.ifconfig()[0]
    print('[WiFi] 连接成功 IP:', ip)
    return ip

# ---------- 车道检测（直接沿用探针算法） ----------
def med(vals):
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return 0.0
    return float(s[n // 2]) if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0

def strip_mean(img, x, y0, h):
    return img.get_statistics(roi=(max(0, x - 12), y0, 24, h)).mean()

def horizon_line(img):
    pts = []
    w = W // HZ_STRIPS
    for s in range(HZ_STRIPS):
        x = s * w + w // 2
        prof = [strip_mean(img, x, y, 6) for y in range(4, 170, 6)]
        lo = min(prof)
        hi = max(prof)
        if hi - lo < 25:
            continue
        thr = lo + 0.55 * (hi - lo)
        for i in range(len(prof) - 2):
            if prof[i] < thr and (prof[i + 1] + prof[i + 2]) / 2.0 > thr:
                pts.append((x, 4 + (i + 1) * 6))
                break
    if len(pts) < 3:
        return None
    n = float(len(pts))
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    den = n * sxx - sx * sx
    if abs(den) < 1e-6:
        return None
    k = (n * sxy - sx * sy) / den
    return (k, (sy - k * sx) / n)

def tile_cands(img, y, hz):
    roi = (0, y, W, TILE_H)
    thr = img.get_statistics(roi=roi).mean() - OFF
    if thr <= 0:
        return []
    dark = 0
    blobs = img.find_blobs([(0, int(thr))], roi=roi, x_stride=1, y_stride=1,
                           pixels_threshold=MIN_AREA, area_threshold=MIN_AREA,
                           merge=True, margin=2)
    for b in blobs:
        dark += b.pixels()
    if dark > DARK_FRAC_MAX * W * TILE_H:
        return []
    out = []
    for b in blobs:
        if b.w() > MAX_W or b.h() < MIN_H:
            continue
        den = b.density() if hasattr(b, 'density') else b.pixels() / float(b.w() * b.h())
        if den > MAX_DENSITY:
            continue
        cx = b.cx()
        cy = b.cy()
        if hz is not None and cy < hz[0] * cx + hz[1] + HZ_MARGIN:
            continue
        out.append((float(cy), float(cx), b.w(), b.h(), b.pixels()))
    return out

def fit_line(pts):
    n = float(len(pts))
    sy = sum(p[0] for p in pts)
    sx = sum(p[1] for p in pts)
    syy = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    den = n * syy - sy * sy
    if abs(den) < 1e-6:
        return None
    k = (n * sxy - sy * sx) / den
    return (k, (sx - k * sy) / n)

def refit(pts, tol=LINK_TOL):
    f = fit_line(pts)
    if f is None or len(pts) < 3:
        return f, pts
    keep = [p for p in pts if abs(p[1] - (f[0] * p[0] + f[1])) <= tol]
    return (fit_line(keep) if len(keep) >= 2 else f), keep

def predict(f, y):
    return f[0] * y + f[1] if f else None

def track(img, hz):
    acc = [[], []]
    mdl = [None, None]
    for i in range(TILES - 1, -1, -1):
        y = TILE_TOP + i * TILE_H
        c = tile_cands(img, y, hz)
        if not c:
            continue
        used = [False] * len(c)
        ymid = y + TILE_H / 2.0
        for k in (0, 1):
            if mdl[k] is not None:
                py, tol = predict(mdl[k], ymid), LINK_TOL
            elif acc[k]:
                py, tol = acc[k][-1][1], int(LINK_TOL * 1.6)
            else:
                py = None
            if py is None:
                av = [j for j in range(len(c)) if not used[j]]
                if not av:
                    continue
                j = max(av, key=lambda q: c[q][4])
            else:
                j, bd = -1, tol
                for q, p in enumerate(c):
                    if not used[q] and abs(p[1] - py) < bd:
                        bd, j = abs(p[1] - py), q
                if j < 0:
                    continue
            acc[k].append(c[j])
            used[j] = True
    for k in (0, 1):
        if len(acc[k]) >= 3:
            mdl[k], acc[k] = refit(acc[k])
    return acc, mdl

# ---------- 单帧：检测 + 标注 + 遥测 ----------
def analyze(img):
    t0 = time.ticks_ms()
    hz = horizon_line(img)
    acc, mdl = track(img, hz)
    if len(acc[0]) < len(acc[1]):
        acc = [acc[1], acc[0]]
        mdl = [mdl[1], mdl[0]]
    valid = mdl[0] is not None and len(acc[0]) >= 3
    x200 = 0
    slope = 0.0
    conf = 0
    if valid:
        x200 = int(max(0, min(W - 1, predict(mdl[0], Y_REF))))
        slope = mdl[0][0]
        errs = [abs(p[1] - predict(mdl[0], p[0])) for p in acc[0]]
        resid = med(errs)
        # 临时的置信度启发式：点数越多、残差越小越高；等 V-02 定正式口径
        conf = int(max(0, min(100, 20 + 8 * len(acc[0]) - 2 * resid)))
        del errs, resid
    det_ms = time.ticks_diff(time.ticks_ms(), t0)

    # 叠加：点、拟合线、地平线、中心线、Y_REF 行
    for k, col in ((0, 255), (1, 180)):
        for p in acc[k]:
            img.draw_cross(int(p[1]), int(p[0]), color=col, size=4, thickness=1)
        if mdl[k] is not None and len(acc[k]) >= 2:
            img.draw_line(int(predict(mdl[k], TILE_TOP)), TILE_TOP,
                          int(predict(mdl[k], H - 3)), H - 3, color=col, thickness=1)
    if hz:
        img.draw_line(0, int(hz[1]), W - 1, int(hz[0] * (W - 1) + hz[1]), color=110, thickness=1)
    img.draw_line(W // 2, TILE_TOP, W // 2, H - 1, color=70, thickness=1)
    img.draw_line(0, Y_REF, W - 1, Y_REF, color=70, thickness=1)
    if valid:
        img.draw_circle(x200, Y_REF, 6, color=255, thickness=1)

    # 顶部信息条 + 丢线大提示
    img.draw_rectangle(0, 0, W, 34, color=0, fill=True)
    err = int(max(-1000, min(1000, (x200 - W // 2) / (W / 2.0) * 1000))) if valid else 0
    img.draw_string_advanced(3, 1, 14, 'v%d pts=%d/%d x=%d err=%+d' % (
        1 if valid else 0, len(acc[0]), len(acc[1]), x200, err), color=255)
    img.draw_string_advanced(3, 17, 14, 'conf=%d slope=%.2f det=%dms' % (conf, slope, det_ms), color=255)
    if not valid:
        img.draw_rectangle(70, 100, 180, 34, color=0, fill=True)
        img.draw_string_advanced(84, 106, 24, 'LOST LINE', color=255)

    TELEM['valid'] = 1 if valid else 0
    TELEM['pts0'] = len(acc[0])
    TELEM['pts1'] = len(acc[1])
    TELEM['x200'] = x200 if valid else -1
    TELEM['err'] = err
    TELEM['slope'] = round(slope, 2)
    TELEM['conf'] = conf
    TELEM['det_ms'] = det_ms
    TELEM['ts'] = time.ticks_ms()
    TELEM['frames'] += 1
    return img

# ---------- 相机 ----------
def camera_init():
    sensor = Sensor(id=2)        # CSI2 = 当前摄像头座子
    sensor.reset()
    sensor.set_framesize(width=W, height=H)
    sensor.set_pixformat(Sensor.GRAYSCALE)   # 检测用灰度，显示也是灰度
    Display.init(Display.VIRT, width=W, height=H, fps=30, to_ide=False)
    sensor.run()
    for _ in range(20):
        sensor.snapshot()
    return sensor

# ---------- HTTP 工具 ----------
def send_all(client, data):
    view = memoryview(data)
    off = 0
    deadline = time.ticks_add(time.ticks_ms(), STALL_MS)
    while off < len(view):
        try:
            sent = client.send(view[off:off + SEND_CHUNK])
            if sent:
                off += sent
                deadline = time.ticks_add(time.ticks_ms(), STALL_MS)
                continue
        except OSError as e:
            if e.errno not in (11, 110):
                raise
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            raise OSError(110)
        os.exitpoint()
        time.sleep_ms(1)

def send_response(client, status, ctype, body):
    head = ('HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %d\r\n'
            'Cache-Control: no-store\r\nConnection: close\r\n\r\n') % (status, ctype, len(body))
    send_all(client, head.encode())
    if body:
        send_all(client, body)

def read_path(client):
    req = bytearray()
    deadline = time.ticks_add(time.ticks_ms(), 2000)
    client.setblocking(False)
    while len(req) < 4096:
        chunk = client.recv(min(256, 4096 - len(req)))
        if chunk:
            req.extend(chunk)
            if req.find(b'\r\n\r\n') >= 0 or req.find(b'\n\n') >= 0:
                break
        elif time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            raise OSError(110)
        else:
            os.exitpoint()
            time.sleep_ms(10)
    line = bytes(req).split(b'\r\n', 1)[0].split()
    if len(line) < 2:
        return '/'
    return line[1].decode().split('?', 1)[0]

# ---------- 页面 ----------
# 单线程服务器：/stream 连接期间不轮询 JSON（会被排队）。
# 关键遥测已画在画面顶部信息条里；/telem.json 留给无流时 curl 诊断。
INDEX_HTML = ("""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>椰椰杯调试图传 S3</title>
<style>
html,body{margin:0;background:#111;color:#eee;font-family:sans-serif}
header{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:#1c1c1c;font-size:14px}
button{background:#2a2a2a;color:#eee;border:1px solid #555;border-radius:6px;padding:5px 10px}
main{display:flex;align-items:center;justify-content:center;height:calc(100% - 44px)}
img{width:100%;max-width:640px;object-fit:contain}
img.flip{transform:rotate(180deg)}
</style></head><body>
<header><span>椰椰杯调试 S3 · K230 判定（未接 UART）</span><button id="r">旋转</button></header>
<main><img id="s" alt="live"></main>
<script>
var s=document.getElementById('s'),t=null;
document.getElementById('r').onclick=function(){s.classList.toggle('flip')};
function go(){t=null;s.src='/stream?_='+Date.now()}
s.onerror=function(){s.removeAttribute('src');if(t===null)t=setTimeout(go,1000)};
go();
</script></body></html>
""").encode()

# ---------- MJPEG 流：每帧检测 + 标注 ----------
def stream_mjpeg(client, sensor):
    send_all(client, b'HTTP/1.1 200 OK\r\n'
             b'Content-Type: multipart/x-mixed-replace; boundary=frame\r\n'
             b'Cache-Control: no-store\r\nConnection: close\r\n\r\n')
    interval = 1000 // STREAM_FPS
    n = 0
    enc_sum = 0
    t_fps = time.ticks_ms()
    while True:
        t0 = time.ticks_ms()
        img = analyze(sensor.snapshot())
        jpeg = img.to_jpeg(quality=JPEG_Q).bytearray()
        t_enc = time.ticks_diff(time.ticks_ms(), t0) - TELEM['det_ms']
        head = ('--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n') % len(jpeg)
        send_all(client, head.encode())
        send_all(client, jpeg)
        send_all(client, b'\r\n')
        del img, jpeg
        n += 1
        enc_sum += t_enc
        TELEM['enc_ms'] = t_enc
        if n % 30 == 0:
            dt = time.ticks_diff(time.ticks_ms(), t_fps)
            TELEM['fps'] = 30000.0 / dt
            print('[流] %d帧 实测%.1ffps 检测%dms 编码均%.1fms' % (
                n, TELEM['fps'], TELEM['det_ms'], enc_sum / 30.0))
            enc_sum = 0
            t_fps = time.ticks_ms()
            gc.collect()
        delay = interval - time.ticks_diff(time.ticks_ms(), t0)
        if delay > 0:
            time.sleep_ms(delay)
        os.exitpoint()

def build_telem():
    TELEM['age_ms'] = time.ticks_diff(time.ticks_ms(), TELEM['ts'])
    return json.dumps(TELEM).encode()

def serve_client(client, sensor):
    path = read_path(client)
    if path == '/stream':
        stream_mjpeg(client, sensor)
    elif path == '/snapshot.jpg':
        jpeg = analyze(sensor.snapshot()).to_jpeg(quality=JPEG_Q).bytearray()
        send_response(client, '200 OK', 'image/jpeg', jpeg)
    elif path == '/telem.json':
        send_response(client, '200 OK', 'application/json', build_telem())
    elif path == '/favicon.ico':
        send_response(client, '204 No Content', 'text/plain', b'')
    else:
        send_response(client, '200 OK', 'text/html; charset=utf-8', INDEX_HTML)

# v1.8 不支持同机回连，自测从局域网另一端（电脑/手机）做。
def main():
    ip = wifi_connect()
    sensor = camera_init()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(2)
    server.setblocking(False)
    print('==============================================')
    print('S3 手机浏览器: http://%s:%d/' % (ip, PORT))
    print('遥测 JSON:     http://%s:%d/telem.json' % (ip, PORT))
    print('==============================================')
    while True:
        try:
            client, addr = server.accept()
        except OSError as e:
            if e.errno != 11:
                raise
            os.exitpoint()
            time.sleep_ms(20)
            continue
        print('[HTTP] 客户端:', addr)
        try:
            serve_client(client, sensor)
        except OSError:
            pass
        finally:
            client.close()
            gc.collect()

try:
    os.exitpoint(os.EXITPOINT_ENABLE)
    main()
except KeyboardInterrupt:
    print('手动停止')
finally:
    try:
        sensor.stop()
    except Exception:
        pass
