#ifndef DS3231_h
#define DS3231_h
#endif 

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <time.h> 


enum display_options {SECOND, MINUTE, HOUR, DAY_OF_WEEK, DATE, MONTH, YEAR, TIME, ALL};

enum run_states {clock_stop, clock_start};

#define DS3231_I2C_ADDRESS  0X68


void ds3231_init(const struct device *i2c_dev);
bool ds3231_set_time(const struct device *i2c_dev, struct tm *time);
bool ds3231_get_time(const struct device *i2c_dev, struct tm *time);
void ds3231_start_clock(const struct device *i2c_dev);
void ds3231_stop_clock(const struct device *i2c_dev);



#define DS3231_REG_SECONDS   0x00
#define DS3231_REG_MINUTES   0x01
#define DS3231_REG_HOURS     0x02
#define DS3231_REG_DAY       0x03
#define DS3231_REG_DATE      0x04
#define DS3231_REG_MONTH     0x05
#define DS3231_REG_YEAR      0x06
#define DS3231_REG_CONTROL   0x0E
#define DS3231_REG_STATUS    0x0F

#define DS3231_STATUS_OSF    0x80  // prob not needed
#define DS3231_CONTROL_CONV  0x20  // prob not needed

// error handling 
#define DS3231_ERR_OK        0
#define DS3231_ERR_COMM      -1
#define DS3231_ERR_PARAM     -2



// utiliies , handles leap year stuff --> not really necessary but a nice edge case consideration 


#define BCD_TO_BIN(val) (((val) & 0x0F) + ((val) >> 4) * 10)
#define BIN_TO_BCD(val) (((val) / 10) << 4) + ((val) % 10)




// last revised : 05/06/2024 

// subject to change 