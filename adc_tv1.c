/*ADC sample module 
 ---------------------------------------------------------------------------------------------------
 *2014.6.18 change log:
 *construct into object style, wrapped by data_t gData.
 *With only one object instance(gData), object reference is omitted in operation parameter list. 
 ---------------------------------------------------------------------------------------------------
 *2014.6.1
 *initialising called by entry.c 
 *service called by cmd.c ( initialized from PC, by entry gADC[] )
 * 
 * 
 */

#include "stm32f10x_conf.h"
#include "stm32f10x_usart.h"
#include "stm32f10x_tim.h"
#include "stm32f10x_adc.h"
#include <string.h>
#include <math.h>
#include "cmd_type.h"
#define SW_R	0
#define SW_UI 	1
#define SW_NTC 	2
#define SW_CAN	3
#define SW_232	4
#define SW_485 	5
int gSW_status = SW_R;
extern pga_t gPGA_ports;
int write_sport(sp_port_t * pSPort, uint32_t value);
void data_t_init(void);
int gThermo_flag=UNSET_;
data_t gData;
sw_t gSW={
	{GPIOC, GPIO_Pin_14},	// sw_232_pin
	{GPIOC, GPIO_Pin_13},	// sw_CAN_pin
	{GPIOB, GPIO_Pin_15},	// swU_IR_pin
	{GPIOB, GPIO_Pin_14},	// swUI_R_pin
	};

#define ADC1_DR_Address    ((uint32_t)0x4001244C)
#define END_FLAG '\0'
#define JEXTTRIG_SW		0x111<< 12
#define JEXTTRIG_CC1	0x011<< 12
#define SAMPL_41_5 0x100
#define SAMPL0_41_5 0x100 << 0
#define JCH_NUM(D) (D-1)<<20
#define JCH0(D) D<<15
#define ADC1_ON()  ADC1->CR2 |= ADC_CR2_ADON
#define ADC1_JSW_START() ADC1->CR2 |= ADC_CR2_JSWSTART

void delay_loop(__IO int ticks_)
{
	while(1){
		if (ticks_ == 0)
			break;
		asm("nop");
		ticks_ -= 1;
	}	
}


void data_t_service(void)
{
	//if (gData.sample_flag == UNSET_)
	//	return ;	
	//new data, format and upload if neeeded 
	//gData.sample_flag = UNSET_;
	//gData.format();
	if (gData.need_upload_flag == SET_){ //!!!! mutex may be need  here.
		gData.need_upload_flag = UNSET_;
		gData.upload();
	}

}

void data_t_upload(void)
{
	//printf(&(gData.str_buffer[0]));
	int tail = gData.ad_buffer.tail;
	while (gData.ad_buffer.tail != gData.ad_buffer.head){
		print2usb(&(gData.ad_buffer._buffer[tail].slot[0]));
		gData.ad_buffer.tail += 1;
		if (gData.ad_buffer.tail == AD_BUFF_LEN )
			gData.ad_buffer.tail = 0;
	}
}

void data_t_run(char* cmd)
{
	gData.running_flag = SET_;
}

void data_t_stop(char* cmd)
{
	gData.running_flag = UNSET_;
}

void data_t_cfg(char* cmd);
void data_t_set_interval(char* cmd);
void data_t_set_channel(char* cmd);
void data_t_set_manual(char* cmd);
__IO function_t gAdc_cfg[4]={
	{"manual",data_t_set_manual},// "adc:sample:\r" to sample
	{"interval",data_t_set_interval},// "adc:run:\r" to set running_flag
	{"channel",data_t_set_channel},// "adc:run:\r" to set running_flag
	{0,0},// "adc:cfg:auto:N\r" to set manual_flag
};

void data_t_cfg(char* cmd)
{
	return deal_cmd__(cmd,&gAdc_cfg[0]);
}

