/*
 * UltraSonicScanner.c
 *
 *  Created on: Mar 1, 2026
 *      Author: FARID
 */
#include "UltrasonicScanner.h"
#include "HCSR04.h"
#include "Helpers.h"
#include "stdio.h"



void UScanner_System_Init(
								UltrasonicScanner_HandleTypeDef *hus,
								HCSR04_HandleTypeDef* hcsr04,
								TIM_HandleTypeDef* htim_servo,
								UART_HandleTypeDef* uart_comm,
								System_config* sys_config
							){
	hus->hcsr04 = hcsr04;
	hus->htim_servo= htim_servo;
	hus->uart_comm = uart_comm;
	hus->sys_config = sys_config;
	hus->sys_state = US_SYSTEM_READY;

}
void UScanner_System_Update(
								UltrasonicScanner_HandleTypeDef *hus,
								System_config* sys_config,
								HCSR04_HandleTypeDef *hcsr04
							){
	hus->sys_config = sys_config;
	hus->hcsr04->max_distance = DistanceToTime(sys_config->max_distance);

	hus->sys_state = US_SYSTEM_CONFIG;

}
void UScanner_UpdateConfigFromUART(char* buffer, System_config* config) {
    int left_angle, right_angle, step, max_distance;
    // sscanf cherche le format : entier, entier, entier, entier
    if (sscanf(buffer, "%d,%d,%d,%d", &left_angle, &right_angle, &step, &max_distance) == 4) {
        config->max_left_angle = (uint8_t) left_angle;
        config->max_right_angle = (uint8_t)right_angle;
        config->rotation_step = (uint8_t) step;
        config->max_distance = (uint16_t)max_distance;
    }
}
void UScanner_System_Start(UltrasonicScanner_HandleTypeDef *hus){

	//get constraints
	uint16_t left_angle_tim = AngletoTime(hus->sys_config->max_left_angle);
	uint16_t right_angle_tim = AngletoTime(hus->sys_config->max_right_angle);
	uint8_t step = hus->sys_config->rotation_step;


	float distance;
	float distances[3];
	//system start
	while(1){
		if(hus->sys_state ==US_SYSTEM_CONFIG ) return;//Si une mise a jour via uart est arrivé, sortir pour L'effectuer

		for(uint16_t angle = left_angle_tim ; angle <=right_angle_tim ; angle += step){
			__HAL_TIM_SET_COMPARE(hus->htim_servo, TIM_CHANNEL_1, angle);
			HAL_Delay(1);
			for(size_t i = 0; i<3; i++){
				get_Distance( hus->hcsr04, &distance );
				distances[i] = distance;
			}
			for(size_t i = 0;i < 3; i++){
				for(size_t j = i+1; j < 3; j++){
					if (distances[i] > distances[j]){
						float temp = distances[i];
						distances[i] = distances[j];
						distances[j] = temp;
					}
				}
			}
			uint8_t current_angle = TimetoAngle(angle);
			send_data(hus->uart_comm,current_angle,distances[1]);

		}
		for(uint16_t angle = right_angle_tim ; angle > left_angle_tim ; angle -= step){


			__HAL_TIM_SET_COMPARE(hus->htim_servo, TIM_CHANNEL_1, angle);
			HAL_Delay(1);



			for(size_t i = 0;i<3;i++){
							get_Distance(hus->hcsr04,&distance);
							distances[i] = distance;
						}
						for(size_t i = 0;i < 3; i++){
							for(size_t j = i+1; j < 3; j++){
								if (distances[i] > distances[j]){
									float temp = distances[i];
									distances[i] = distances[j];
									distances[j] = temp;
								}
							}
						}

			uint8_t current_angle = TimetoAngle(angle);
			send_data(hus->uart_comm,current_angle,distances[1]);

	}

	}
}
