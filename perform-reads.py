#!/usr/bin/env python3
"""Trigger pull requests from ebusd."""

import argparse
import pprint
import subprocess
import sys
import time
from textwrap import wrap

from utilities import get_logger

logger = get_logger(destination="sysout", level="INFO")




def get_options() -> argparse.Namespace:
    """Get the required options using argparse 
    Returns:
        dict: A dictionary of the options to be used.
    """
    parser = argparse.ArgumentParser(description='Performs reads of all defined values for a circuit or all circuts')
    parser.add_argument('-c', '--circuit', help='circuit to reads', default='all')
    return parser.parse_args()


def main() -> None:

    args = get_options()
    
    desired_circuit = args.circuit

    cmd_prefix = [
        "/bin/ebusctl",
        "read",
        "-f",
        "-c",
    ]
    hex_prefix = [
        "/bin/ebusctl",
        "hex",
        "-n",
    ]
    find_prefix = [
        "/bin/ebusctl",
        "find",
        "-V",
        "-r",
    ]
    decode_prefix = [
        "/bin/ebusctl",
        "decode",
    ]
    destination_address = "18"
    decode = "SIN,10"
    pbsb = "2000"

    test_commands = [
        {"dest": "18", "pbsb": "2000", "data_start": "7071", "digit": "2", "number": "16"},
    ]

    command_responses = []

    resp = subprocess.check_output([*find_prefix], encoding="utf8")
    command_responses = resp.split("\n")
    # pprint.pprint(command_responses)

    for response in command_responses:
        command = response.split(" = ")[0]
        if command.find("scan") > 0:
            continue
        if len(command) < 3:
            continue
        circuit, cmd = command.split(" ")
        if desired_circuit in('all',circuit):
            resp2 = subprocess.check_output([*cmd_prefix, circuit, cmd], encoding="utf8").replace("\n", "")
            print(circuit, cmd, resp2)
            time.sleep(2)
    sys.exit(0)

    for command in test_commands:
        data = command["data_start"]
        digit = int(command["digit"])

        for number in range(int(command["number"])):
            databytes = data[: digit - 1] + str(hex(int(data[digit - 1 : digit], 16) + number))[2:] + data[digit:]

            cmd = command["dest"] + command["pbsb"] + databytes

            resp = subprocess.check_output([*hex_prefix, cmd], encoding="utf8").replace("\n", "")

            if resp.startswith("ERR", "done", "00"):
                print("data", cmd, "resp", resp)
            else:
                print("data", cmd, "resp", resp)
                length = int(resp[:2], 16)
                if length == 1:
                    response = str(resp[2:])

                    print("data", cmd, "resp", resp, "length", length, "response", response)
                elif length == 2:
                    nextval = int(resp[2:4])
                    response = str(resp[4:])
                    uch = subprocess.check_output([*decode_prefix, "UCH", response], encoding="utf8").replace("\n", "")
                    bcd = subprocess.check_output([*decode_prefix, "BCD", response], encoding="utf8").replace("\n", "")
                    print(
                        "data", cmd, "resp", resp, "length", length, "next", nextval, "response", response, "uch", uch, "bcd", bcd
                    )
                    command_responses.append(
                        {
                            "dest": command["dest"],
                            "pbsb": command["pbsb"],
                            "data": databytes,
                            "length": length,
                            "next": nextval,
                            "response": response,
                        }
                    )
                elif length == 3:
                    nextval = int(resp[2:4])
                    response = str(resp[4:])
                    sin = subprocess.check_output([*decode_prefix, "SIN,10", response], encoding="utf8").replace("\n", "")
                    uin = subprocess.check_output([*decode_prefix, "UIN", response], encoding="utf8").replace("\n", "")
                    command_responses.append(
                        {
                            "dest": command["dest"],
                            "pbsb": command["pbsb"],
                            "data": databytes,
                            "length": length,
                            "next": nextval,
                            "response": response,
                        }
                    )
                    print(
                        "data", cmd, "resp", resp, "length", length, "next", nextval, "response", response, "sin", sin, "uin", uin
                    )
                else:
                    nextval = int(resp[2:4])
                    response = str(resp[4:])
                    print("data", cmd, "resp", resp, "length", length, "next", nextval, "response", response)
            time.sleep(2)

        pprint.pprint(command_responses)
        sys.exit(0)

        mylist = wrap(resp, 4)

        numchars = wrap(mylist[0], 2)[0]
        nextval = wrap(mylist[0], 2)[1]
        print("numchars", numchars)
        print("next", nextval)

        if numchars == "03":
            output = mylist[1]
            respd = subprocess.check_output([*decode_prefix, decode, output], encoding="utf8")

            respd = respd.replace("\n", "")

            print(
                "destination",
                destination_address,
                "pbsb",
                pbsb,
                "data bytes",
                databytes,
                "response",
                output,
                "as",
                decode,
                "is",
                respd,
            )

        elif numchars == "05":
            output = mylist[1]
            respd = subprocess.check_output([*decode_prefix, decode, output], encoding="utf8")

            respd = respd.replace("\n", "")

            print(
                "destination",
                destination_address,
                "pbsb",
                pbsb,
                "data bytes",
                databytes,
                "response",
                output,
                "as",
                decode,
                "is",
                respd,
            )

            output = mylist[2]
            respd = subprocess.check_output([*decode_prefix, decode, output], encoding="utf8")

            respd = respd.replace("\n", "")

            print(
                "destination",
                destination_address,
                "pbsb",
                pbsb,
                "data bytes",
                databytes,
                "response",
                output,
                "as",
                decode,
                "is",
                respd,
            )

        else:
            print("destination", destination_address, "pbsb", pbsb, "data bytes", databytes, "response", resp)

        # Sleep for 2 seconds to avoid overloading the bus
        time.sleep(2)


if __name__ == "__main__":
    main()
