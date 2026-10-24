# ariston-nimbus-ebusd
Configuration and implementation details for an Ariston Nimbus Pocket M NET R32 with ebusd and Home Assistant

This repository builds on the definitions and documentation in the following repository and would not have been possible without this:
    https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet

Configuration definitions are split into multiple files and ebusd circuit definitions to provide a more structured Home Assistant configuration with simplified naming. This also enables the mqtt-hassio.cfg file to be used to exclude entire circuits if they are not relevant.

The ebsud message definitions are overconfigured compared to what is used in Home Assistant and ignored and unknown circuit definitions are used to filter out messages in the mqtt config and messages to Home Assistant.

Templates are used extensively for the message definitions to provide common definitions for repeated types and to enable chained template definitions to be used for messages with multiple variables.

Write definitions are available for many messages but in order to avoid providing too much opportunity for mistakes in home assistant the write messages are moved to the "ignored" circuit definition which means the home assistant entity is read only. If it is desired to re-enable the write capability then simply changing the circuit will enable Home Assistant to be used for updates.

A perform-reads python script is provided to enable forced reads of the entire configuration or individual circuits.

## Hardware and software configuration

I am using the ESERA EBC 100 eBus coupler USB ( https://esera.de/Produkte/12001/EBC-100-eBus-Koppler-USB ) attached to a Raspberry Pi Zero 2. This system is only running ebusd and is then communicating over Ethernet to a Raspberry Pi 5 running MQTT and Home Assistant.

The ebusd options used are as follows

EBUSD_OPTS="--configpath <<ebusd directory>> -d /dev/serial/by-id/usb-ESERA_GmbH_eBus_Coupler_12001_AL9ELVUS-if00-port0 --enablehex --port 8888 --mqtthost 192.168.1.100 --mqttport 1883 --mqttjson --mqttint <<ebusd directory>>/mqtt-hassio.cfg --loglevel=error"

MQTT is installed on the Raspberry Pi 5 as a docker container using docker-compose

The Home Assistant MQTT integration is installed with discovery enabled

## Query Commands and Modes

There are two main query commands issued by the system. The 2000 query response has a format where the first byte is ignored and then the response to the query is provided. The 2001 query does not have an ignored byte but it provides the value and then a minimum and maximum range for the value. Sometimes this is a specific system limit and other times it is simply the maximum range of allowed by the numeric type. Examples of the 2000 and 2001 direct queries are shown below

    31 18 2000 02 7226 / 03 01 38ff
    31 18 2001 02 7226 / 06 38ff 38ff 5e01 

Note : See the extra initial 1 byte value for the direct query which should be set to ignored in the parsing definition

There are two different query modes used by the system. There seems to be no explanation of why a particular query uses one more or the other. The first is a direct query issued as above to a slave entity on the bus that will respond directly to the query. The second is a broadcast query where a broadcast read is issued and the component will indirectly reply with a broadcast message. A 2000 broadcast query is responded with a 200f response and a 2001 query is responded with a 200e response as per the example below.

    31 fe 2000 02 6126
    13 fe 200f 05 6126 5802 00 
    7f fe 2001 02 6126 
    13 fe 200e 08 6126 5802 5e01 8a02 

It is also possible to issue multiple queries in a single command using the 2000 query only. This is presumably more efficient and also is useful if wanting to obtain multiple variables at the same time to use in a calculation (for example CoP or flow/return delta). Experimentation seems to suggest that the maximum number of variables that can be queried is 8 as larger queries do not get a response from the system. This can be done both using the direct query and broadcast query as per the example below:

    31 1e 2000 08 7610 7710 6e13 7c4f / 09 0f 3201 2a01 7e00 1800

Note : See the extra initial 1 byte value for the direct query which changes with the length of the response but again should be set to ignored in the parsing definition
   
    7f fe 2000 06 6a96 6b96 6d96
    13 fe 200f 0f 6a96 a000 00 6b96 8c00 00 6c96 be00 00

Note : See the queried variable and additional 00 value in the 200f response after the data for each queried value which should both be set to ignored in the parsing definition.

Caution is needed when using the broadcast query as the definition of the command responses only uses the first two bytes of the command response to determine the mapping of the response. Hence two queries with the same first two bytes will be parsed using the same single definition resulting in erroneous parsing of the response. 

## ebusd template usage

A standard template style can be used for the 2000 and 2001 query responses both for direct and indirect modes as shown in the example below. The template here uses the 2001 response only for the minimum and maximum values to avoid replicating the information in the 2000 response

    ignore_1,IGN:1,,,,
    ignore_2,IGN:2,,,,
    temperature,S2L,10,°C,temperature
    temperature_min_max,ignore_2;temperature:minimum;temperature:maximum,,,
    
    r,dhw,pv_delta_temperature,Delta temperature for PV Integration,,18,2000,762d,,,ignore_1;temperature:setting
    r,dhw,pv_delta_temperature_limits,Delta temperature for PV Integration,,18,2001,762d,,,temperature_min_max
    
    r,dhw,thermal_cleanse_temp,Thermal Cleanse Temperature,,fe,2000,7d26
    b,dhw,thermal_cleanse_temp,Thermal Cleanse Temperature,13,fe,200f,7d26,,,temperature:setting
    r,dhw,thermal_cleanse_temp_limits,Thermal Cleanse Temperature,,fe,2001,7d26
    b,dhw,thermal_cleanse_temp_limits,Thermal Cleanse Temperature,13,fe,200e,7d26,,,temperature_min_max

This results in the following messages being produced in MQTT

    dhw pv_delta_temperature = setting=10.0
    dhw pv_delta_temperature_limits = minimum=0.0;maximum=20.0
    dhw thermal_cleanse_temp = setting=60.0
    dhw thermal_cleanse_temp_limits = minimum=60.0;maximum=70.0

## Write Commands and Modes

There are two different write modes used by the system. The first is a direct write to a particular slave entity to update the entity. The second is a broadcast write that is picked up by the relevant entity.

When a direct write is issued with a 2020 command that changes a value there is then a subsequent echoed 2010 response that can be interpreted as a passive read of the master to update the value 

    31 18 2020 03 1823 01 / 00 
    13 18 2010 03 1823 01 / 00 

when a broadcast write is issued using a 2020 command that changes a value then there is also a subsequent echoed 2010 broadcast. This cannot be associated with the same name as the write as the name would conflict with the broadcast read entity. 

    31 fe 2020 03 0120 00 
    13 fe 2010 04 0120 00 00 

Similar to reads it is possible to have multiple updates in a single command. This is used heavily by the system for both 2020 and 2010 commands.

    13 fe 2020 0c 7072 b400 7172 e600 7272 e600

Note : See the queried variable in the 2020 command after the data for each queried value which should be set to ignored in the parsing definition.    

    7f fe 2010 09 7617 4e00 00 c19a 01 00

Note : See the queried variable and additional 00 value in the 2010 command after the data for each queried value which should both be set to ignored in the parsing definition.    

Caution is also needed when parsing 2010 and 2020 commands with multiple updates as the definition of the command responses only uses the first two bytes of the command response to determine the mapping of the response. As the system issues many chained update commands with variations after the first value parsing more than the first response is dangerous unless it is known that the combination is unique. However it is possible to only define the first parameter in the csv file and the later entries will be ignored if a longer command is issued by the system.

## Combined definition for reads and writes

For an entity that uses the direct read method the following provides a complete definition for the messages seen on the bus. Not all entities provide the broadcast 2010 response to a change.

    r,energymgr,hv_input_2,HV Input 2,,18,2001,cb2a,,,hv_input_2
    w,energymgr,hv_input_2,HV Input 2,,18,2020,cb2a,,,hv_input_2
    b,energymgr,hv_input_2,HV Input 2,13,18,2010,cb2a,,m,hv_input_2

For an entity that uses the broadcast read method the following provides a complete definition for the messages seen on the bus. The 2010 entry can be ignored by home assistant as it cannot be grouped with the same entity

    r,heating,status,Heating Status,,fe,2001,0120
    b,heating,status,Heating Status,13,fe,200e,0120,,,onoff
    w,heating,status,Heating Status,70,fe,2020,0120,,,onoff
    b,ignored,status_bcast,Heating Status,13,fe,2010,0120,,,onoff

For an entity where we also woould like to obtain the minimum and maximum values that are allowed by the system the base entity should use a 2000 read and 200f read response with the 2001/200e pair used for the _limits entity. The 2010 entry can also be defined but again ignored by Home Assistant.

    r,energymgr,ext_temp_correct,External Temperature Correction,,fe,2000,7426
    b,energymgr,ext_temp_correct,External Temperature Correction,13,fe,200f,7426,,,temperature:setting
    w,energymgr,ext_temp_correct,External Temperature Correction,70,fe,2020,7426,,,temperature:setting
    r,energymgr,ext_temp_correct_limits,External Temperature Correction,,fe,2001,7426
    b,energymgr,ext_temp_correct_limits,External Temperature Correction,13,fe,200e,7426,,,temperature_min_max
    b,ignored,ext_temp_correct_bcast,External Temperature Correction,13,fe,2010,7426,,,temperature:setting

## Performing regular queries

There are a number of entities for which it would be highly desirable to get regular updates but which are not present on the bus with the normal operation of the system. Given the use by the system of multiple entity queries it seems obvious to follow a similar pattern to efficiently obtain multiple responses with a single command. An example of this is show below for the flow and return temperatures and flow rate of the heatpump.

    r1,heatpump,water_flow,Regular read of flow rate and temps,,1e,2000,761077106e13,,,ignore_1;temperature:flow_temperature;temperature:return_temperature;flow_rate:flow_rate

## MQTT integration with Home Assistant

Given the use of the historical CSV files for the Ariston ebusd configuration there are some changes to the default mqtt-hassio.cfg configuration provided in the ebusd github.

### filter-non-circuit

The first change is something that was very helpful when creating the configuration to allow for a large amount of messages to be defined but not to pass them through to Home Assistant. The ignored and unkown circuit definitions can be used to define messages in ebusd but avoid these being sent through to home assistant.  In the example below also circuits that are not relevant to the configuration can be excluded while still leaving the messages in ebusd.

filter-non-circuit = scan|ignored|unknown|cooling|boiler|buffer|zone2|zone3|zone4|zone5|zone6

### steps, min and max with csv file

When number entities are created it can also be necessary to modify the default minimum and maximum and step values for the entry. A key example of this is temperature entities which can be negative as well as positive and for which a steps value of 0.5 might make more sense. It is possible to override these in the configuration.yaml but having a better default can help.

In order to do this the following changes were made to the mqtt-hassio.cfg file. The example below will set a steps value of 0.5 and a -100 to 100 minimum and maximum for the temperature number entities in Home Assistant.

    '# Added step_value, min_value, and max_value for number entities to be passed to HA
    type_switch-names = type_topic,type_class,type_state,type_sub,step_value,min_value,max_value

    '# Also add the relevant step,minimum,maximum values to these definitions
    type_switch-w-number =
        number,temperature,,,0.5,-100,100 = temp|,°C$

    '# HA integration: optional variable with the minimum numeric value using min_value from above
    min_number ?= ,
    "min":%min_value

    '# HA integration: optional variable with the maximum numeric value using max_value from above
    max_number ?= ,
    "max":%max_value

    HA integration: optional variable with the numeric step value using step_value from above
    step_number ?= ,
    "step":%step_value

    '# Add the min_number, max_number and step_number entries to the command topic definition
    type_part-number = ,
    "command_topic":"%topic/set"%min_number%max_number%step_number%unit_of_measurement%state_class%type_class_number

## Home Assistant Integration

The definitions above result in entity IDs in Home Assistant like the example below for the Thermal Cleanse Temperature messages.

    number.heating_ebusd_dhw_thermal_cleanse_temp
    sensor.heating_ebusd_dhw_thermal_cleanse_temp_limits_maximum
    sensor.heating_ebusd_dhw_thermal_cleanse_temp_limits_minimum

These values can be used to create a protected slider and display in Home Assistant using the system generated value for the minimum and maximum

<img width="388" height="217" alt="image" src="https://github.com/user-attachments/assets/61b9d525-110d-49be-8dd7-57e2fdee2d01" />

This particular example uses the config-template-card and big-slider-card but there are other options available
    
    type: custom:config-template-card
    variables:
      MinVal: states['sensor.heating_ebusd_dhw_thermal_cleanse_temp_limits_minimum'].state
      MaxVal: states['sensor.heating_ebusd_dhw_thermal_cleanse_temp_limits_maximum'].state
    entities:
      - number.heating_ebusd_dhw_thermal_cleanse_temp
      - sensor.heating_ebusd_dhw_thermal_cleanse_temp_limits_minimum
      - sensor.heating_ebusd_dhw_thermal_cleanse_temp_limits_maximum
    card:
      type: custom:big-slider-card
      entity: number.heating_ebusd_dhw_thermal_cleanse_temp
      show_percentage: true
      name: DHW Thermal Cleanse Temperature
      attribute: temperature
      color: green
      min: ${parseFloat(MinVal)}
      max: ${parseFloat(MaxVal)}

### Home Assistant Template Entities

There are a few template entities that it is interesting to create based on the raw data from ebusd. These include:

    Heatpump Flow Return Temperature Delta
    Heatpump CoP
    Heatpump Energy Produced
    
These rely on multiple data values from ebusd and it is helpful for these to be included in the same query from the system so that the values are all from the same point in time. However even if a single query is used the values will not all arrive at precisely the same time. The following trigger template seems to work to avoid calculations being performed on data from different points of time.

    - triggers:
      - trigger: state
        entity_id:
          - sensor.heating_ebusd_heatpump_water_flow_flow_temperature
          - sensor.heating_ebusd_heatpump_water_flow_return_temperature
        not_to:
          - unknown
          - unavailable
        for: "00:00:03" # 3-second evaluation delay after any state change
      sensor:
        - name: "Heatpump flow return delta"
          unique_id: heatpump_flow_return_delta
          unit_of_measurement: "°C"
          state: >
            {% set flow = states('sensor.heating_ebusd_heatpump_water_flow_flow_temperature') | float %}
            {% set return = states('sensor.heating_ebusd_heatpump_water_flow_return_temperature') | float %}
            {% set correction = 0.4 | float %}
            {{ (flow - return - correction)|round(1) }}

### Home Assistant Dashboards

As there are limited parameters available in the website/app and it is inconvenient to have to use the Sensys HD interface I have created a number of Home Assistant panels for display and potential modification of the relevant parameters on the system. Once things are setup these are unlikely to change unless something changes in the configuration but I have found them useful so far.

The DHW dashboard with system state and history is shown below

<img width="1737" height="711" alt="image" src="https://github.com/user-attachments/assets/27181a92-36d8-4a17-8e86-b65c7445a587" />

The DHW dashboard with the parameter settings is shown below

<img width="1742" height="1087" alt="image" src="https://github.com/user-attachments/assets/bce5150f-7a1f-475b-a29c-b977f073be59" />

The heating dashboard with system state and history is shown below

<img width="1725" height="1130" alt="image" src="https://github.com/user-attachments/assets/ae582efe-14c0-4d82-a9fe-0721238b5509" />

The heating dashboard with the parameter settings is shown below

<img width="1732" height="976" alt="image" src="https://github.com/user-attachments/assets/e7db6bc9-3665-4ef2-b422-9d20858d35d1" />

<img width="512" height="425" alt="image" src="https://github.com/user-attachments/assets/0e7c573f-ce3d-4d5f-909b-cd19d7cff796" />

## System behaviour notes

### Heatpump Status and Behaviour

This section contains some notes of the system heating behaviour over time and the information shown in the heatpump status 

When external temperatures are high enough that the heatpump is active but not running continually then the following behaviour is seen on the system

<img width="581" height="587" alt="image" src="https://github.com/user-attachments/assets/4d41ca18-ed68-4cd5-812a-c4aa39d09890" />

A period of heating of 10 minutes or more is followed by a 3 minute period in "timeguard" state where the heatpump is not running but water is circulating. The heatpump then may go into "standby" mode for a period of time while water continues to circulate before restarting the heating cycle. At higher temperatures the standby period becomes longer reducing the cycles per hour but worst case there are approximately 4 cycles per hour.

### Automatic Winter Mode

The automatic winter mode is a useful feature to enable and disable heating based on an external temperature threshold. However it does not use the defined threshold directly to perform the enable/disable of heating. If temperature drops 1C below the defined threshold the heating will be enabled and if the temperature rises 1C above the defined threshold the heating will be disabled. In this way it avoids repetitive enabling and disabling of heating but it does mean that setting the value correctly for the house is important. It is definitely possible to use 0.5C steps for this value. On my system I have set the associated winter mode delay to 0 minutes as with the behaviour above it does not seem sensible to wait for an extended period once the higher or lower threshold is reached. The settings used are as follows

        ebusd zone1 winter_mode - on
        ebusd zone1 winter_mode_temp - 15.5
        ebusd zone1 winter_mode_delay - 0
        
### Thermal Cleanse 

It is not possible on my system to use the thermal cleanse functionality of the system as the heatpump plus immersion are not able to reach the minimum thermal cleanse temperature and maintain it for the required time period. However as I am on a time of use tariff with very cheap overnight electricity it makes sense to simply set the comfort temperature to 60C and to use the timed DHW schedule to boost the temperature to 60C every night. 

My settings for DHW are set to 

    ebusd dhw scheduling - time_based
    ebusd dhw comfort_temp - 60
    ebusd dhw reduced_temp - 45

The DHW schedule is set with comfort temperature in a 1 hour period between 2am and 3am which is the middle of the cheap tariff period and gives sufficient time for the heating cycle to complete.

<img width="1387" height="546" alt="image" src="https://github.com/user-attachments/assets/7e01ac93-241d-4859-8506-2c78336a9f82" />

### Eddi integration for the immersion

As I have a myenergi system for car charging and now also the immersion it makes sense to integrate this with the heatpump. I have done this in two ways, firstly so that the heatpump can trigger the Eddi to reach a 60C temperature to prevent Legionella and secondly to enable the Eddi to be able to trigger additional DHW heating rather than exporting solar energy. This second function is not currently active in my system as the export prices are good but if they drop then it will enable the energy to be used.

The functionality for the heatpump to activate the Eddi is setup using the "Aux 1 Output" connection and the following settings on the heatpump
    
    ebusd dhw aux_heat_activation - heat_integration_and_backup
    ebusd energymgr aux_output_1 - dhw_request
    ebusd dhw delay_time - 1200 
    ebusd dhw release_integral - 15

This will trigger the DHW heating_boost status after approximately 20 minutes of water heating and will activate the Eddi until the DHW heating cycle has finished.

The functionality for the Eddi to activate the heatpump is setup using the "Aux 1 Input" connection and the following settings on the heatpump

    ebusd energymgr aux_input_1 - photovoltaic_integration
    ebusd dhw pv_delta_temperature - 10

This will increase the target DHW temperature by 10C when the Eddi determines that enough solar energy is being exported for this to be worthwhile.

### Power Consumption and Energy Produced

The heatpump produced an incrementing value for the heatpump power consumption associated with DHW and heating and the associated estimated energy produced for these. This can be used in Home Assistant as a Utility Meter input to provide hourly and daily statistics. It can also be used to create a heating and DHW CoP statistics based on these although on my system these seem to be somewhat optimistic.
    
## Disclaimer
All information posted is merely for educational and informational purposes. It is not intended as a substitute for professional advice. Should you decide to act upon any information on this website, you do so at your own risk. While the information on this website has been verified to the best of our abilities, I cannot guarantee that there are no mistakes or errors. You may use this library with the understanding that doing so is AT YOUR OWN RISK. No warranty, express or implied, is made with regards to the fitness or safety of this code for any purpose. If you use this library to query or change settings of your products you understand that it is possible to cause damages.
