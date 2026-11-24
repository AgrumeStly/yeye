"""手机浏览器的只读首弯画面。相机与路线计算由主循环拥有。"""
import json
import time

PHONE_PORT = 8080
PHONE_INTERVAL_MS = 180
PHONE_CHUNK = 4096
PHONE_CONFIG = '/sdcard/right_angle_wifi.json'

PAGE = b"""<!doctype html><html lang="zh"><meta charset="utf-8">
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Right-angle preview</title>
<style>body{margin:0;background:#141414;color:#eee;text-align:center;font:16px sans-serif}
img{width:min(100%,800px);height:auto}button{margin:12px} .rot{transform:rotate(180deg)}</style>
<button id="r">&#26059;&#36716;</button><br><img id="v" alt="Live camera">
<script>const v=document.querySelector('#v');function connect(){v.src='/stream?'+Date.now()}
v.onerror=()=>setTimeout(connect,1000);document.querySelector('#r').onclick=()=>v.classList.toggle('rot');
connect()</script>"""
MJPEG_HEADER = (b'HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=frame\r\n'
                b'Cache-Control: no-store\r\nConnection: close\r\n\r\n')


def _phone_point(point):
    """地面代理坐标映射成原相机像素。画外点舍弃，不把线延伸到画面边缘。"""
    x, z = point
    if z <= 2:
        return None
    py = (7802.22222222222 - 38.11111111111108 * z) / (z + 15.555555555555546)
    px = 159.5 + x * (py + 38.11111111111108) / 48
    return (int(px), int(py)) if 0 <= px < 320 and 32 <= py < 240 else None


def annotate_preview(frame, result, packet):
    """给已完成控制计算的同一帧叠加线路。圆点与线段来自实际控制候选点。"""
    points = [_phone_point(point) for point in result.get('route', ())]
    shade = 255 if packet[6] & 1 else 150
    for start, end in zip(points, points[1:]):
        if start is not None and end is not None:
            frame.draw_line(start[0], start[1], end[0], end[1], color=shade, thickness=3)
    for point in points:
        if point is not None:
            frame.draw_circle(point[0], point[1], 3, color=shade, thickness=1)
    mode = {'current_pair': 'PAIR', 'current_corner_predicted': 'L CORNER',
            'current_single_forecast': 'ONE EDGE', 'short_corridor_forecast': 'SHORT PRED'}.get(result['source'], 'NO PATH')
    frame.draw_rectangle(0, 0, 320, 28, color=0, fill=True)
    frame.draw_string_advanced(4, 1, 13, '%s %s q%d' % (mode, result['stage'], result['confidence']), color=255)
    frame.draw_string_advanced(4, 14, 13, 'seq %03d  steer %+d  permit %d' %
                               (packet[5], result['steering'], int(bool(packet[6] & 1))), color=255)


class PhonePreview:
    """一次只服务一个浏览器。每次最多一次接收和一次定长发送，无等待重试。"""

    def __init__(self, server):
        self.server = server
        self.client = None
        self.last_frame = None
        self._reset_client()

    def _reset_client(self):
        if self.client is not None:
            try:
                self.client.close()
            except OSError:
                pass
        self.client = None
        self.request = bytearray()
        self.pending = b''
        self.offset = 0
        self.stream = False
        self.deadline = None

    def close(self):
        self._reset_client()
        self.server.close()

    def step(self, frame, result, packet, encode_allowed):
        """主循环已发送PATH、已保存原像素后调用。网络慢时分帧发或丢弃连接。"""
        now = time.ticks_ms()
        try:
            if self.client is None:
                self.client, _ = self.server.accept()
                self.client.setblocking(False)
                self.deadline = time.ticks_add(now, 900)
            if self.deadline is not None and time.ticks_diff(now, self.deadline) >= 0:
                self._reset_client()
                return
            if not self.stream and not self.pending:
                incoming = self.client.recv(512)
                if incoming is None:
                    return
                if not incoming:
                    self._reset_client()
                    return
                self.request.extend(incoming)
                if len(self.request) > 1536:
                    self._reset_client()
                    return
                if self.request.find(b'\r\n\r\n') < 0:
                    return
                fields = bytes(self.request).split(b'\r\n', 1)[0].split()
                if len(fields) < 2 or fields[0] != b'GET':
                    self._reset_client()
                    return
                self.stream = fields[1].split(b'?', 1)[0] == b'/stream'
                self.pending = MJPEG_HEADER if self.stream else (
                    ('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %d\r\n'
                     'Connection: close\r\n\r\n' % len(PAGE)).encode() + PAGE)
            if (self.stream and not self.pending and encode_allowed
                    and (self.last_frame is None or time.ticks_diff(now, self.last_frame) >= PHONE_INTERVAL_MS)):
                annotate_preview(frame, result, packet)
                jpeg = frame.to_jpeg(quality=55).bytearray()
                self.pending = (('--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n'
                                 % len(jpeg)).encode() + bytes(jpeg) + b'\r\n')
                self.deadline = time.ticks_add(now, 900)
                self.last_frame = now
            if self.pending:
                sent = self.client.send(memoryview(self.pending)[self.offset:self.offset + PHONE_CHUNK])
                if sent:
                    self.offset += sent
                    if self.offset == len(self.pending):
                        if not self.stream:
                            self._reset_client()
                            return
                        self.pending = b''
                        self.offset = 0
                        self.deadline = None
                    else:
                        self.deadline = time.ticks_add(now, 900)
        except OSError as exc:
            if not exc.args or exc.args[0] not in (11, 35, 110, 116):
                self._reset_client()


def open_phone_preview():
    """开机连接已有队内热点并返回非阻塞服务器。失败时车载功能照常等待Go。"""
    server = None
    try:
        import socket
        import network

        with open(PHONE_CONFIG) as handle:
            config = json.load(handle)
        if not config.get('enabled'):
            return None
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        if not wifi.isconnected():
            key = config['ssid_key'].encode('utf-8')
            target = next((ap for ap in wifi.scan() if key in getattr(ap, 'ssid', b'')), None)
            if target is None:
                print('[PHONE] hotspot not found')
                return None
            wifi.connect(target.ssid, config['password'])
            for _ in range(25):
                if wifi.isconnected():
                    break
                time.sleep_ms(200)
        if not wifi.isconnected():
            print('[PHONE] hotspot connection timeout')
            return None
        ip = wifi.ifconfig()[0]
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ip, PHONE_PORT))
        server.listen(2)
        server.setblocking(False)
        print('[PHONE] http://%s:%d/' % (ip, PHONE_PORT))
        return PhonePreview(server)
    except Exception:
        if server is not None:
            try:
                server.close()
            except OSError:
                pass
        print('[PHONE] preview unavailable')
        return None
