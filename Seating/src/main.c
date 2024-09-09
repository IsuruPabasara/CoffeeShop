#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gap.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>

#define STACKSIZE 1024
#define THREAD_BLE_PRIORITY 7
#define THREAD_PRES_PRIORITY 9
#define THREAD_TEMP_PRIORITY 11

LOG_MODULE_REGISTER(enviorenment_sensor, LOG_LEVEL_DBG);
K_MUTEX_DEFINE(i2c_mutex);

typedef struct {
	float pressure;
} SensorLPS22HHReading;
/* STEP 3.2 - Define the message queue */
K_MSGQ_DEFINE(my_LPS22HHmsgq, sizeof(SensorLPS22HHReading), 16, 4);

typedef struct {
	float temperature;
} SensorSTTS751Reading;
/* STEP 3.2 - Define the message queue */
K_MSGQ_DEFINE(my_STTS751msgq, sizeof(SensorSTTS751Reading), 16, 4);

/*
 *
 Bluetooth thread
 *
*/

#define CUSTOM_SERVICE_UUID   BT_UUID_INIT_16(0x1234)
#define CUSTOM_TEMP_UUID      BT_UUID_INIT_16(0x1234)
#define CUSTOM_PRESSURE_UUID  BT_UUID_INIT_16(0x1234)

static struct bt_uuid_16 custom_service_uuid = BT_UUID_INIT_16(0x1234);
static struct bt_uuid_16 custom_temp_uuid = BT_UUID_INIT_16(0x1235);
static struct bt_uuid_16 custom_pressure_uuid = BT_UUID_INIT_16(0x1236);
static struct bt_uuid_16 custom_sensor_uuid = BT_UUID_INIT_16(0x1237);

/* static struct bt_uuid_128 custom_temp_uuid = BT_UUID_INIT_128(
    0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
    0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe
);

static struct bt_uuid_128 custom_pressure_uuid = BT_UUID_INIT_128(
    0x34, 0x12, 0x78, 0x56, 0x9a, 0xbc, 0xde, 0xf0,
    0x34, 0x12, 0x78, 0x56, 0x9a, 0xbc, 0xde, 0xf0
); */

static struct bt_le_adv_param adv_param = BT_LE_ADV_PARAM_INIT(
    (
        BT_LE_ADV_OPT_CONNECTABLE
    ),      /* Connectable advertising */
    800,    /* Min Advertising Interval 500ms (800*0.625ms) */
    1001,   /* Max Advertising Interval 625.625ms (1001*0.625ms) */
    NULL    /* Set to NULL for undirected advertising */
); 

static const struct bt_data adv_packet_array[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_NO_BREDR),
    BT_DATA(
        BT_DATA_NAME_COMPLETE, 
        CONFIG_BT_DEVICE_NAME, 
        sizeof(CONFIG_BT_DEVICE_NAME) - 1
        ),

};

static const struct bt_data scan_packet_array[] = {
    // now we will use a "real" BLE service UUID
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, BT_UUID_16_ENCODE(0x1234)),
};

static void on_connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
		LOG_ERR("Connection failed (err %u)\n", err);
		return;
	}
	LOG_INF("Connected\n");
}

static void on_disconnected(struct bt_conn *conn, uint8_t reason)
{
	LOG_INF("Disconnected (reason %u)\n", reason);
}

struct bt_conn_cb connection_callbacks = {
	.connected = on_connected,
	.disconnected = on_disconnected,
};

BT_GATT_SERVICE_DEFINE(
    my_custom_service,
    BT_GATT_PRIMARY_SERVICE(&custom_service_uuid),
    BT_GATT_CHARACTERISTIC(
        &custom_temp_uuid.uuid,
        BT_GATT_CHRC_NOTIFY,
        BT_GATT_PERM_NONE,
        NULL, NULL, NULL
    ),
    BT_GATT_CCC(
        NULL,
        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE
    ),
    BT_GATT_CHARACTERISTIC(
        &custom_pressure_uuid.uuid,
        BT_GATT_CHRC_NOTIFY,
        BT_GATT_PERM_NONE,
        NULL, NULL, NULL
    ),
    BT_GATT_CCC(
        NULL,
        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE
    ),
    BT_GATT_CHARACTERISTIC(
        &custom_sensor_uuid.uuid,
        BT_GATT_CHRC_NOTIFY,
        BT_GATT_PERM_NONE,
        NULL, NULL, NULL
    ),
    BT_GATT_CCC(
        NULL,
        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE
    )
);

