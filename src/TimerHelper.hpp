#pragma once

#include <Arduino.h>

void registerTimerTask(void (*task)(void), uint32_t freq)
{
    static int timer_num = 0;
    static hw_timer_t *timers[256] = {0};

    timers[timer_num] = timerBegin(timer_num, 80, true);
    timerAttachInterrupt(timers[timer_num], task, true);
    timerAlarmWrite(timers[timer_num], 1000000 / freq, true);
    timerAlarmEnable(timers[timer_num]);
    timer_num++;
}