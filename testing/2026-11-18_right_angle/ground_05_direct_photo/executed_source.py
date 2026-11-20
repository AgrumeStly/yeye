import time,os
from media.sensor import Sensor,CAM_CHN_ID_0
from media.display import Display
from media.media import MediaManager
sensor=None
try:
 sensor=Sensor(id=2);sensor.reset()
 sensor.set_framesize(width=320,height=240,chn=CAM_CHN_ID_0)
 sensor.set_pixformat(Sensor.GRAYSCALE,chn=CAM_CHN_ID_0)
 sensor.set_hmirror(False);sensor.set_vflip(False)
 Display.init(Display.VIRT,width=320,height=240,to_ide=True)
 MediaManager.init();sensor.run()
 start=time.ticks_ms()
 print('DIRECT_PHOTO_READY NO_UART NO_SD')
 while time.ticks_diff(time.ticks_ms(),start)<8000:
  os.exitpoint()
  frame=sensor.snapshot(chn=CAM_CHN_ID_0)
  Display.show_image(frame)
  time.sleep_ms(40)
finally:
 if sensor is not None:sensor.stop()
 Display.deinit();time.sleep_ms(100);MediaManager.deinit()
