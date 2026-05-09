/*
 * Helpers.h
 *
 *  Created on: Feb 26, 2026
 *      Author: FARID
 */

#ifndef INC_HELPERS_H_
#define INC_HELPERS_H_

#include "stm32f4xx_hal.h"

uint16_t TimtoDistance(uint16_t distane_cm);
uint16_t DistanceToTime(uint16_t distane_cm);


uint8_t TimetoAngle(uint16_t time);
uint16_t AngletoTime(uint8_t angle);



void send_data(UART_HandleTypeDef* huart, uint16_t angle,uint16_t distance);

#endif /* INC_HELPERS_H_ */
