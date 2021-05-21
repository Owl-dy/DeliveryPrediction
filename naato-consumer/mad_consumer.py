import oci
import json
import sys
import time
from base64 import b64encode, b64decode
import cx_Oracle
import os

#os.system("export TNS_ADMIN=/etc/ORACLE/WALLETS/ATP1")


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
    connection = cx_Oracle.connect("admin","Welcome#12345","dbtracing_low")
    cur = connection.cursor()

    cursor = initial_cursor
    while True:
        get_response = client.get_messages(stream_id, cursor, limit=10)
        # No messages to process. return.
        if not get_response.data:
            return

        # Process the messages
        print(" Read {} messages".format(len(get_response.data)))
        data_list = []
        for message in get_response.data:
            #Convert response into JSON
            data = {}
            data['PACKAGE_ID'] = b64decode(message.key.encode()).decode()
            data.update(json.loads(b64decode(message.value.encode()).decode()))
            data['TIMESTAMP'] = message.timestamp
            
            tmp_list = []
            for x in data:
                tmp_list.append(data[x])
            
            data_list.append(tmp_list)
        print(data_list)
            #print("{}: {}".format(b64decode(message.key.encode()).decode(),
            #                      b64decode(message.value.encode()).decode()))
        
        # get_messages is a throttled method; clients should retrieve sufficiently large message
        # batches, as to avoid too many http requests.
        time.sleep(1)
        # use the next-cursor for iteration
        cursor = get_response.headers["opc-next-cursor"]

        sql = "INSERT INTO ADRIEN.PACKAGE ("

        sql += "PACKAGE_ID,"
        sql += "LONGITUDE,"
        sql += "LATITUDE,"
        sql += "TRANSIT_TIME,"
        sql += "STATUS,"
        sql += "DEST_LONG,"
        sql += "DEST_LAT,"
        sql += "TIME_STAMP"

        sql += ") VALUES ("
        sql += ":1,:2,:3,:4,:5,:6,:7,:8"
        sql += ") "

        cur.executemany(sql,data_list)
        connection.commit()
    cur.close()


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