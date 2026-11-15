"""从原工程只读派生独立LowSpeedLap配置／入口；不覆盖原文件，不操作板卡。

本工具保留已验证的启动限时／IWDG代码，替换调度入口并增加独立UART。
本工具只允许首次执行；产物已存在就拒绝，后续直接维护独立C／Keil源。
"""
from pathlib import Path
import copy
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
# 这是首次派生用的引导工具；生成后的C／Keil文件就是可编辑源，不再覆盖。
targets=(root/'Core/Src/low_speed_lap_main.c',root/'MDK-ARM/low_speed_lap.uvprojx')
if any(path.exists() for path in targets):
    raise FileExistsError('LowSpeedLap already exists; edit its C/Keil source directly, do not regenerate over shared work')
source = (root / 'Core/Src/speed_match_main.c').read_text(encoding='utf-8')
source = source.replace('@file speed_match_main.c','@file low_speed_lap_main.c').replace('双轮同速独立台架','低速视觉差速独立入口')
source = source.replace('#include "speed_match.h"', '#include "lap_motion.h"\n#include "lap_link.h"\n#include "lap_uart.h"')
source = source.replace(' * 原逐轮校准500ms，成功后双轮同目标RPM；不连接UART或整车循迹状态机。',
    ' * 前两次KEY逐轮500ms校准；之后KEY启动视觉差速，UART断流由1ms监督撤驱动。')
source = source.replace('volatile uint32_t g_speed_ms, g_speed_fault, g_speed_revision;',
    'volatile uint32_t g_speed_ms, g_speed_fault, g_speed_revision;\nlap_parser_t g_lap_parser;')
source = source.replace('speed_match_sample(now, &g_speed_encoder_a.sample, &g_speed_encoder_b.sample);',
    'lap_motion_sample(now, &g_speed_encoder_a.sample, &g_speed_encoder_b.sample);')
source = source.replace('speed_match_tick(now, GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_0));',
    'lap_motion_tick(now, GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_0));')
source = source.replace('straight_pwm_apply(g_speed_match.left_pwm, g_speed_match.right_pwm)',
    'straight_pwm_apply(g_lap.left_pwm, g_lap.right_pwm)')
source = source.replace('speed_match_fault(SPEED_ERROR_HARDWARE, now);', 'lap_motion_fault(LAP_HARDWARE, now);')
source = source.replace('speed_match_led(now)', 'lap_motion_led(now)')
source = source.replace('uint32_t now = ++g_speed_ms;', 'uint32_t now = ++g_speed_ms;\n    lap_uart_tick(now);')
source = source.replace('g_speed_revision = 0x020f0001u;', 'g_speed_revision = 0x02110001u;')
source = source.replace('speed_match_init(0u);', 'lap_motion_init(0u);\n    lap_link_init(&g_lap_parser);\n    lap_uart_init();')
source = source.replace('speed_match_fault(SPEED_ERROR_HARDWARE, 0u);', 'lap_motion_fault(LAP_HARDWARE, 0u);')
source = source.replace('    for (;;) __WFI();', '''    /* 协议解析留在主循环；停止／轮速／看门狗始终由更高优先级滴答执行。
     * 一帧提交只拷贝少量标量，临界区不包含CRC／串口等待或图像处理。
     * 每次循环先处理传输错误，绝不从已溢出的缓冲恢复运动许可。
     */
    for (;;) {
        uint8_t byte; uint32_t arrival, mask;
        if (lap_uart_fault()) {
            mask = __get_PRIMASK(); __disable_irq();
            lap_motion_fault(LAP_TRANSPORT, g_speed_ms); lap_link_init(&g_lap_parser);
            __set_PRIMASK(mask);
        }
        while (lap_uart_read(&byte, &arrival)) {
            if (lap_link_push(&g_lap_parser, byte)) {
                mask = __get_PRIMASK(); __disable_irq();
                lap_motion_receive(g_lap_parser.bytes, arrival, g_speed_ms);
                __set_PRIMASK(mask);
            }
        }
        /* 不在这里WFI：包到达与睡眠之间的竞争可能把解析延迟一拍。
         * 低功耗不是本试跑的目标，主循环无等待，ISR只维护接收环。
         */
    }''')
