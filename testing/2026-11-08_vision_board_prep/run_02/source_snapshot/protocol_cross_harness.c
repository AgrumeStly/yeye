/* 视觉PC交叉验证适配器：仅调用现有protocol.c和car.c，不含寄存器或电机。
 * 通过DLL向Python公开观测函数。now的单位为毫秒；所有请求只是原car.c
 * 演示归一量，不解释为RPM/PWM。此文件不加入STM32或Keil工程。
 */
#include "protocol.h"
#include "car.h"
#include <stdio.h>

static protocol_parser_t parser;
static car_t vehicle;

/* 清空协议和车辆模型，等同独立上电后的软件初始条件。 */
__declspec(dllexport) void probe_reset(void) {
    protocol_parser_init(&parser);
    car_init(&vehicle);
}

/* 按真实生产解析器逐字节输入；只有CRC和字段合法的完整包更新车辆模型。
 * bytes只读、count为字节数、now为本地毫秒。返回本次解析的合法包数。
 */
__declspec(dllexport) unsigned probe_feed(const unsigned char *bytes, unsigned count, unsigned now) {
    unsigned i, accepted=0;
    protocol_frame_t frame;
    for(i=0;i<count;++i) {
        if(protocol_push(&parser,bytes[i],&frame)) {
            car_receive(&vehicle,&frame,now);
            ++accepted;
        }
    }
    car_tick(&vehicle,now);
    return accepted;
}

/* 无数据时仍执行原生产监督逻辑，验证200ms断流及归零。 */
__declspec(dllexport) void probe_tick(unsigned now) { car_tick(&vehicle,now); }
/* 注入传输故障，不生成物理UART中断，验证原故障路径。 */
__declspec(dllexport) void probe_transport_fault(void) { car_transport_fault(&vehicle); }
/* 下列只读快照用于测试状态、偏差符号、序号和拒绝行为。 */
__declspec(dllexport) int probe_state(void) { return (int)vehicle.state; }
__declspec(dllexport) int probe_reason(void) { return (int)vehicle.reason; }
__declspec(dllexport) int probe_error(void) { return vehicle.path.error; }
__declspec(dllexport) int probe_flags(void) { return vehicle.path.flags; }
__declspec(dllexport) int probe_sequence(void) { return vehicle.path.sequence; }
__declspec(dllexport) int probe_left(void) { return vehicle.left_request; }
__declspec(dllexport) int probe_right(void) { return vehicle.right_request; }
__declspec(dllexport) unsigned probe_duplicates(void) { return vehicle.duplicates; }
__declspec(dllexport) unsigned probe_path_time(void) { return vehicle.path_time; }

/* 独立32位主机进程接口，避免32位MinGW DLL无法装入64位Python。
 * 输入F 字节数 毫秒 十六进制／T 毫秒／R／X，输出只读整数快照。
 * 最多512字节一批，越界或格式错误退出；无串口、GPIO和设备访问。
 */
int main(void) {
    char operation, hex[1025];
    unsigned size,now,value,i,accepted;
    unsigned char data[512];
    probe_reset();
    while(scanf(" %c",&operation)==1) {
        accepted=0;
        if(operation=='R') probe_reset();
        else if(operation=='X') probe_transport_fault();
        else if(operation=='T') {
            if(scanf("%u",&now)!=1) return 2;
            probe_tick(now);
        } else if(operation=='F') {
            if(scanf("%u %u %1024s",&size,&now,hex)!=3 || size>512u) return 3;
            for(i=0;i<size;++i) {
                if(sscanf(hex+i*2u,"%2x",&value)!=1) return 4;
                data[i]=(unsigned char)value;
            }
            accepted=probe_feed(data,size,now);
        } else return 5;
        printf("%u %d %d %d %d %d %d %d %u %u\n",accepted,probe_state(),probe_reason(),
               probe_error(),probe_flags(),probe_sequence(),probe_left(),probe_right(),
               probe_duplicates(),probe_path_time());
        fflush(stdout);
    }
    return 0;
}
