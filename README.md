# ariston-nimbus-ebusd
Configuration and implementation details for an Ariston Nimbus Pocket M NET R32 with ebusd and Home Assistant

This repository builds on the definitions and documentation in the following repository and would not have been
possible without this:
    https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet

Configuration definitions are split into multiple files and ebusd circuit definitions to provide a more structured
Home Assistant configuration with simplified naming. This also enables the mqtt-hassio.cfg file to be used to
exclude entire circuits if they are not relevant.

The ebsud message definitions are overconfigured compared to what is used in Home Assistant and ignored and
unknown circuit definitions are used to filter out messages in the mqtt config and messages to Home Assistant.

Templates are used extensively for the message definitions to provide common definitions for repeated types
and to enable chained template definitions to be used for messages with multiple variables.

A perform-reads python script is provided to enable forced reads of the entire configuration or individual
circuits.