/* BT_GATT_SERVICE_DEFINE(
    my_custom_service,
    BT_GATT_PRIMARY_SERVICE(CUSTOM_SERVICE_UUID),
    BT_GATT_CHARACTERISTIC(
        &CUSTOM_TEMP_UUID,
        BT_GATT_CHRC_NOTIFY,
        BT_GATT_PERM_NONE,
        NULL, NULL, NULL
    ),
    BT_GATT_CCC(
        NULL,
        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE
    ),
    BT_GATT_CHARACTERISTIC(
        &CUSTOM_PRESSURE_UUID,
        BT_GATT_CHRC_NOTIFY,
        BT_GATT_PERM_NONE,
        NULL, NULL, NULL
    ),
    BT_GATT_CCC(
        NULL,
        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE
    )
);
 
// BLE Service defined
BT_GATT_SERVICE_DEFINE(
    my_ess_service,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_ESS),  // [0]
    BT_GATT_CHARACTERISTIC( 
        BT_UUID_TEMPERATURE,  // [1]
        BT_GATT_CHRC_NOTIFY,
        BT_GATT_PERM_NONE,
        NULL, NULL, NULL     // [2]
    ),    
    BT_GATT_CCC(    // [3]
        NULL,
        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE
    ),
    BT_GATT_CHARACTERISTIC(
        BT_UUID_PRESSURE,  // [1]
        BT_GATT_CHRC_NOTIFY,
        BT_GATT_PERM_NONE,
        NULL, NULL, NULL     // [2]
    ), 
    BT_GATT_CCC(    // [3]
        NULL,
        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE
    )
); */

// notifying the client
void sensor_read_and_notify() {
	SensorLPS22HHReading tempLPS22HH;
	k_msgq_get(&my_LPS22HHmsgq, &tempLPS22HH, K_FOREVER);
	SensorSTTS751Reading tempSTTS751;
	k_msgq_get(&my_STTS751msgq, &tempSTTS751, K_FOREVER);
    LOG_DBG("Current temperature is %.3f C", tempSTTS751.temperature);
    LOG_DBG("Current pressure is %.3f hPa\n", tempLPS22HH.pressure);

    int publishTemp = (int)(tempSTTS751.temperature * 100);
    int publishPres = (int)(tempLPS22HH.pressure * 1000);
    int publishSensor = (int)(1000);
    
    bt_gatt_notify(  // actual call to notify and change the [2] value
        NULL,
        &my_custom_service.attrs[2],
        &publishTemp,
        sizeof(publishTemp)
    );
    bt_gatt_notify(  // actual call to notify and change the [4] value
        NULL,
        &my_custom_service.attrs[4],
        &publishPres,
        sizeof(publishPres)
    );

    bt_gatt_notify(  // actual call to notify and change the [4] value
        NULL,
        &my_custom_service.attrs[6],
        &publishSensor,
        sizeof(publishSensor)
    );
    
}

void thread_ble(void) {
    int err;
    
    err = bt_enable(NULL);
    if (err) {
        LOG_ERR("Bluetooth init failed (err %d)\n", err);
        return;
    }

    bt_conn_cb_register(&connection_callbacks);
    LOG_INF("Bluetooth initialized\n");

    err = bt_le_adv_start(
        &adv_param, 
        adv_packet_array, ARRAY_SIZE(adv_packet_array), 
        scan_packet_array, ARRAY_SIZE(scan_packet_array));

    if (err) {
        LOG_ERR("Advertising failed to start (err %d)\n", err);
        return;
    }

    LOG_INF("Advertising successfully started\n");

    while (true) {
        sensor_read_and_notify();
        k_msleep(1 * MSEC_PER_SEC);
    }
}


/*
 *
 Pressure thread
 *
*/
const uint8_t LPS22HH_PRES_XL_REG = 0x28;
const uint8_t LPS22HH_PRES_L_REG = 0x29;
const uint8_t LPS22HH_PRES_H_REG = 0x2A;
const uint8_t LPS22HH_CTRL_REG = 0x10;

float get_pressure_lps22hh(uint8_t  byte_XL, uint8_t  byte_L, uint8_t  byte_H){
    int pres_read_temp = (int)((byte_H<<16) | (byte_L<<8) | byte_XL);
    float pres_read = pres_read_temp/4096;
    return pres_read;
}

