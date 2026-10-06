# ariston-nimbus-ebusd
Configuration and implementation details for an Ariston Nimbus Pocket M NET R32 with ebusd and Home Assistant

This repository builds on the definitions and documentation in the following repository and would not have been possible without this:
    https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet

Configuration definitions are split into multiple files and ebusd circuit definitions to provide a more structured Home Assistant configuration with simplified naming. This also enables the mqtt-hassio.cfg file to be used to exclude entire circuits if they are not relevant.

The ebsud message definitions are overconfigured compared to what is used in Home Assistant and ignored and unknown circuit definitions are used to filter out messages in the mqtt config and messages to Home Assistant.

Templates are used extensively for the message definitions to provide common definitions for repeated types and to enable chained template definitions to be used for messages with multiple variables.

Write definitions are available for many messages but in order to avoid providing too much opportunity for mistakes in home assistant the write messages are moved to the "ignored" circuit definition which means the home assistant entity is read only. If it is desired to re-enable the write capability then simply changing the circuit will enable Home Assistant to be used for updates.

A perform-reads python script is provided to enable forced reads of the entire configuration or individual circuits.

## Query Commands and Modes

There are two main query commands issued by the system. The 2000 query response has a format where the first byte is ignored and then the response to the query is provided. The 2001 query does not have an ignored byte but it provides the value and then a minimum and maximum range for the value. Sometimes this is a specific system limit and other times it is simply the maximum range of allowed by the numeric type. Examples of the 2000 and 2001 direct queries are shown below

    31 18 2000 02 7226 / 03 01 38ff
    31 18 2001 02 7226 / 06 38ff 38ff 5e01 

There are two different query modes used by the system. There seems to be no explanation of why a particular query uses one more or the other. The first is a direct query issued to a slave entity on the bus that will respond directly to the query. The second is a broadcast query where a broadcast read is issued and the component will indirectly reply with a broadcast message. A 2000 broadcast query is responded with a 200f response and a 2001 query is responded with a 200e response as per the example below.

    31 fe 2000 02 6126
    13 fe 200f 05 6126 5802 00 
    7f fe 2001 02 6126 
    13 fe 200e 08 6126 5802 5e01 8a02 

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

This results in the following messages being produces

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

filter-non-circuit = scan|ignored|unknown|cooling|boiler|buffer|zone2|zone3

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

## System behaviour notes

The automatic winter mode is a useful feature to enable and disable heating based on an external temperature threshold. However it does not use the defined threshold directly to perform the enable/disable of heating. If temperature drops 1C below the defined threshold the heating will be enabled and if the temperature rises 1C above the defined threshold the heating will be disabled. In this way it avoids repetitive enabling and disabling of heating but it does mean that setting the value correctly for the house is important. It is definitely possible to use 0.5C steps for this value. On my system I have set the associated winter mode delay to 0 minutes as with the behaviour above it does not seem sensible to wait for an extended period once the higher or lower threshold is reached.

## Disclaimer
All information posted is merely for educational and informational purposes. It is not intended as a substitute for professional advice. Should you decide to act upon any information on this website, you do so at your own risk. While the information on this website has been verified to the best of our abilities, I cannot guarantee that there are no mistakes or errors. You may use this library with the understanding that doing so is AT YOUR OWN RISK. No warranty, express or implied, is made with regards to the fitness or safety of this code for any purpose. If you use this library to query or change settings of your products you understand that it is possible to cause damages I reserve the right to change this policy at any given time.
