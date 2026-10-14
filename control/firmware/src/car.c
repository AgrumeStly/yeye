#include "car.h"
#include <string.h>
static void stop(car_t *c, car_state_t state, stop_reason_t reason) {
    c->state=state; c->reason=reason; c->left_request=0; c->right_request=0;
}
static int path_ready(const car_t *c, uint32_t now) {
    return c->have_path && (uint32_t)(now-c->path_time) < CAR_LINK_TIMEOUT_MS &&
           (c->path.flags & PATH_VALID) && c->path.confidence >= CAR_MIN_CONFIDENCE &&
           c->path.processing_ms <= CAR_PROCESSING_LIMIT_MS;
}
void car_init(car_t *c) { memset(c, 0, sizeof(*c)); c->state=CAR_IDLE; }
void car_transport_fault(car_t *c) { stop(c, CAR_FAULT, STOP_TRANSPORT); c->have_path=0; }
void car_receive(car_t *c, const protocol_frame_t *f, uint32_t now) {
    uint8_t index, delta;
    if (f->type != PROTOCOL_PATH && f->type != PROTOCOL_COMMAND) return;
    /* A late frame must not conceal a timeout between two scheduler ticks. */
    if (c->state == CAR_RUNNING && !path_ready(c, now)) stop(c, CAR_FAULT, STOP_LINK);
    index = (uint8_t)(f->type-1u);
    /* Explicit STOP is idempotent, including repeated/old command sequence numbers. */
    if (f->type == PROTOCOL_COMMAND && f->command == CMD_STOP) {
        stop(c, CAR_STOPPED, STOP_COMMAND);
        delta=(uint8_t)(f->sequence-c->last_sequence[index]);
        if (!c->seen[index] || (uint32_t)(now-c->sequence_time[index]) >= CAR_LINK_TIMEOUT_MS ||
            (delta != 0u && delta < 128u)) {
            c->seen[index]=1; c->last_sequence[index]=f->sequence; c->sequence_time[index]=now;
        }
        return;
    }
    if (c->seen[index] && (uint32_t)(now-c->sequence_time[index]) < CAR_LINK_TIMEOUT_MS) {
        delta = (uint8_t)(f->sequence-c->last_sequence[index]);
        if (delta == 0u || delta >= 128u) { ++c->duplicates; return; }
    }
    c->seen[index]=1; c->last_sequence[index]=f->sequence; c->sequence_time[index]=now;
    if (f->type == PROTOCOL_PATH) {
        c->path=*f; c->path_time=now; c->have_path=1;
        if (c->state == CAR_RUNNING && !path_ready(c, now)) stop(c, CAR_FAULT, STOP_PATH);
    } else if (f->command == CMD_START) {
        if (path_ready(c, now)) { c->state=CAR_RUNNING; c->reason=STOP_NONE; }
        else ++c->starts_rejected;
    }
}
void car_tick(car_t *c, uint32_t now) {
    int16_t turn, base;
    if (c->state != CAR_RUNNING) { c->left_request=0; c->right_request=0; return; }
    if (!path_ready(c, now)) { stop(c, CAR_FAULT, STOP_LINK); return; }
    /* Bench-only normalized demands: NOT speed feedback, PID, PWM, or calibrated steering. */
    base = c->path.bend > 500u ? 80 : 120;
    turn = (int16_t)(c->path.error / 20);
    c->left_request=(int16_t)(base+turn); c->right_request=(int16_t)(base-turn);
}
const char *car_state_name(car_state_t state) {
    switch (state) {
    case CAR_IDLE: return "IDLE";
    case CAR_RUNNING: return "RUNNING";
    case CAR_STOPPED: return "STOPPED";
    case CAR_FAULT: return "FAULT";
    default: return "UNKNOWN";
    }
}