void data_t_set_manual(char* cmd)
{
	if (cmd[0] == 'y' || cmd[0] == 'Y')
		gData.manual_flag = SET_;
	else if ( cmd[0] == 'n' || cmd[0] == 'N')
		gData.manual_flag = UNSET_;
}

void data_t_set_interval(char* cmd)
{
	uint16_t seconds;
	seconds = atoi(cmd);
	gData.delay = RT_TICK_PER_SECOND / seconds; // delay for speeding up
}

void data_t_set_channel(char* cmd)
{
	gData.channel = atoi(cmd); // delay for speeding up
}


#define set_485_on	 GPIO_SetBits(gSW.sw_CAN_pin.port,gSW.sw_CAN_pin.pin)
#define set_CAN_on	 GPIO_ResetBits(gSW.sw_CAN_pin.port,gSW.sw_CAN_pin.pin)
#define set_232_off	 GPIO_SetBits(gSW.sw_232_pin.port,gSW.sw_232_pin.pin)
#define set_232_on	 GPIO_ResetBits(gSW.sw_232_pin.port,gSW.sw_232_pin.pin)
#define set_IN_U	 GPIO_SetBits(gSW.swU_IR_pin.port,gSW.swU_IR_pin.pin)
#define set_IN_IR	 GPIO_ResetBits(gSW.swU_IR_pin.port,gSW.swU_IR_pin.pin)
#define set_SW_UI	 GPIO_SetBits(gSW.swUI_R_pin.port,gSW.swUI_R_pin.pin)
#define set_SW_R	 GPIO_ResetBits(gSW.swUI_R_pin.port,gSW.swUI_R_pin.pin)
#define sw_485		 set_232_off;set_485_on;
#define sw_CAN	 	set_232_off;set_CAN_on;
#define sw_232		 set_232_on
#define sw_U		 sw_CAN;set_IN_U;set_SW_UI;
#define sw_I		 sw_CAN;set_IN_IR;set_SW_UI;
#define sw_R		 sw_CAN;set_IN_IR;set_SW_R;

////////////////////////////////////////////////////////////////////////////////////////////////////
void switch_RAT(char* cmd)
{
	switch  (*cmd){
		case 'R': // setup as R input
			sw_R;
			break;
		case 'U': // setup as A1 or A2 channel 
			sw_U;
			break;
		case 'I': // setup as NTC channel
			sw_I;
			break;
		case 'C':
			if (*(cmd+1)=='A' && *(cmd+2)=='N')
				sw_CAN;
			break;
		case '4':
			if (*(cmd+1)=='8' && *(cmd+2)=='5')
				sw_485;
			break;
		case '2':
			if (*(cmd+1)=='3' && *(cmd+2)=='2')
				sw_232;
			break;
		default :
			rt_kprintf("switch_RAT bad parameter ...! should be R|U|I|NTC|CAN|485|232 \r\n");
			break;
	}
}



void data_t_format(void)
{
	int last=0;
	uint16_t *pLength;
	uint16_t *pSignal;
	uint16_t *pStart;
	//pStart = (uint16_t*) &(gData.str_buffer[4]);
	//switch (gData.running_flag){
	//	case SET_:
	//		if (gData.current == 0 )
	//		 	last = DATA_NUM - 1 ;
	//		else
	//			last = gData.current - 1 ;
	//		break;
	//	default:
	//		last = 0;
	//}
	//pLength = pStart + last*2;
	//pSignal = pStart + last*2 + 1;
	//*pLength = gData.ADC_sample_group[last].length;
	//*pSignal = gData.ADC_sample_group[last].signal;

//	sprintf( str + last * DATA_LEN, 
//		"%04x%04x",
//		gData.ADC_sample_group[last].length,
//		gData.ADC_sample_group[last].signal);
}

