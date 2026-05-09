#include "HCSR04.h"
#include "Helpers.h"

void HCSR04_Init(HCSR04_HandleTypeDef *hcsr04,
                TIM_HandleTypeDef* htim,
                GPIO_TypeDef *trig_port,
                uint16_t  trig_pin,
                GPIO_TypeDef *echo_port,
                uint16_t  echo_pin,
				uint16_t max_dis)
{
    hcsr04->htim = htim;
    hcsr04->trig_pin = trig_pin;
    hcsr04->trig_port = trig_port;
    hcsr04->echo_pin = echo_pin;
    hcsr04->echo_port = echo_port;
    hcsr04->max_distance = max_dis;

    HAL_TIM_Base_Start(hcsr04->htim);
}


HCSR04_State get_Distance(HCSR04_HandleTypeDef* hcsr04, float *distance)
{
    uint32_t pMillis;
    uint32_t duration = 0;

    // Trigger : Impulsion de 10us
    HAL_GPIO_WritePin(hcsr04->trig_port, hcsr04->trig_pin, GPIO_PIN_RESET);
    HAL_Delay(1);
    HAL_GPIO_WritePin(hcsr04->trig_port, hcsr04->trig_pin, GPIO_PIN_SET);
    __HAL_TIM_SET_COUNTER(hcsr04->htim, 0);
    while (__HAL_TIM_GET_COUNTER(hcsr04->htim) < 10);
    HAL_GPIO_WritePin(hcsr04->trig_port, hcsr04->trig_pin, GPIO_PIN_RESET);

    // Attendre que l'ECHO passe a HIGH
    pMillis = __HAL_TIM_GET_COUNTER(hcsr04->htim);
    while (!(HAL_GPIO_ReadPin(hcsr04->echo_port, hcsr04->echo_pin)))
    {
        if ((__HAL_TIM_GET_COUNTER(hcsr04->htim) - pMillis) > 30000 ) {
        	*distance = 0;
        	return HCSR04_TIMEOUT;
        }
    }

    // RESET le compteur
    __HAL_TIM_SET_COUNTER(hcsr04->htim, 0);

    //Attendre que l'ECHO repasse à LOW
    pMillis = __HAL_TIM_GET_COUNTER(hcsr04->htim);

    while (HAL_GPIO_ReadPin(hcsr04->echo_port, hcsr04->echo_pin))
    {
        if ((__HAL_TIM_GET_COUNTER(hcsr04->htim) - pMillis) > hcsr04->max_distance){
        	*distance = 0;
        	return HCSR04_TIMEOUT;
        }
    }

    // Lecture de la durée
    duration = __HAL_TIM_GET_COUNTER(hcsr04->htim);

    //  Calcul (Vitesse du son = 0.0343 cm/us) Distance = (Temps * 0.0343) / 2  => ce qui revient à Temps / 58
    *distance = (float)duration / 58.0f;

    return HCSR04_OK;
}