if 'SPEED_SPRINT_TARGET' in source:
    # 删除仅高速目标的预处理分支，防止独立目标被误定义宏后走错状态机。
    lines = source.splitlines(); out = []; stack = []
    for line in lines:
        if line.strip() == '#ifdef SPEED_SPRINT_TARGET': stack.append(False); continue
        if stack and line.strip() == '#else': stack[-1] = not stack[-1]; continue
        if stack and line.strip() == '#endif': stack.pop(); continue
        if all(stack): out.append(line)
    source = '\n'.join(out) + '\n'
source=source.replace('    g_speed_revision = 0x02110001u;', '#ifdef LAP_TRACK_TARGET\n    g_speed_revision = 0x02110002u;\n#else\n    g_speed_revision = 0x02110001u;\n#endif')
(root / 'Core/Src/low_speed_lap_main.c').write_text(source, encoding='utf-8')
tree = ET.parse(root / 'MDK-ARM/speed_match.uvprojx')
target = tree.find('./Targets/Target')
target.find('TargetName').text = 'LowSpeedLap'
common = target.find('TargetOption/TargetCommonOption')
for name in ('OutputDirectory', 'ListingPath'): common.find(name).text = '..\\build\\firmware\\low_speed_lap\\'
common.find('OutputName').text = 'low_speed_lap'
defines=target.find('TargetOption/TargetArmAds/Cads/VariousControls/Define')
defines.text=defines.text.replace('BOARD_UART_ENABLE=0','BOARD_UART_ENABLE=1')
for group in target.findall('Groups/Group'):
    files = group.find('Files')
    if files is None: continue
    for f in list(files):
        included = f.find('FileOption/CommonProperty/IncludeInBuild')
        if included is not None and included.text == '0': files.remove(f)
        elif f.findtext('FileName') == 'speed_match_main.c':
            f.find('FileName').text = 'low_speed_lap_main.c'
            f.find('FilePath').text = '..\\Core\\Src\\low_speed_lap_main.c'
group = ET.SubElement(target.find('Groups'), 'Group'); ET.SubElement(group, 'GroupName').text = 'LowSpeedLap'
files = ET.SubElement(group, 'Files')
existing = {f.findtext('FileName') for f in target.findall('Groups/Group/Files/File')}
for path in ('App/Motion/lap_motion.c', 'Drivers_Custom/Communication/lap_link.c',
             'Drivers_Custom/Communication/lap_uart.c', 'Drivers_Custom/Communication/protocol.c',
             'Drivers/stdperiph/src/stm32f4xx_usart.c'):
    if Path(path).name in existing: continue
    f = ET.SubElement(files, 'File')
    ET.SubElement(f, 'FileName').text = Path(path).name
    ET.SubElement(f, 'FileType').text = '1'
    ET.SubElement(f, 'FilePath').text = '..\\' + path.replace('/', '\\')
track=copy.deepcopy(target); track.find('TargetName').text='LowSpeedLapTrack'
track_common=track.find('TargetOption/TargetCommonOption')
for name in ('OutputDirectory','ListingPath'): track_common.find(name).text='..\\build\\firmware\\low_speed_lap_track\\'
track_common.find('OutputName').text='low_speed_lap_track'
track.find('TargetOption/TargetArmAds/Cads/VariousControls/Define').text+=',LAP_TRACK_TARGET=1'
tree.find('Targets').append(track)
ET.indent(tree)
tree.write(root / 'MDK-ARM/low_speed_lap.uvprojx', encoding='utf-8', xml_declaration=True)
# 本机调试设置沿用主控已确认的CMSIS-DAP；只复制为新工程，不改原设置。
options=ET.parse(root/'MDK-ARM/speed_match.uvoptx'); opt_target=options.find('Target')
opt_target.find('TargetName').text='LowSpeedLap'
watch=opt_target.find('TargetOption/WatchWindow1')
if watch is not None:
    watch.clear()
    for i,expression in enumerate(('g_speed_revision','g_speed_fault','g_lap','g_lap_config','g_speed_match','g_lap_parser','g_lap_uart_errors')):
        item=ET.SubElement(watch,'Ww'); ET.SubElement(item,'count').text=str(i)
        ET.SubElement(item,'WinNumber').text='1'; ET.SubElement(item,'ItemText').text=expression
track_opt=copy.deepcopy(opt_target); track_opt.find('TargetName').text='LowSpeedLapTrack'; options.getroot().append(track_opt)
ET.indent(options); options.write(root/'MDK-ARM/low_speed_lap.uvoptx',encoding='utf-8',xml_declaration=True)
print('Independent LowSpeedLap entry/project prepared; original files unchanged.')