void data_t_reset(void)
{
	gData.counter1 = 0 ;
	gData.ad_buffer.current = &(gData.ad_buffer._buffer[0].slot[2]); //'0x::.......................'
	TIM_SetCounter(TIM2,0);
}
#define _A0 gData.ADC_sample[0]
#define _A1 gData.ADC_sample[1]
#define _A2 gData.ADC_sample[2]
#define _A3 gData.ADC_sample[3]
#define OVER_FLOW(x)  ((x & 0xfff)==0xfff)
#define NOT_OVER_FLOW(x)  ((x & 0xfff)!=0xfff)
#define filter_size 50
//uint16_t filter_buffer[filter_size];
#define SMP_DELAY 10
#define DATA0_ADDR &(gData.ad_buffer._buffer[gData.ad_buffer.head].slot[2])
#define DATAn_ADDR &(gData.ad_buffer._buffer[gData.ad_buffer.head].slot[27])
#define VALUEX *(gData.ad_buffer.current + 0)
#define VALUEY *(gData.ad_buffer.current + 1)
#define COUNT  *(gData.ad_buffer.current + 2)
uint16_t last_Yvalue=0;
void data_t_sample(void) {
//	int i;
//	uint32_t sum;
//	uint32_t signal;
//	uint8_t channel;
//	uint8_t x10_flag;
//	uint16_t current_Yvalue;
	
//	if (gData.channel ==0 && gData.ADC_[1] < 0xfff){
//		channel =  1;
//		x10_flag = SET_;
//	}else{
//		channel = gData.channel;
//		x10_flag = UNSET_;
//	}
//	sum = 0;
//	for (i=0;i<filter_size;i++){
//		sum +=  (gData.ADC_[channel] & 0xfff); // sampling data from DMA-memory area gData.ADC_
//		delay_loop(SMP_DELAY); // delay sometime for next sample
//	}
//	if (x10_flag==SET_)
//		current_Yvalue = (sum / filter_size) | (0x1<<15);
//	else
//		current_Yvalue = (sum / filter_size) ;
//	if (abs(current_Yvalue-last_Yvalue) > 2 || COUNT > 256){ // new value 
		*(gData.ad_buffer.current + 0) = (gData.ADC_[0] & 0xfff); 
		*(gData.ad_buffer.current + 1) = (gData.ADC_[1] & 0xfff); 
		*(gData.ad_buffer.current + 2) = (gData.ADC_[2] & 0xfff); 
		*(gData.ad_buffer.current + 3) = (gData.ADC_[3] & 0xfff); 
		gData.ad_buffer.current += 4; //point to  next item
		if ( (gData.ad_buffer.current > DATAn_ADDR)  ){ // one slot stuffed
			gData.ad_buffer.head += 1;// first,adjust  write_slot 
			if (gData.ad_buffer.head == AD_BUFF_LEN)
				gData.ad_buffer.head = 0;
			gData.ad_buffer.current = DATA0_ADDR; // second, adjust write_head(index)
			gData.need_upload_flag = SET_;  // set flag to start upload later
		}
}

// loop buffer init
void ad_buffer_init(void)
{
	int i;
	for (i=0;i<AD_BUFF_LEN;i++){
		gData.ad_buffer._buffer[i].slot[0]=0x7830; // '0x::'
		gData.ad_buffer._buffer[i].slot[1]=0x3a3a; // '0x::'
	}
	gData.ad_buffer.head = 0; 
	gData.ad_buffer.tail = 0;
	gData.ad_buffer.current = &(gData.ad_buffer._buffer[0].slot[2]); //'0x::.......................'
	*(gData.ad_buffer.current + 2)  = 1; //for new value , set count to 1
}



void data_t_init(void){
	gData.service = data_t_service;
	gData.cfg= data_t_cfg;
	gData.run = data_t_run;
	gData.stop = data_t_stop;
	gData.upload = data_t_upload;
	gData.format = data_t_format;
	gData.sample = data_t_sample;
	gData.channel= 0;
	gData.reset  = data_t_reset;
	gData.reset();
	//gData.str_buffer[0] = 0x7830; //0x
	//gData.str_buffer[1] = 0x3a3a; //::
	gData.delay= 1;
	gData.sample_flag = UNSET_ ;
	gData.need_upload_flag = UNSET_ ;
	gData.running_flag = UNSET_ ;
	gData.manual_flag = UNSET_ ;
	ad_buffer_init();


}


