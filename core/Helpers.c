/*
 * Helpers.c
 *
 *  Created on: Feb 26, 2026
 *      Author: FARID
 */

#include "Helpers.h"

uint16_t DistanceToTime(uint16_t distane_cm){

	return distane_cm * 58.0f;
}


uint8_t TimetoAngle(uint16_t time){
	return (time - 1000) * 180.0f / 1000.0f;
}
uint16_t AngletoTime(uint8_t angle){
	// On s'assure que l'angle ne dépasse pas 180 pour éviter les débordements
	    if (angle > 180) angle = 180;

	    return (uint16_t)((angle * 1000.0f / 180.0f) + 1000);
}




void send_data(UART_HandleTypeDef* huart, uint16_t angle,uint16_t distance){

	char msg[20];
	sprintf(msg, "%d,%d\r\n",angle,(int)distance);
	HAL_UART_Transmit(huart, (uint8_t*)msg, strlen(msg), 100);

}
