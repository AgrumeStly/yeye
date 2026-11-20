"""首次派生独立直道Keil目标，沿用SPL／已确认CMSIS-DAP配置；不烧录。"""
from pathlib import Path
import copy
import xml.etree.ElementTree as ET


def main():
    root = Path(__file__).resolve().parents[1]
    target_path = root / 'MDK-ARM/straight_assist.uvprojx'
    if target_path.exists():
        raise FileExistsError('edit existing StraightAssist project; do not overwrite')
    tree = ET.parse(root / 'MDK-ARM/low_speed_lap.uvprojx')
    targets = tree.find('Targets')
    target = copy.deepcopy(targets.find('Target'))
    targets.clear()
    targets.append(target)
    target.find('TargetName').text = 'StraightAssist'
    common = target.find('TargetOption/TargetCommonOption')
    for name in ('OutputDirectory', 'ListingPath'):
        common.find(name).text = '..\\build\\firmware\\straight_assist\\'
    common.find('OutputName').text = 'straight_assist'
    target.find('TargetOption/TargetArmAds/Cads/VariousControls/Define').text += ',STRAIGHT_ASSIST_TARGET=1'
    group = ET.SubElement(target.find('Groups'), 'Group')
    ET.SubElement(group, 'GroupName').text = 'StraightGuide'
    files = ET.SubElement(group, 'Files')
    item = ET.SubElement(files, 'File')
    for name, value in (('FileName', 'straight_guide.c'), ('FileType', '1'),
                        ('FilePath', '..\\Algorithms\\Speed\\straight_guide.c')):
        ET.SubElement(item, name).text = value
    ET.indent(tree)
    tree.write(target_path, encoding='utf-8', xml_declaration=True)
    # 本机uvoptx被Git忽略；缺少源设置时不假造下载器配置。
    original = root / 'MDK-ARM/low_speed_lap.uvoptx'
    if original.exists():
        options = ET.parse(original)
        entries = options.findall('Target')
        kept = copy.deepcopy(entries[0])
        for entry in entries:
            options.getroot().remove(entry)
        kept.find('TargetName').text = 'StraightAssist'
        watch = kept.find('TargetOption/WatchWindow1')
        if watch is not None:
            watch.clear()
            for index, expression in enumerate(('g_speed_revision', 'g_speed_fault', 'g_lap', 'g_lap_config',
                                                'g_straight_guide', 'g_speed_match', 'g_lap_last', 'g_lap_diag',
                                                'g_lap_parser', 'g_lap_uart_errors', 'g_lap_timing')):
                item = ET.SubElement(watch, 'Ww')
                for name, value in (('count', str(index)), ('WinNumber', '1'), ('ItemText', expression)):
                    ET.SubElement(item, name).text = value
        options.getroot().append(kept)
        ET.indent(options)
        options.write(root / 'MDK-ARM/straight_assist.uvoptx', encoding='utf-8', xml_declaration=True)
    print(target_path)


if __name__ == '__main__':
    main()
