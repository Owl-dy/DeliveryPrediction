import oci
import json
import sys
import time
import datetime
from base64 import b64encode, b64decode
from flask import Flask, render_template, Response

# ------------------------------------------------------

# <!--Toms>

from kafka import KafkaConsumer

oci_secret_client = oci.vault.VaultsClient(signer = instance_principal)


connection_parameters = {
    "bootstrap_servers":'cell-1.streaming.ap-seoul-1.oci.oraclecloud.com:9092', 
    "security_protocol":'SASL_SSL', 
    "sasl_mechanism":'PLAIN', 
    "sasl_plain_username": oci_secret_client("<user_name_ocid>"), 
    "sasl_plain_password":oci_secret_client("<password_ocid>")
}

consumer_properties = {
    "auto_offset_reset":'latest',
    "enable_auto_commit":"false",
    "group_id":'test-group'
}

stream_name = 'ds-stream'

def get_kafka_client():

    return KafkaConsumer(stream_name,**({**connection_parameters,**consumer_properties}))

app = Flask(__name__)

@app.route('/')
def index():
    return(render_template('index.html'))

#Consumer API
@app.route('/stream')
def get_messages():
    consumer = get_kafka_client()
    def events():
        for message in consumer:
            yield 'data:{0}\n\n'.format(message.value.decode())
    return Response(events(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5006)