///////////////////////////////////////////////////////////////////////////////////
void RCC_ADC_init(void)
{
	/* Enable DMA clock */
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_DMA1, ENABLE);

	/* Enable ADC1 and GPIOC clock */
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1 | RCC_APB2Periph_GPIOA | RCC_APB2Periph_AFIO, ENABLE);
	RCC_APB2PeriphClockCmd(RCC_APB1Periph_USART2 | RCC_APB1Periph_TIM2 , DISABLE);
	ADC_DeInit(ADC1);
	RCC_ADCCLKConfig(RCC_PCLK2_Div6);

}

///////////////////////////////////////////////////////////////////////////////////
#define RCC_SW_init() RCC_APB2PeriphClockCmd( RCC_APB2Periph_GPIOC, ENABLE)
///////////////////////////////////////////////////////////////////////////////////

void swR_init(void)
{
	RCC_SW_init();
	GPIO_InitTypeDef GPIO_InitStructure;
	int i=0;
	port_pin_t *pPin = (port_pin_t*) &gSW; 
	for(i=0;i<4;i++){
		GPIO_InitStructure.GPIO_Pin = pPin->pin ;
		GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
		GPIO_InitStructure.GPIO_Speed = GPIO_Speed_2MHz;
		GPIO_Init(pPin->port, &GPIO_InitStructure);
		pPin++;
	}
}
void pga_init(void);
///////////////////////////////////////////////////////////////////////////////////
void GPIO_ADC_init(void)
{
	GPIO_InitTypeDef GPIO_InitStructure;

	/* Configure PA.0-3 (ADC Channel 0-3) as analog input -------------------------*/
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_4;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	pga_init();
	
}

///////////////////////////////////////////////////////////////////////////////////
void DMA_ADC_init(void)
{
	DMA_InitTypeDef DMA_InitStructure;
	DMA_DeInit(DMA1_Channel1);
	DMA_InitStructure.DMA_PeripheralBaseAddr = ADC1_DR_Address;
	DMA_InitStructure.DMA_MemoryBaseAddr = (u32)&(gData.ADC_[0]);
	DMA_InitStructure.DMA_DIR = DMA_DIR_PeripheralSRC;
	DMA_InitStructure.DMA_BufferSize = 6; // A0~A5 round circularly
	DMA_InitStructure.DMA_PeripheralInc = DMA_PeripheralInc_Disable;
	DMA_InitStructure.DMA_MemoryInc = DMA_MemoryInc_Enable;
	DMA_InitStructure.DMA_PeripheralDataSize = DMA_PeripheralDataSize_HalfWord;
	DMA_InitStructure.DMA_MemoryDataSize = DMA_MemoryDataSize_HalfWord;
	DMA_InitStructure.DMA_Mode = DMA_Mode_Circular;
	DMA_InitStructure.DMA_Priority = DMA_Priority_High;
	DMA_InitStructure.DMA_M2M = DMA_M2M_Disable;
	DMA_Init(DMA1_Channel1, &DMA_InitStructure);

	/* Enable DMA channel1 */
	DMA_Cmd(DMA1_Channel1, ENABLE);
}

