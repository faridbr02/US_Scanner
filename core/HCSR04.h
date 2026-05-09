/*
 * HCSR04.h
 *
 *  Created on: Feb 22, 2026
 *      Author: FARID
 */

#ifndef HCSR04_H_
#define HCSR04_H_

#include "stm32f4xx_hal.h"

typedef struct {
	TIM_HandleTypeDef* htim;
	GPIO_TypeDef *trig_port;
	uint16_t  trig_pin;
	GPIO_TypeDef *echo_port;
	uint16_t  echo_pin;
	uint16_t max_distance;
} HCSR04_HandleTypeDef;


typedef enum  {
	HCSR04_OK = 0,
	HCSR_ERROR= 1,
	HCSR04_TIMEOUT=2
} HCSR04_State ;


void HCSR04_Init(HCSR04_HandleTypeDef *hcsr04,
		TIM_HandleTypeDef* htim,
		GPIO_TypeDef *trig_port,
		uint16_t  trig_pin,
		GPIO_TypeDef *echo_port,
		uint16_t  echo_pin,
		uint16_t max_dis );





HCSR04_State get_Distance(HCSR04_HandleTypeDef* hcsr04, float *distance);


#endif /* HCSR04_H_ */
