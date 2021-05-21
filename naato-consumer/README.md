### Table of Contents
1. Provision Autonomous Database Warehouse
2. Provision a VM or use your existing workstation
3. Install necessary libraries
4. Upload database wallet file and update database credentials
5. Update compartment OCID with the OCID of your OCI streaming compartment and the stream name of your stream
6. Run the Python script to consume the stream and inject it to the Autonomous database Warehouse
​

### Provision the Infrastructure
- Autonomous Database Warehouse
  - Create necessary tables in the database
  - Note down the Username and password for the database where the tables are created

#### Setting up workstation

For this Project we used a VM in OCI using the developer cloud image. Based on the image you are using you will need to have python, oci cli, cx_oracle and oracle-release-el7 installed. 
After installing Oracle instant client you will also need to add it to the runtime link path. 
`sudo sh -c "echo /usr/lib/oracle/18.3/client64/lib > /etc/ld.so.conf.d/oracle-instantclient.conf"`

You will also need to set up oci cli config file with credentials to connect to your tenancy with the streaming service and ADW. If you are using a VM in the same tenancy you can also use instance principal by setting setting the environment variable to instance principal.
`OCI_CLI_AUTH=instance_principal`

#### Download Wallet file

You can either download the wallet file from the console and scp to you workstation or if you have set up oci cli you can also download the wallet file using the following command. You will need to add the OCID of the database and the password.
`oci db autonomous-database generate-wallet --autonomous-database-id $DB_ID --password MYPASSWORD123 --file wallet_consumer.zip`

After downloading the wallet you will need to unzip it and change permissions so it can be accessed. Run the following commands to save the wallet file contents to a directory called consumer.
`sudo mkdir -pv /etc/ORACLE/WALLETS/consumer`
`sudo chown -R opc /etc/ORACLE`
`cd /etc/ORACLE/WALLETS/consumer`
`unzip ~/wallet_consumer.zip`
`sudo chmod -R 700 /etc/ORACLE`

You will then need to edit the sql.ora file in the wallet directory with the path of the wallet file.
`nano /etc/ORACLE/WALLETS/consumer/sqlnet.ora`
Edit the file to make it look like
`WALLET_LOCATION = (SOURCE = (METHOD = file) (METHOD_DATA = (DIRECTORY="/etc/ORACLE/WALLETS/consumer")))
SSL_SERVER_DN_MATCH=yes`

Set the TNS_ADMIN environment variable to point Instant Client the Oracle
`export TNS_ADMIN=/etc/ORACLE/WALLETS/ATP1`

#### Edit mad_consumer.py
Edit the python file with the stream name, compartment OCID, table name and column names according to your configuration.
Add the username of the database followed by the password and connection type in the connection string for cx_oracle

#### Run
After setting up your database and specifying the connection to the python file and editing the file with the correct Compartment OCID and connection information you can run the python file.
`Python mad_consumer.py`

This will connect the OCI streaming service and check for any streams to consume. If it finds any availabe stream in the compartment you specified if will start consuming and also connect to the database and inject the stream to the database.