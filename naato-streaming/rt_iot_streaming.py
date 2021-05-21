# coding: utf-8
# Copyright (c) 2016, 2020, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

import datetime
import json
import oci
import requests
import sys
import osmapi as osm
from base64 import b64encode, b64decode
from random import randrange, uniform
from time import sleep

# Usage : python mad_stream.py <compartment id>

STREAM_NAME = "IoT_Stream"
PARTITIONS = 1
api = osm.OsmApi()


def get_route (src_lat, src_lon, dst_lat, dst_lon):
    request_url = F"http://router.project-osrm.org/route/v1/driving/{src_lon},{src_lat};{dst_lon},{dst_lat}?alternatives=false&annotations=nodes"
    #print(request_url)
    res = requests.get(request_url)
    #Parse response json for nodeList
    #print(res)
    node_list = (res.json()['routes'][0]['legs'][0]['annotation']['nodes'])
    #Get all cordinates of nodes in route
    node_cords = api.NodesGet(node_list)
    sorted_cords = [node_cords[x] for x in node_list]
    #Calculate sleep interval between nodes
    interval = res.json()['routes'][0]['legs'][0]['duration'] * (1/len(node_list))
    return (sorted_cords, interval)

def publish_data (package_id, node_cords, interval, dst_lat, dst_lon, client, stream_id):
    print(F"Publishing to stream {stream_id}")
    #Transit time (tt), equivalent index of for loop, multiplied by interval to
    #get current transit time (in seconds).
    tt = 0
    for node in node_cords:
            tt+=1
            sleep(interval)
            status = 0 #default state, in_transit
            #Check if loop is on last node, aka destination node
            if tt == len(node_cords):
                status = 1
                print(F"Package {package_id} has reached its destination.")
            #Dictionary to be converted to JSON in message
            data = {
                'LATITUDE' : node['lat'],
                'LONGITUDE' : node['lon'],
                'TRANSIT_TIME' : (tt * interval),
                'STATUS' : status,
                'DEST_LAT' : dst_lat,
                'DEST_LON' : dst_lon
            }
            data = json.dumps(data)
            key = str(package_id)
            encoded_key = b64encode(key.encode()).decode()
            encoded_value = b64encode(data.encode('utf-8')).decode()
            message = oci.streaming.models.PutMessagesDetailsEntry(key=encoded_key, value=encoded_value)

            #Debug lines, check output being posted to OCI Streaming Service
            #print(F"Key: {package_id} Value: {data}")

            package_message = oci.streaming.models.PutMessagesDetails(messages=[message])
            put_message_result = client.put_messages(stream_id, package_message)

            # The put_message_result can contain some useful metadata for handling failures
            for entry in put_message_result.data.entries:
                if entry.error:
                    print("Error ({}) : {}".format(entry.error, entry.error_message))
                else:
                    print("Published message to partition {} , offset {}".format(entry.partition, entry.offset))

def get_or_create_stream(client, compartment_id, stream_name, partition, sac_composite):

    list_streams = client.list_streams(compartment_id=compartment_id, name=stream_name,
                                       lifecycle_state=oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE)
    if list_streams.data:
        # If we find an active stream with the correct name, we'll use it.
        print("An active stream {} has been found".format(stream_name))
        sid = list_streams.data[0].id
        return get_stream(sac_composite.client, sid)

    print(" No Active stream  {} has been found; Creating it now. ".format(stream_name))
    print(" Creating stream {} with {} partitions.".format(stream_name, partition))

    # Create stream_details object that need to be passed while creating stream.
    stream_details = oci.streaming.models.CreateStreamDetails(name=stream_name, partitions=partition,
                                                              compartment_id=compartment, retention_in_hours=24)

    # Since stream creation is asynchronous; we need to wait for the stream to become active.
    response = sac_composite.create_stream_and_wait_for_state(
        stream_details, wait_for_states=[oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE])
    return response


def get_stream(admin_client, stream_id):
    return admin_client.get_stream(stream_id)


def delete_stream(client, stream_id):
    print(" Deleting Stream {}".format(stream_id))
    print("  Stream deletion is an asynchronous operation, give it some time to complete.")
    client.delete_stream_and_wait_for_state(stream_id, wait_for_states=[oci.streaming.models.StreamSummary.LIFECYCLE_STATE_DELETED])

# Load the default configuration
#config = oci.config.from_file()

#Use instance principal token instead of OCI config file
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

# Create a StreamAdminClientCompositeOperations for composite operations.
stream_admin_client = oci.streaming.StreamAdminClient(config={}, signer=signer)
stream_admin_client_composite = oci.streaming.StreamAdminClientCompositeOperations(stream_admin_client)

if len(sys.argv) != 2:
    raise RuntimeError('This example expects an ocid for the compartment in which streams should be created.')

compartment = sys.argv[1]

# We  will reuse a stream if its already created.
# This will utilize list_streams() to determine if a stream exists and return it, or create a new one.
stream = get_or_create_stream(stream_admin_client, compartment, STREAM_NAME,
                              PARTITIONS, stream_admin_client_composite).data

print(" Created Stream {} with id : {}".format(stream.name, stream.id))

# Streams are assigned a specific endpoint url based on where they are provisioned.
# Create a stream client using the provided message endpoint.
stream_client = oci.streaming.StreamClient(config={}, signer=signer,  service_endpoint=stream.messages_endpoint)
s_id = stream.id

# Publish some messages to the stream
for i in range(10):
    package_id = randrange(10000, 99999)
    #Source is Oracle Waterfront Office
    src_lat = 30.242889
    src_lon = -97.721605
    #Destination restricted to Austin area
    dst_lat = uniform(30.12755, 30.515226)
    dst_lon = uniform(-97.956402, -97.601520)

    route = get_route (src_lat, src_lon, dst_lat, dst_lon)
    publish_data(package_id, route[0], route[1], dst_lat, dst_lon, stream_client, s_id)

# Cleanup; remember to delete streams which are not in use.
#delete_stream(stream_admin_client_composite, s_id)
