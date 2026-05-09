/*
 * UltrasonicScanner.h
 *
 *  Created on: Feb 26, 2026
 *      Author: FARID
 */

#ifndef INC_ULTRASONICSCANNER_H_
#define INC_ULTRASONICSCANNER_H_

#include "stm32f4xx_hal.h"
#include "HCSR04.h"

typedef struct {

	uint16_t max_distance;
	uint8_t rotation_step;
	uint8_t max_left_angle;
	uint8_t max_right_angle;

}System_config;

typedef enum{
	US_SYSTEM_READY,
	US_SYSTEM_CONFIG,
	US_SYSTEM_ERROR,
}
UltrasonicScanner_state;

typedef struct {
	HCSR04_HandleTypeDef* hcsr04;
	TIM_HandleTypeDef* htim_servo;
	UART_HandleTypeDef* uart_comm;
	System_config* sys_config;
	UltrasonicScanner_state sys_state;

} UltrasonicScanner_HandleTypeDef;


void UScanner_System_Init(
								UltrasonicScanner_HandleTypeDef *hus,
								HCSR04_HandleTypeDef* hcsr04,
								TIM_HandleTypeDef* htim_servo,
								UART_HandleTypeDef* uart_comm,
								System_config* sys_config
							);


void UScanner_UpdateConfigFromUART(char* buffer, System_config* config);

void UScanner_System_Update(
								UltrasonicScanner_HandleTypeDef *hus,
								System_config* sys_config,
								HCSR04_HandleTypeDef *hcsr04
							);


void UScanner_System_Start(UltrasonicScanner_HandleTypeDef *hus);



#endif /* INC_ULTRASONICSCANNER_H_ */
