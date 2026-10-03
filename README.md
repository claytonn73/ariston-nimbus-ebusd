# ariston-nimbus-ebusd
Configuration and implementation details for an Ariston Nimbus Pocket M NET R32 with ebusd and Home Assistant

This repository builds on the definitions and documentation in the following repository and would not have been possible without this:
    https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet

Configuration definitions are split into multiple files and ebusd circuit definitions to provide a more structured Home Assistant configuration with simplified naming. This also enables the mqtt-hassio.cfg file to be used to exclude entire circuits if they are not relevant.

The ebsud message definitions are overconfigured compared to what is used in Home Assistant and ignored and unknown circuit definitions are used to filter out messages in the mqtt config and messages to Home Assistant.

Templates are used extensively for the message definitions to provide common definitions for repeated types and to enable chained template definitions to be used for messages with multiple variables.

A perform-reads python script is provided to enable forced reads of the entire configuration or individual circuits.

# Query Commands and Modes 

There are two main query commands issued by the system. The 2000 query response has a format where the first byte is ignored and then the response to the query is provided. The 2001 query does not have an ignored byte but it provides the value and then a minimum and maximum range for the value. Sometimes this is a specific system limit and other times it is simply the maximum range of allowed by the numeric type. Examples of the 2000 and 2001 direct queries are shown below

    31 18 2000 02 7226 / 03 01 38ff
    31 18 2001 02 7226 / 06 38ff 38ff 5e01 

There are two different query modes used by the system. There seems to be no explanation of why a particular query uses one more or the other. The first is a direct query issued to a slave entity on the bus that will respond directly to the query. The second is a broadcast query where a broadcast read is issued and the component will indirectly reply with a broadcast message. A 2000 broadcast query is responded with a 200f response and a 2001 query is responded with a 200e response as per the example below.

    31 fe 2000 02 6126
    13 fe 200f 05 6126 5802 00 
    7f fe 2001 02 6126 
    13 fe 200e 08 6126 5802 5e01 8a02 

A standard template style can be used for the 2000 and 2001 query responses both for direct and indirect modes as shown in the example below

    ignore_1,IGN:1,,,,
    temperature,S2L,10,°C,temperature
    temperature_min_max,temperature:setting;temperature:minimum;temperature:maximum,,,
    
    r,dhw,pv_delta_temperature,Delta temperature for PV Integration,,18,2000,762d,,,ignore_1;temperature:setting
    r,dhw,pv_delta_temperature_limits,Delta temperature for PV Integration,,18,2001,762d,,,temperature_min_max
    
    r,dhw,thermal_cleanse_temp,Thermal Cleanse Temperature,,fe,2000,7d26
    b,dhw,thermal_cleanse_temp,Thermal Cleanse Temperature,13,fe,200f,7d26,,,temperature:setting
    r,dhw,thermal_cleanse_temp_limits,Thermal Cleanse Temperature,,fe,2001,7d26
    b,dhw,thermal_cleanse_temp_limits,Thermal Cleanse Temperature,13,fe,200e,7d26,,,temperature_min_max

# Disclaimer
All information posted is merely for educational and informational purposes. It is not intended as a substitute for professional advice. Should you decide to act upon any information on this website, you do so at your own risk. While the information on this website has been verified to the best of our abilities, I cannot guarantee that there are no mistakes or errors. You may use this library with the understanding that doing so is AT YOUR OWN RISK. No warranty, express or implied, is made with regards to the fitness or safety of this code for any purpose. If you use this library to query or change settings of your products you understand that it is possible to cause damages I reserve the right to change this policy at any given time.
