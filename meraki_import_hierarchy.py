"""
# BSD 3-Clause License

Copyright (c) 2026, Cisco Systems, Inc. and/or its affiliates

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

__author__ = "Aron Donaldson <ardonald@cisco.com>"
__contributor__ = ""
__copyright__ = "Copyright (c) 2026 Cisco and/or its affiliates."
__license__ = "BSD 3-Clause License (https://opensource.org/license/bsd-3-clause)"

import base64
import os
import sys
import csv
from io import BytesIO
from glob import glob
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from getpass import getpass
from argparse import ArgumentParser
import logging

from PIL import Image
import requests
import meraki

# Disable certificate warnings
urllib3.disable_warnings(InsecureRequestWarning)

def config_logging(args):
    """
    Configures logging handler for the script.
    NOTSET: 0
    DEBUG: 10
    INFO: 20
    WARNING: 30
    ERROR: 40
    CRITICAL: 50

    The output format is configured as such:

    Date    Timezone+-  Time + 3   Log   Script   Func.     Code    Log message
            GMT offset  Millisec.  Lvl   name     name    line num     text
    ---------- -------- ------------- ---- --------------------------  -----------
    YYYY-MM-DD CDT-0500 HH:MM:SS.msec INFO (module, function, lineNo): Log Message

    param args: Argparse namespace object with "debug" variable.

    Example output: 2025-06-25 CDT-0500 16:12:52.154 INFO (myscript, myfunction, 123): testing
    Format: YYYY-MM-DD [timezone][+,-][GMT offset] HH:mm:ss.msec [logging level] (module, function, lineNo): [message]
    """
    logger = logging.getLogger(__name__)
    if args.debug:
        logger.setLevel(10)
    else:
        logger.setLevel(20)
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s (%(module)s, %(funcName)s, %(lineno)d): %(message)s', datefmt='%Y-%m-%d %Z%z %H:%M:%S')
    return logger


def export_ids(api):
    columns = [
        "org_name",
        "org_id",
        "network_name",
        "network_id"
    ]
    rows = []
    response = api.organizations.getOrganizations()
    for item in response:
        if item.get("id"):
            networks = api.organizations.getOrganizationNetworks(item["id"], total_pages="all")
            for network in networks:
                try:
                    row = {
                        "org_name": item["name"],
                        "org_id": item["id"],
                        "network_name": network["name"],
                        "network_id": network["id"]
                    }
                    rows.append(row)
                except Exception as e:
                    logger.error(f"Failed to build row for:\n{item}\n{network}")
        else:
            logger.error(f"Failed to get Org details for:\n{item}")
    with open("org_and_network_ids.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        f.close()
    logger.info("Exported Org and Network IDs to 'org_and_network_ids.csv'.")


def read_csv(args):
    try:
        with open(args.input_file, "r") as f:
            reader = csv.DictReader(f)
            input_data = []
            for row in reader:
                input_data.append(row)
            f.close()
        logger.debug(f"Input data: {input_data}")
        return input_data
    except Exception as e:
        logger.critical(f"Error encountered parsing input file into JSON: {e}")
        return None


def generate_input_file():
    columns = [
        "type",
        "name",
        "address",
        "country",
        "floorNumber",
        "org_id",
        "network_id",
        "assigned_building_name",
        "top_left_lat",
        "top_left_long",
        "bottom_left_lat",
        "bottom_left_long",
        "image_filename",
    ]
    sample_data = [
        {
            "type": "building",
            "name": "The White House",
            "address": "1600 Pennsylvania Ave., Washington, D.C.",
            "country": "United States",
            "floorNumber": 0,
            "org_id": "",
            "network_id": "",
            "assigned_building_name": "",
            "top_left_lat": 0.0,
            "top_left_long": 0.0,
            "bottom_left_lat": 0.0,
            "bottom_left_long": 0.0,
            "image_filename": "",
        },
        {
            "type": "floor",
            "name": "Secret Bunker",
            "address": "",
            "country": "",
            "floorNumber": -1,
            "org_id": "",
            "network_id": "",
            "assigned_building_name": "The White House",
            "top_left_lat": 38.89795886581941,
            "top_left_long": -77.03686156343726,
            "bottom_left_lat": 38.897549488184765,
            "bottom_left_long": -77.03625249775843,
            "image_filename": "",
        },
    ]
    with open("meraki_input_file_example.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(sample_data)
        f.close()
    logger.info("Input file example created: meraki_input_file_example.csv")


def find_file(filename):
    return glob(f"**/{filename}", root_dir=os.getcwd(), recursive=True)


def generate_image_base64(filepath):
    if filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
        try:
            # Open the image
            with Image.open(filepath) as img:
                # Prepare the image to be encoded
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                # Encode the image to base64
                img_base64 = base64.b64encode(buffered.getvalue())
                return img_base64.decode('utf-8')
        except Exception as e:
            logger.error(f"Error: Unable to base64 encode image file {filepath}: {str(e)}")
            return None
    else:
        try:
            # Open the image
            with Image.open(filepath) as img:
                # Prepare the image to be encoded
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                # Encode the image to base64
                img_base64 = base64.b64encode(buffered.getvalue())
                return img_base64.decode('utf-8')
        except Exception as e:
            logger.error(f"Error: Unable to base64 encode image file {filepath}: {str(e)}")
            return None


def create_building(args, networkId, building):
    url = f"https://api.meraki.com/api/v1/networks/{networkId}/sites/buildings"
    headers = {
        "Authorization": f"Bearer {args.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "name": building,
        "floors": []
    }
    result = requests.post(url, headers=headers, json=payload)
    logger.debug(f"Building creation result: {result.status_code} - {result.text}")
    if result.status_code in [200, 201]:
        logger.info(f"Building {building} created successfully.")
        return result.json()["buildingId"]
    else:
        logger.error(f"Creation of building {building} may have failed: {result.status_code} - {result.text}")
        return None


def create_floor(args, networkId: str, floorDetails: dict, buildingId: str|None = ""):
    if buildingId != "" and all(k in floorDetails for k in (
        "name", 
        "floorNumber", 
        "top_left_lat",
        "top_left_long",
        "bottom_left_lat",
        "bottom_left_long")
        ):
        image_b64 = None
        if floorDetails["image_filename"] != "":
            filepath = find_file(floorDetails["image_filename"])
            if len(filepath) > 0:
                # Just going to pick the first instance of the file for simplicity
                image_b64 = generate_image_base64(filepath[0])
                
        if image_b64:
            payload = {
                "name": floorDetails["name"],
                "floorNumber": floorDetails["floorNumber"],
                "buildingId": buildingId,
                "imageContents": image_b64,
                "topLeftCorner": {
                    "lat": float(floorDetails["top_left_lat"]),
                    "lng": float(floorDetails["top_left_long"])
                },
                "bottomLeftCorner": {
                    "lat": float(floorDetails["bottom_left_lat"]),
                    "lng": float(floorDetails["bottom_left_long"])
                },
            }
        else:
            payload = {
                "name": floorDetails["name"],
                "floorNumber": floorDetails["floorNumber"],
                "buildingId": buildingId,
                "topLeftCorner": {
                    "lat": float(floorDetails["top_left_lat"]),
                    "lng": float(floorDetails["top_left_long"])
                },
                "bottomLeftCorner": {
                    "lat": float(floorDetails["bottom_left_lat"]),
                    "lng": float(floorDetails["bottom_left_long"])
                },
            }
    elif buildingId != "" and floorDetails.get("name"):
        payload = {
            "name": floorDetails["name"],
            "buildingId": buildingId,
        }
    elif floorDetails.get("name"):
        payload = {
            "name": floorDetails["name"],
        }
    else:
        logger.error(f"Could not create payload for Floor: {floorDetails}")
        return None

    url = f"https://api.meraki.com/api/v1/networks/{networkId}/floorPlans"
    headers = {
        "Authorization": f"Bearer {args.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    result = requests.post(url, headers=headers, json=payload)
    logger.debug(f"Floor creation result: {result.status_code} - {result.text}")
    if result.status_code in [200, 201]:
        logger.info(f"Floor {floorDetails["name"]} created successfully.")
        return result.json()["floorPlanId"]
    else:
        logger.error(f"Creation of floor {floorDetails["name"]} may have failed: {result.status_code} - {result.text}")
        return None


def main(args):
    global logger
    logger = config_logging(args)
    if args.api_key:
        pass
    else:
        args.api_key = getpass("Enter the API Key for authenticating to the Meraki Dashboard: ", stream=None)

    global api
    api = meraki.DashboardAPI(api_key=args.api_key, inherit_logging_config=True)

    if args.get_org_net_ids:
        export_ids(api)
        sys.exit(0)
    elif args.gen_input_file:
        generate_input_file()
        sys.exit(0)
    elif args.input_file:
        input_data = read_csv(args)
    else:
        logger.critical("You must specify an Input CSV file for this script to function.")
        sys.exit(1)

    buildings = {}
    if input_data:
        for row in input_data:
            if row.get("type") and row["type"].lower() == "building":
                if row["network_id"] != "" and row["name"] != "":
                    buildingId = create_building(args, networkId=row["network_id"], building=row["name"])
                    if buildingId:
                        buildings[row["name"]] = buildingId

        for row in input_data:
            if row.get("type") and row["type"].lower() == "floor":
                if row["network_id"] != "" and row["name"] != "":
                    building_id = buildings.get(row["assigned_building_name"])
                    floorId = create_floor(args, networkId=row["network_id"], floorDetails=row, buildingId=building_id)



if __name__ == '__main__':
    parser = ArgumentParser(description="Script for exporting floor plans and AP placement from Catalyst Center and importing into Meraki Dashboard.")
    parser.add_argument("-k", "--api_key", help="API Key for authenticating to the Meraki Dashboard", required=False)
    parser.add_argument("-i", "--input_file", help="CSV input file listing the buildings and floors you want to import.", required=False)
    parser.add_argument("--debug", help="Enable DEBUG level logging output.", default=False, action="store_true")
    parser.add_argument("--get_org_net_ids", help="Return only the Org IDs and Network IDs accessible with this API Key.", default=False, action="store_true")
    parser.add_argument("--gen_input_file", help="ONLY generate an input file template, with required columns and sample data.", default=False, action="store_true")
    args = parser.parse_args()
    main(args)
