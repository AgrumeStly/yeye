"""核对实际AXF布局与环形取证解码，不能代替实板中断耗时或试跑。"""
import importlib.util
import json
from pathlib import Path
import struct
from elftools.elf.elffile import ELFFile

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('lap_capture',ROOT/'control/tools/lap_swd_capture.py')
capture=importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
expected={
    'lap_diag_view_t':(1952,dict(total_samples=0,frozen=4,stop_at_ms=8,stop_reason=12,
        left_channel=16,right_channel=20,left_sign=24,right_sign=28,samples=32)),
    'lap_diag_sample_t':(60,dict(at_ms=0,dt_ms=4,received=8,path_at=12,left_delta=16,
        right_delta=20,left_counts_per_s=24,right_counts_per_s=28,left_raw_rpm=32,
        right_raw_rpm=36,left_target=40,right_target=44,left_pwm=48,right_pwm=50,
        steering=52,bend=54,history=56,single=57,path_valid=58,path_sequence=59))}
found={}
with capture.AXF.open('rb') as stream:
    dwarf=ELFFile(stream).get_dwarf_info()
    for cu in dwarf.iter_CUs():
        for die in cu.iter_DIEs():
            name=die.attributes.get('DW_AT_name')
            if die.tag=='DW_TAG_typedef' and name and name.value.decode() in expected:
                item=die.get_DIE_from_attribute('DW_AT_type')
                members={}
                for member in item.iter_children():
                    if member.tag=='DW_TAG_member':
                        location=member.attributes['DW_AT_data_member_location'].value
                        assert location[0]==35
                        members[member.attributes['DW_AT_name'].value.decode()]=location[1]
                found[name.value.decode()]=(item.attributes['DW_AT_byte_size'].value,members)
assert found==expected,(found,expected)
blob=bytearray(1952)
struct.pack_into('<6I2i',blob,0,130,1,2580,5,2,1,-1,1)
for k in range(98,130):
    struct.pack_into('<4I4i4fHHhH4B',blob,32+(k%32)*60,
        k*20,20,k*2,k*20-60,-2,10,-100,500,-6.25,28.0,6.75,23.0,
        172,298,-545,845,0,1,1,0)
actual=capture.diagnostic_view(blob)
assert len(actual['samples'])==32
assert [s['at_ms'] for s in actual['samples']]==list(range(1960,2600,20))
assert actual['samples'][-1]['left_delta']==-2
assert actual['samples'][-1]['left_raw_rpm']==-6.25
assert actual['samples'][-1]['single']==1
assert capture.diagnostic_view(bytes(1952))['samples']==[]
capture.symbols()
result=dict(passed=True,host_only=True,actual_armcc_dwarf_layout=found,
    ring_wrap_order_checked=True,negative_sample_retained=True,empty_trace_checked=True)
folder=Path(__file__).parent/'diagnostic_checks_02'
folder.mkdir(exist_ok=False)
(folder/'checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('ARMCC DWARF and diagnostic ring decoder checks passed; no device accessed.')
