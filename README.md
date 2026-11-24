# Catalyst_Center_to_Meraki_Hierarchy_Migration
A collection of Python scripts that assists with migrating site hierarchy configurations from Catalyst Center into Meraki Dashboard.

## Limitations

The Cisco Catalyst Center platform and the Meraki Dashboard portal differ in how they represent site hierarchy levels and the location of Access Points in relation to floor plans.  Here is a table for comparison:

| Element | Catalyst Center | Meraki Dashboard |
|:--------|:---------------:|:----------------:|
| Areas | :white_check_mark: | :no_entry_sign: |
| Buildings | :white_check_mark: | :white_check_mark: |
| Floors | :white_check_mark: | :white_check_mark: |
| Address | Building level | Building Level |
| Lat/Long | Building level | Floor level |
| Floor Plans | :white_check_mark: | :white_check_mark: |
| Floor Plan Orientation | :no_entry_sign: | :white_check_mark: |
| Floor Plan on Map | :no_entry_sign: | :white_check_mark: |
| Device Location | X,Y Coord based on floor plan image | Lat/Long Coordinates based on map |

The primary challenge in migrating site hierarchies between Catalyst Center and Meraki Dashboard is the placement of devices on a floor plan and the orientation of the floor plan to match actual map data.  Since Catalyst Center only places devices on the floor plan according to arbitrary X,Y coordinates based on the floor plan image, there is no reliable way to convert these locations to actual Latitude and Longitude coordinates on a digital map.  Also, since Catalyst Center does not place the floor plan on an actual map, the orientation and scale of the image is not matched up with the real-world data on a map.  Catalyst Center will provide a Latitude and Longitude coordinate for a building, derived from its physical address or the values provided at creation, but these coordinates are treated as the centerpoint of the building.

For these reasons, the easiest method of migration is to follow this process:

1. Export buildings, floors and floor plan images from Catalyst Center.
2. Enhance the exported data with:
    1. Lat/Long coordinates of two adjacent corners of each floor plan image (we'll use the upper-left and lower-left corners).
    2. The filename of the exported floor plan image.
    3. The Meraki Org ID and Network ID where you wish to create the buildings and floors.
3. Create buildings in Meraki Dashboard.
4. Create floors in Meraki Dashboard while simultaneously assigning them to a building and adjusting orientation.
5. Export access points from Catalyst Center, including their floor assignment.
6. Select four access points for each floor and collect the following details:
    1. Meraki Cloud ID (serial number)
    2. Latitude and Longitude coordinates of access point
7. Import access points into Meraki Dashboard.
8. Place access points on the correct floor.
9. Initiate an AP Auto-Locate task to allow Meraki to triangulate and place the remaining APs on each floor.

## Usage

Coming soon!