void status_init()
{
	//set_COM_off();//com relay off
	set_CAN_on;//can relay off
	set_232_off;//232 relay off
	sw_R;
}
void ds18b20_init(void);
///////////////////////////////////////////////////////////////////////////////////
void adc_config(void)
{
	gData.__init__ = data_t_init;
	gData.__init__();
	ADC_InitTypeDef ADC_InitStructure;
	RCC_ADC_init();
	GPIO_ADC_init();
	DMA_ADC_init();
	//ds18b20_init(); // hook 1wire digit_thermo DS18B02 

	// pga and switch init here
	pga_init();
	swR_init();
	//status_init();

	/* ADC1 configuration ------------------------------------------------------*/
	ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;
	ADC_InitStructure.ADC_ScanConvMode = ENABLE;
	ADC_InitStructure.ADC_ContinuousConvMode = ENABLE;
	ADC_InitStructure.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
	ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;
	ADC_InitStructure.ADC_NbrOfChannel = 6;
	ADC_Init(ADC1, &ADC_InitStructure);

	/* ADC1 regular channel 0 configuration */ 
	ADC_RegularChannelConfig(ADC1, ADC_Channel_0, 1, ADC_SampleTime_55Cycles5);
	ADC_RegularChannelConfig(ADC1, ADC_Channel_1, 2, ADC_SampleTime_55Cycles5);
	ADC_RegularChannelConfig(ADC1, ADC_Channel_2, 3, ADC_SampleTime_55Cycles5);
	ADC_RegularChannelConfig(ADC1, ADC_Channel_3, 4, ADC_SampleTime_55Cycles5);
	ADC_RegularChannelConfig(ADC1, ADC_Channel_4, 5, ADC_SampleTime_55Cycles5);
	ADC_RegularChannelConfig(ADC1, ADC_Channel_5, 6, ADC_SampleTime_55Cycles5);

	/* Enable ADC1 DMA */
	ADC_DMACmd(ADC1, ENABLE);

	/* Enable ADC1 */
	ADC_Cmd(ADC1, ENABLE);

	/* Enable ADC1 reset calibaration register */   
	ADC_ResetCalibration(ADC1);
	/* Check the end of ADC1 reset calibration register */
	while(ADC_GetResetCalibrationStatus(ADC1));

	/* Start ADC1 calibaration */
	ADC_StartCalibration(ADC1);
	/* Check the end of ADC1 calibration */
	while(ADC_GetCalibrationStatus(ADC1));

	/* Start ADC1 Software Conversion */ 
	ADC_SoftwareStartConvCmd(ADC1, ENABLE);

}

void get_temp(void)
{

	gThermo_flag=SET_;
}


void sample_temp(void)
{

	int PT,NTC,status;
	char str_buffer[64];
	if ( gThermo_flag==UNSET_)
		return
	gThermo_flag=UNSET_;
	status = gSW_status;
	//switch_NTC();
 	/*Warning: sleep 1ms to be stable */
	//rt_thread_delay( RT_TICK_PER_SECOND/1000);
	PT  = gData.ADC_[4];
	NTC = gData.ADC_[3];
	//format:0t:NNNNPPPP
	sprintf(str_buffer, "0t:%04x%04x",NTC,PT);
	print2usb(str_buffer);
	//printf(str_buffer);
	//return to origin status
}


int pga_set(char* cmd);

__IO function_t gAdc[8]={
	{"sample",data_t_sample},// "adc:sample:\r" to sample
	{"run",data_t_run },// "adc:run:\r" to set running_flag
	{"stop",data_t_stop},// "adc:stop:\r" to clear running_flag
	{"cfg",data_t_cfg},// "adc:cfg:auto:Y\r" to clear manual_flag
	{"swt",switch_RAT},// "adc:swt:R|U|I|NTC|CAN|232|485:\r" to switch to R input_mode
	{"pga",pga_set},// "adc:pga:set:R|A|r:xxx:a:xxx\r" to set pga R|A|B value
	{"temp",get_temp},// "adc:temp:\r" to get temprature
	{0,0},// "adc:cfg:auto:N\r" to set manual_flag
};

/**********************************************************/
__IO rt_uint8_t ad_sample_stack[ 512 ];
__IO struct rt_thread ad_sample_thread;
__IO void ad_sample_thread_entry(void* parameter)
{
	while (1){
		if( gData.running_flag == SET_)
			gData.sample();
			sample_temp();
		rt_thread_delay( gData.delay); /* sleep 0.5 second and switch to other thread */
	}
}


