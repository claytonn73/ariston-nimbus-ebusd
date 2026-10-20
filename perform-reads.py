#!/usr/bin/env python3
"""Trigger pull requests from ebusd."""

import argparse
import subprocess
import sys
import time

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
    find_prefix = [
        "/bin/ebusctl",
        "find",
        "-V",
        "-r",
    ]

    command_responses = []

    resp = subprocess.check_output([*find_prefix], encoding="utf8")
    command_responses = resp.split("\n")

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

if __name__ == "__main__":
    main()