void thread_pres(void)
{
    uint8_t  byte_XL;
    uint8_t  byte_L;
    uint8_t  byte_H;
    int err;
    
    const struct i2c_dt_spec dt_spec_lps22hh = I2C_DT_SPEC_GET(DT_NODELABEL(my_lps22hh));
    uint8_t config[2] = {LPS22HH_CTRL_REG,0x20}; // setting update rate to 10 Hz
    
    k_mutex_lock(&i2c_mutex, K_FOREVER);
    if (i2c_is_ready_dt(&dt_spec_lps22hh) != true) {
        LOG_ERR("I2C0 bus not ready for some reason!");
        return;
    }
    err = i2c_write_dt(&dt_spec_lps22hh, config, sizeof(config));
	if(err != 0){
		printk("Failed to write to I2C device address %x at Reg. %x \n", dt_spec_lps22hh.addr,config[0]);
		return;
	}
    k_mutex_unlock(&i2c_mutex);        
	
    while (true) {
        k_mutex_lock(&i2c_mutex, K_FOREVER);
        err = i2c_write_read_dt(&dt_spec_lps22hh, &LPS22HH_PRES_H_REG,1,&byte_H,1); //MSB read
        if(err != 0){
            LOG_ERR("Failed to write/read I2C device address %d at Reg. %x \r\n", dt_spec_lps22hh.addr,LPS22HH_PRES_H_REG);
        }
        err = i2c_write_read_dt(&dt_spec_lps22hh, &LPS22HH_PRES_L_REG,1,&byte_L,1); //Middle byte read
        if(err != 0){
            LOG_ERR("Failed to write/read I2C device address %d at Reg. %x \r\n", dt_spec_lps22hh.addr,LPS22HH_PRES_L_REG);
        }
        err = i2c_write_read_dt(&dt_spec_lps22hh, &LPS22HH_PRES_XL_REG,1,&byte_XL,1); //LSB read
        if(err != 0){
            LOG_ERR("Failed to write/read I2C device address %d at Reg. %x \r\n", dt_spec_lps22hh.addr,LPS22HH_PRES_XL_REG);
        }
        k_mutex_unlock(&i2c_mutex);
        
        float pressure = get_pressure_lps22hh(byte_XL,byte_L, byte_H); // convert reading to pressure
        
        while (k_msgq_put(&my_LPS22HHmsgq, &pressure, K_NO_WAIT) != 0) { // messege queue the pressure
            k_msgq_purge(&my_LPS22HHmsgq);
        }
        k_msleep(1 * MSEC_PER_SEC);
    }
}


/*
 *
 Temperature thread
 *
*/
const uint8_t STTS751_TEMP_HIGH_REG = 0x00;
const uint8_t STTS751_TEMP_LOW_REG = 0x02;

float get_temperature_stts751(uint8_t  byte_high, uint8_t  byte_low){
    float output_val = (float)byte_high;
    output_val += ((byte_low & 0x80)!=0) * 0.5;
    output_val += ((byte_low & 0x40)!=0) * 0.25;
    output_val += ((byte_low & 0x20)!=0) * 0.125;
    output_val += ((byte_low & 0x10)!=0) * 0.0625;
    return output_val;
}

void thread_temp(void)
{
    uint8_t  byte_high;
    uint8_t  byte_low;
    int err;

    const struct i2c_dt_spec dt_spec_stts751 = I2C_DT_SPEC_GET(DT_NODELABEL(my_stts751));
    k_mutex_lock(&i2c_mutex, K_FOREVER);
    if (i2c_is_ready_dt(&dt_spec_stts751) != true) {
        LOG_ERR("I2C0 bus not ready for some reason!");
        return;
    }
    k_mutex_unlock(&i2c_mutex);
    
    while (true) {        
        k_mutex_lock(&i2c_mutex, K_FOREVER);
        err = i2c_write_read_dt(&dt_spec_stts751, &STTS751_TEMP_HIGH_REG,1,&byte_high,1); // High reg read
        if(err != 0){
            LOG_ERR("Failed to write/read I2C device address %d at Reg. %x \r\n", dt_spec_stts751.addr,STTS751_TEMP_HIGH_REG);
        }
        err = i2c_write_read_dt(&dt_spec_stts751, &STTS751_TEMP_LOW_REG,1,&byte_low,1); // Low reg read
        if(err != 0){
            LOG_ERR("Failed to write/read I2C device address %d at Reg. %x \r\n", dt_spec_stts751.addr,STTS751_TEMP_LOW_REG);
        }
        k_mutex_unlock(&i2c_mutex);
        
        float temperature = get_temperature_stts751(byte_high,byte_low); // convert reading to temperature
        
        while (k_msgq_put(&my_STTS751msgq, &temperature, K_NO_WAIT) != 0) { // messege queue the temperature
            /* message queue is full: purge old data & try again */
            k_msgq_purge(&my_STTS751msgq);
        }
        
        k_msleep(1 * MSEC_PER_SEC);

    }
}

/*
 *
 Set above threads
 *
*/
K_THREAD_DEFINE(thread_ble_id, STACKSIZE, thread_ble, NULL, NULL, NULL, THREAD_BLE_PRIORITY, 0, 0);
K_THREAD_DEFINE(thread_pres_id, STACKSIZE, thread_pres, NULL, NULL, NULL, THREAD_PRES_PRIORITY, 0, 0);
K_THREAD_DEFINE(thread_temp_id, STACKSIZE, thread_temp, NULL, NULL, NULL, THREAD_TEMP_PRIORITY, 0, 0);

/*
 *
 Main thread
 *
*/
int main(void)
{
	while(1){
		int uptime = (int)(k_uptime_get()/1000);
		LOG_INF("Time elapsed is %d s",uptime);		
		k_sleep(K_MSEC(2000));
	}
}
