import os
import oci 
from oci.vault import VaultsClient
from oci.secrets import SecretsClient
import base64
from sqlalchemy import create_engine
import pandas as pd
from sklearn.utils import Bunch
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
import schedule

#loading up oci conifg
config = oci.config.from_file(
     "~/.oci/config")

#define a method to decode Vault.Secrets
def decode_secret(config, secret_id): 
    """ Given a config file and a secret_id this function 
    will decode a given secret
    """
    
    secrets_client = oci.secrets.SecretsClient(config)
    secret_bundle = secrets_client.get_secret_bundle(secret_id)
    base64_Secret_content = secret_bundle.data.secret_bundle_content.content
    base64_secret_bytes = base64_Secret_content.encode('ascii')
    base64_message_bytes = base64.b64decode(base64_secret_bytes)
    return base64_message_bytes.decode('ascii')


#using sdk to load uri as a Secret from Oracle Vault, passing secret's OCID as argument
uri = decode_secret(config, "ocid1.vaultsecret.oc1.iad.amaaaaaavgi4n5aaab3ta73bxtz4qevfozaem72dzwa4n2wr7utpqvzg5e5q")
os.environ['TNS_ADMIN'] = "/home/datascience/prod/ADB/DBTracing"


def job():
    df = pd.read_sql_query('SELECT longitude, latitude, transit_time, status, dest_long, dest_lat FROM adrien.package where ROWNUM < 10000 order by time_stamp', con=engine)
    ds = DatasetFactory.from_dataframe(df)
    ds = ds.set_target('transit_time')
    transformed_ds = ds.auto_transform()
    transformed_ds.show_in_notebook()
    transformed_ds = transformed_ds[['longitude','latitude','transit_time']]
    train, test = transformed_ds.train_test_split(test_size=0.3)
    X_train = train.X.values
    y_train = train.y.values
    X_test = test.X.values
    y_test = test.y.values
    rdfr = RandomForestRegressor(max_depth=1000, random_state=10).fit(X_train, y_train)
    model_artifact = ads_rdfr.prepare("/home/datascience/model", force_overwrite=True, fn_artifact_files_included=True)
    compartment_id = os.environ['NB_SESSION_COMPARTMENT_OCID']
    project_id = os.environ['PROJECT_OCID']
    mc_model = model_artifact.save(project_id=project_id, compartment_id=compartment_id, display_name="ontime-predict",
                                     description="production ready", training_script_path="getting-started.ipynb", ignore_pending_changes=True)
    
    
schedule.every().day.at("6:30").do(job)
while True:
    schedule.run_pending()
    time.sleep(1)