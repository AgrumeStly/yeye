"""使用已安装CanMV扩展的官方stdio后端进行限定诊断和悬空台架。

专用CanMV工具不可用时，本助手复用本机0.9.10后端的CM封帧协议。
普通模式只支持状态、已有SD诊断、无效UART包、无驱动live。
motor_straight/right/left仅在主控确认轮子悬空和MCU三秒上限后提供人工固定输入，
明确不是相机；仍不发START。live_link_isolated／live_link_suspended是显式
真实相机模式，分别要求动力隔离或当前悬空／版本／校准确认，不供地面使用。
没有任意脚本、Flash、main.py或文件删除。
同一COM口不能和VS Code同时连接；已运行脚本不自动打断。
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import queue
import struct
import subprocess
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
BACKEND=Path('C:/Users/Agrum/.vscode/extensions/kendryte747.canmv-vscode-0.9.10/bin/win32-x64/canmv-backend.exe')
MOTOR_SCENARIOS={'motor_straight':'straight','motor_right':'right','motor_left':'left'}
VISUAL_MODES={'live_link_isolated':'isolated','live_link_suspended':'suspended'}


class Session:
    """单一后端／端口所有者；线程只拆帧入队，主线程顺序记录和发请求。"""
    def __init__(self,output):
        self.output=output; self.messages=queue.Queue(); self.index=0; self.running=None; self.script_error=False
        self.tail=''
        # 仅无驱动live模式开启主机取证；保存已有预览JPEG，不向板上写文件。
        self.capture_preview=False; self.preview_saved=0; self.preview_next_at=0.0; self.preview_invalid=0
        self.log=(output/'backend.jsonl').open('w',encoding='utf-8')
        self.terminal=(output/'terminal.txt').open('w',encoding='utf-8')
        self.child=subprocess.Popen([str(BACKEND)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        threading.Thread(target=self._read,daemon=True).start()
        threading.Thread(target=self._stderr,daemon=True).start()

    def _stderr(self):
        for line in iter(self.child.stderr.readline,b''):
            self.messages.put(dict(stderr=line.decode('utf-8',errors='replace')))

    def _read(self):
        def exact(n):
            chunks=bytearray()
            while len(chunks)<n:
                data=self.child.stdout.read(n-len(chunks))
                if not data: raise EOFError('CanMV backend closed')
                chunks.extend(data)
            return bytes(chunks)
        try:
            while True:
                header=exact(7)
                if header[:2]!=b'CM': raise ValueError('unexpected backend framing')
                kind=header[2]; size=struct.unpack('<I',header[3:])[0]
                if size>50*1024*1024: raise ValueError('oversized backend packet')
                body=exact(size)
                if kind in (2,3): self.messages.put(json.loads(body))
                elif kind==4: self._save_preview(body)
        except BaseException as exc:
            self.messages.put(dict(reader_error=str(exc)))

    def _save_preview(self,body):
        """按已安装官方扩展的MSG_FRAME布局保存少量未叠加JPEG。

        载荷是小端4字节帧号加JPEG；沿用官方端的SOI检查和末尾EOI截取。
        主机最多保存5张、间隔至少1秒，不阻塞等待，不改板上帧或控制消息。
        帧号属于后端图像流，不能擅自当作算法JSON中的index或曝光时间。
        文件错误仅禁用后续取图，继续接收脚本状态，避免诊断失去清理通道。
        """
        if not self.capture_preview or self.preview_saved>=5: return
        if len(body)<8 or len(body)>5*1024*1024 or body[4:6]!=b'\xff\xd8':
            self.preview_invalid+=1; return
        jpeg=body[4:]; end=jpeg.rfind(b'\xff\xd9')
        if end<2: self.preview_invalid+=1; return
        now=time.monotonic()
        if now<self.preview_next_at: return
        jpeg=jpeg[:end+2]; frame_id=struct.unpack('<I',body[:4])[0]
        folder=self.output/'preview'; number=self.preview_saved+1
        path=folder/('preview_%02d_frame_%08d.jpg'%(number,frame_id))
        try:
            folder.mkdir(exist_ok=True); path.write_bytes(jpeg)
        except OSError as exc:
            self.capture_preview=False
            self.messages.put(dict(event='previewSaveError',params=dict(error=str(exc))))
            return
        self.preview_saved=number; self.preview_next_at=now+1.0
        self.messages.put(dict(event='previewSaved',params=dict(file=str(path.relative_to(self.output)),
            frame_id=frame_id,bytes=len(jpeg),sha256=hashlib.sha256(jpeg).hexdigest(),host_monotonic=now)))

    def record(self,message):
        self.log.write(json.dumps(dict(at=time.time(),**message),ensure_ascii=False)+'\n'); self.log.flush()
        if message.get('event')=='scriptOutput':
            text=str(message.get('params',{}).get('text',''))
            self.tail=(self.tail+text)[-12000:]
            if 'Traceback (most recent call last)' in self.tail: self.script_error=True
            self.terminal.write(text); self.terminal.flush(); print(text,end='',flush=True)
        if message.get('event')=='scriptState':
            state=message.get('params',{}).get('state')
            if state=='started': self.running=True
            if state=='finished': self.running=False

    def request(self,method,params=None,timeout=20):
        self.index+=1; identifier=self.index
        request=dict(id=identifier,method=method,params=params or {})
        # 执行全文另存source，日志避免重复大脚本文本；从不打印环境或凭据。
        logged=dict(request)
        if method=='runScript': logged['params']={'script_sha256':hashlib.sha256(params['script'].encode()).hexdigest()}
        self.record({'request':logged})
        payload=json.dumps(request).encode()
        self.child.stdin.write(b'CM'+bytes((1,))+struct.pack('<I',len(payload))+payload); self.child.stdin.flush()
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            try: message=self.messages.get(timeout=min(1,max(.01,deadline-time.monotonic())))
            except queue.Empty: continue
            self.record(message)
            if 'reader_error' in message: raise RuntimeError(message['reader_error'])
            if message.get('id')==identifier:
                if 'error' in message: raise RuntimeError(json.dumps(message['error'],ensure_ascii=False))
                return message.get('result',{})
        raise TimeoutError(method+' timeout')

    def close(self):
        try:
            if self.child.poll() is None:
                try: self.request('disconnectBoard',timeout=5)
                except BaseException as exc: self.record({'disconnect_error':str(exc)})
        finally:
            if self.child.poll() is None:
                self.child.terminate()
                try: self.child.wait(timeout=5)
                except subprocess.TimeoutExpired: self.child.kill(); self.child.wait(timeout=5)
            self.log.close(); self.terminal.close()


def replacement(source,old,new):
    if source.count(old)!=1: raise ValueError('unexpected source configuration: '+old)
    return source.replace(old,new)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=('status','sd_replay','uart_probe','live_no_drive',*MOTOR_SCENARIOS,*VISUAL_MODES))
    parser.add_argument('--port',default='COM10'); parser.add_argument('--output',required=True)
    parser.add_argument('--bundle',default='testing/2026-11-09_low_speed_lap/board_bundle_runtime_r5/low_speed_lap_canmv.py')
    parser.add_argument('--confirmed-suspended',action='store_true')
    parser.add_argument('--confirmed-mcu-run-ms',type=int)
    parser.add_argument('--motor-window-ms',type=int,choices=(120000,600000),default=600000)
    parser.add_argument('--confirmed-power-isolated',action='store_true')
    parser.add_argument('--confirmed-mcu-revision',type=lambda text:int(text,0))
    parser.add_argument('--confirmed-calibrated',action='store_true')
    parser.add_argument('--visual-window-ms',type=int,choices=(120000,600000),default=120000)
    parser.add_argument('--visual-bundle',choices=('r5','r6'),default='r5')
    args=parser.parse_args(); output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    motor_mode=args.mode in MOTOR_SCENARIOS
    if motor_mode and (not args.confirmed_suspended or args.confirmed_mcu_run_ms!=3000):
        raise ValueError('physical suspension and actual MCU 3000ms limit must be confirmed first')
    visual_info=None
    if args.mode in VISUAL_MODES:
        # 先于连接串口验证门槛和冻结哈希。仅生成R5实时相机配置，不能替换为SD或fixture。
        from prepare_lap_visual_link import prepare
        visual_source,visual_info=prepare(VISUAL_MODES[args.mode],
            power_isolated=args.confirmed_power_isolated,suspended=args.confirmed_suspended,
            mcu_revision=args.confirmed_mcu_revision,mcu_run_ms=args.confirmed_mcu_run_ms,
            calibrated=args.confirmed_calibrated,window_ms=args.visual_window_ms,bundle=args.visual_bundle)
    elif args.mode=='live_no_drive' and args.visual_bundle=='r6':
        # 地面失败后的短时原图取证复用冻结R6。prepare会核对精确哈希，
        # no_drive固定10秒／ALLOW_DRIVE=False，保留相机预览和全部发送保护；
        # 不把诊断扩展成任意脚本入口，也不写main.py或自动发送START。
        from prepare_lap_visual_link import prepare
        visual_source,visual_info=prepare('no_drive',bundle='r6')
    session=Session(output)
    session.capture_preview=args.mode=='live_no_drive'
    preview_attempted=preview_active=False
    try:
        board=session.request('connectBoard',{'port':args.port,'baudRate':12000000},timeout=25)
        print('BOARD',json.dumps(board,ensure_ascii=False),flush=True)
        time.sleep(.25)
        status=session.request('scriptRunning')
        print('STATE',json.dumps(status,ensure_ascii=False),flush=True)
        (output/'board.json').write_text(json.dumps(dict(board=board,status=status),ensure_ascii=False,indent=2),encoding='utf-8')
        if args.mode=='status': return
        # 只在明确报告空闲后运行；未知结构或已有脚本直接退出，不隐式stop。
        running=status.get('running',status.get('scriptRunning',status.get('script_running')))
        if running is not False: raise RuntimeError('board idle not confirmed; existing script will not be stopped automatically')
        if visual_info is not None:
            source=visual_source
        elif motor_mode:
            folder=ROOT/'testing/2026-11-11_battery_bench/motor_bench_bundle_r3'
            manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
            bundle_bytes=(folder/'lap_motor_bench_canmv.py').read_bytes()
            # manifest记录实际文件字节，不能先read_text归一化CRLF再计算字节哈希。
            if hashlib.sha256(bundle_bytes).hexdigest()!=manifest['bundle_sha256']:
                raise RuntimeError('motor fixture bundle changed since checks')
            source=bundle_bytes.decode('utf-8').replace('\r\n','\n')
            if "SCENARIO='straight'" not in source or 'DURATION_MS=600000' not in source:
                raise ValueError('only the checked bounded suspended fixture is allowed')
            source=replacement(source,"SCENARIO='straight'","SCENARIO="+repr(MOTOR_SCENARIOS[args.mode]))
            # 只允许已验证的2分钟或10分钟等待窗口；不改变主板每次3秒限制。
            source=replacement(source,'DURATION_MS=600000','DURATION_MS='+str(args.motor_window_ms))
            source=replacement(source,'600s input window',str(args.motor_window_ms//1000)+'s input window')
            source=replacement(source,'ENABLED=False','ENABLED=True')
        elif args.mode=='uart_probe':
            source=(ROOT/'vision/src/lap_uart_probe_canmv.py').read_text(encoding='utf-8')
            source=replacement(source,'ENABLED=False','ENABLED=True')
        else:
            bundle=(ROOT/args.bundle).resolve()
            if not bundle.is_relative_to(ROOT/'testing/2026-11-09_low_speed_lap') or bundle.name!='low_speed_lap_canmv.py':
                raise ValueError('only this task diagnostic bundle is allowed')
            source=bundle.read_text(encoding='utf-8')
            source=replacement(source,"MODE='idle'","MODE='sd_replay'" if args.mode=='sd_replay' else "MODE='live'")
            if args.mode=='live_no_drive':
                source=replacement(source,'UART_ENABLED=False','UART_ENABLED=True')
                source=replacement(source,'DURATION_MS=300000','DURATION_MS=10000')
        if args.mode!='uart_probe' and not motor_mode and visual_info is None and 'ALLOW_DRIVE=False' not in source: raise RuntimeError('drive gate missing')
        # 按发送给后端的原始UTF8字节保存，使run.json文本哈希也可直接校验此文件。
        (output/'executed_source.py').write_bytes(source.encode('utf-8'))
        (output/'run.json').write_text(json.dumps(dict(mode=args.mode,port=args.port,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            started=datetime.now().astimezone().isoformat(),automatic_motor_start_permitted=False,
            operator_KEY_fixture_test=motor_mode,confirmed_suspended=args.confirmed_suspended,
            confirmed_mcu_run_ms=args.confirmed_mcu_run_ms,input_window_ms=args.motor_window_ms if motor_mode else None,
            main_py_written=False,real_camera_link=visual_info),ensure_ascii=False,indent=2),encoding='utf-8')
        session.running=True; result=session.request('runScript',{'script':source},timeout=35)
        print('RUN',json.dumps(result,ensure_ascii=False),flush=True)
        # 固定输入等待较长，只延长本助手会话期限；STM32每次仍由KEY启动且限3秒。
        diagnostic_timeout=(args.motor_window_ms//1000+30 if motor_mode else
            args.visual_window_ms//1000+30 if visual_info is not None else 150)
        deadline=time.monotonic()+diagnostic_timeout; next_status=time.monotonic()+2
        while session.running is not False and time.monotonic()<deadline:
            try: session.record(session.messages.get(timeout=.25))
            except queue.Empty: pass
            if session.capture_preview and not preview_attempted and '"index":' in session.tail:
                # 第一条真实帧日志出现后相机/Display已初始化，再按官方RPC开预览。
                preview_attempted=True
                try:
                    session.request('startPreview',{},timeout=10); preview_active=True
                except BaseException as exc:
                    session.record({'preview_start_error':str(exc)})
            if time.monotonic()>=next_status:
                result=session.request('scriptRunning')
                session.running=result.get('running',result.get('scriptRunning',result.get('script_running',session.running)))
                next_status=time.monotonic()+2
        if session.running is not False:
            # 只中断本助手启动的无动力诊断，不改变其它会话／原main.py。
            session.request('stopScript',timeout=15)
            raise TimeoutError('diagnostic exceeded '+str(diagnostic_timeout)+' seconds; own script interrupted')
        session.request('scriptRunning')
        if session.script_error: raise RuntimeError('board traceback recorded; diagnostic did not pass')
        marker='[MOTOR BENCH DONE]' if motor_mode else ('[UART PROBE DONE]' if args.mode=='uart_probe' else '[L1 DONE]')
        if marker not in session.tail: raise RuntimeError('normal diagnostic completion marker missing')
        print('DONE: no motor START, no main.py write',flush=True)
    finally:
        if preview_active:
            try: session.request('stopPreview',{},timeout=5)
            except BaseException as exc: session.record({'preview_stop_error':str(exc)})
        session.close()


if __name__=='__main__': main()
