FROM ubuntu:18.04

WORKDIR /home/opc

COPY rt_iot_streaming.py /home/opc/

COPY requirements.txt /home/opc/

CMD apt-get update

CMD pip install --upgrade pip

CMD pip install -r requirements.txt

CMD python rt_iot_streaming.py ocid1.compartment.oc1..aaaaaaaaynk2ssyaijfxnfy7mcbs46w5xe3agt2xjgr5bmwjzthjlnyd42tq
