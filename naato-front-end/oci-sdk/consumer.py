import oci
import json
import sys
import time
from base64 import b64encode, b64decode

STREAM_NAME = "IoT_Stream"
PARTITIONS = 1


def list_stream(client, compartment_id, stream_name, partition, sac_composite):

    list_streams = client.list_streams(compartment_id=compartment_id, name=stream_name,
                                       lifecycle_state=oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE)
    if list_streams.data:
        # If we find an active stream with the correct name, we'll use it.
        print("An active stream {} has been found".format(stream_name))
        sid = list_streams.data[0].id
        return get_stream(sac_composite.client, sid)
    #Assumes stream already exists, no error handling
    else:
        return "error_message"


def get_stream(admin_client, stream_id):
    return admin_client.get_stream(stream_id)

def get_cursor_by_partition(client, stream_id, partition):
    print("Creating a cursor for partition {}".format(partition))
    cursor_details = oci.streaming.models.CreateCursorDetails(
        partition=partition,
        type=oci.streaming.models.CreateCursorDetails.TYPE_TRIM_HORIZON)
    response = client.create_cursor(stream_id, cursor_details)
    cursor = response.data.value
    return cursor

def consume_stream(client, stream_id, initial_cursor):
    cursor = initial_cursor
    while True:
        get_response = client.get_messages(stream_id, cursor, limit=10)
        # No messages to process. return.
        if not get_response.data:
            return

        # Process the messages
        msg_list = []
        print(" Read {} messages".format(len(get_response.data)))
        #print(get_response.timestamp)
        for message in get_response.data:
            #Convert response into JSON
            data = json.loads(b64decode(message.value.encode()).decode())
            data['PACKAGE_ID'] = b64decode(message.key.encode()).decode()
            data['TIMESTAMP'] = message.timestamp
            #print(message.timestamp)
            msg_list.append(data)
            #put_in_adb(data)
        print(msg_list)
            #print("{}: {}".format(b64decode(message.key.encode()).decode(),
            #                      b64decode(message.value.encode()).decode()))

        # get_messages is a throttled method; clients should retrieve sufficiently large message
        # batches, as to avoid too many http requests.
        time.sleep(1)
        # use the next-cursor for iteration
        cursor = get_response.headers["opc-next-cursor"]

#Use instance principal token instead of OCI config file
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

# Create a StreamAdminClientCompositeOperations for composite operations.
stream_admin_client = oci.streaming.StreamAdminClient(config={}, signer=signer)
stream_admin_client_composite = oci.streaming.StreamAdminClientCompositeOperations(stream_admin_client)

#MADHACKS compartment
compartment = 'ocid1.compartment.oc1..aaaaaaaaynk2ssyaijfxnfy7mcbs46w5xe3agt2xjgr5bmwjzthjlnyd42tq'

# We  will reuse a stream if its already created.
# This will utilize list_streams() to determine if a stream exists and return it, or create a new one.
stream = list_stream(stream_admin_client, compartment, STREAM_NAME,
                              PARTITIONS, stream_admin_client_composite).data

# Streams are assigned a specific endpoint url based on where they are provisioned.
# Create a stream client using the provided message endpoint.
stream_client = oci.streaming.StreamClient(config={}, signer=signer,  service_endpoint=stream.messages_endpoint)
s_id = stream.id

print(" Consuming Stream {} with id : {}".format(stream.name, stream.id))
partition_cursor = get_cursor_by_partition(stream_client, s_id, partition="0")
consume_stream(stream_client, s_id, partition_cursor)