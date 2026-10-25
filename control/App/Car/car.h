#ifndef YEYE_CAR_H
#define YEYE_CAR_H
#include "protocol.h"
#define CAR_LINK_TIMEOUT_MS 200u
#define CAR_PROCESSING_LIMIT_MS 100u
#define CAR_MIN_CONFIDENCE 40u
typedef enum { CAR_IDLE, CAR_RUNNING, CAR_STOPPED, CAR_FAULT } car_state_t;
typedef enum { STOP_NONE, STOP_COMMAND, STOP_LINK, STOP_PATH, STOP_TRANSPORT } stop_reason_t;
typedef struct {
    car_state_t state;
    stop_reason_t reason;
    protocol_frame_t path;
    uint32_t path_time, sequence_time[2], duplicates, starts_rejected;
    uint8_t have_path, seen[2], last_sequence[2];
    int16_t left_request, right_request;
} car_t;
void car_init(car_t *car);
void car_receive(car_t *car, const protocol_frame_t *frame, uint32_t now);
void car_tick(car_t *car, uint32_t now);
void car_transport_fault(car_t *car);
const char *car_state_name(car_state_t state);
#endif
