# ariston-nimbus-ebusd
Configuration and implementation details for an Ariston Nimbus Pocket M NET R32 with ebusd and Home Assistant

This repository builds on the definitions and documentation in the following repository and would not have been possible without this:
    https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet

Configuration definitions are split into multiple files and ebusd circuit definitions to provide a more structured Home Assistant configuration with simplified naming. This also enables the mqtt-hassio.cfg file to be used to exclude entire circuits if they are not relevant.

The ebsud message definitions are overconfigured compared to what is used in Home Assistant and ignored and unknown circuit definitions are used to filter out messages in the mqtt config and messages to Home Assistant.

Templates are used extensively for the message definitions to provide common definitions for repeated types and to enable chained template definitions to be used for messages with multiple variables.

A perform-reads python script is provided to enable forced reads of the entire configuration or individual circuits.

# Disclaimer
All information posted is merely for educational and informational purposes. It is not intended as a substitute for professional advice. Should you decide to act upon any information on this website, you do so at your own risk. While the information on this website has been verified to the best of our abilities, I cannot guarantee that there are no mistakes or errors. You may use this library with the understanding that doing so is AT YOUR OWN RISK. No warranty, express or implied, is made with regards to the fitness or safety of this code for any purpose. If you use this library to query or change settings of your products you understand that it is possible to cause damages I reserve the right to change this policy at any given time.
