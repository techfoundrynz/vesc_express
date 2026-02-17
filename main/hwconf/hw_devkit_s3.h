#ifndef HW_DEVKIT_S3_H_
#define HW_DEVKIT_S3_H_

#define HW_NAME                 "DevKit S3"
#define HW_TARGET               "esp32s3"
#define HW_UART_COMM

#define HW_INIT_HOOK()          hw_init()

// UART
#define UART_NUM                0
#define UART_BAUDRATE           115200
#define UART_TX                 43
#define UART_RX                 44

// Functions
void hw_init(void);

#endif /* HW_DEVKIT_S3_H_ */
