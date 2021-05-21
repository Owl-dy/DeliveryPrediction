### Table of Contents
---
1. Provision the OCI-Data Science and Necessary Resources
2. Set Up OCI Configuration
3. Set Up ADB Connection
4. Training Machine Learning Model
  -- Exploratory Data Analysis
  -- Training K-Nearest-Neighbor and Random Forest Model
5. Save Model to OCI Model Catalog
6. Deploy Using Cloud Shell and Fn Project
7. Create An API-Gateway
​
​
### Provision the OCI-Data Science and Necessary Resources
---
For this project we'll be using the following services:
- A VCN with Private Subnet and NAT Gateway
- OCI Data Science [follow Data Science quickstart]
  - Configure Dynamic Groups
  - Write IAM policies for Dynamic Group 
​
​
---
#### Set Up OCI Configuration
- Authendicate using `Resource Principle`:
```
import ads 
import oci 

from oci.data_science import DataScienceClient 
resource_principal = oci.auth.signers.get_resource_principals_signer() 
dsc = DataScienceClient(config={},signer=resource_principal)
ads.set_auth(auth='resource_principal') 
```
- Validate connection using oci-cli:
```
%%bash 
oci data-science project get --project-id=$PROJECT_OCID
```
*More detailed instructions followed the "Get Started Notebook" in the notebook session*
​
​
----

#### Set Up ADB Connection
- Upload your ADB's Wallet File and save it to folder `/ADB`
- Store URI ADB connection string as **Secrets** to **OCI Vault**, then use the following code to authenticate:
```
import os
import oci 
from oci.vault import VaultsClient
from oci.secrets import SecretsClient
import base64

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
uri = decode_secret(config, "<OCID FROM OCI VAULT FOR YOUR ADB CONNECTION URI STRING>")
os.environ['TNS_ADMIN'] = "/home/datascience/prod/ADB/<YOU ADB NAME>"
```

*More detailed instructions followed the "Ontime Model Prediction" notebook in this git repo*
​
​
----
#### Training Machine Learning Model
- The Code for training the Ontime Prediction Model is included in this git repo (see the notebook)
- Execute Line by line to see how a normal data scientist would train a Machine Learning Model
Use the `/scheduler.py` file for automatic re-training
​
​
---
#### Save Model to OCI Model Catalog
- The Code for saving the model to OCI Model Catalog is also included in this git repo (see the notebook)
Use the `/scheduler.py` file for automatic saving newly trained model to OCI Model Catalog
​
​
---
#### Deploy Using Cloud Shell and Fn Project
- Create an applications in **Functions**
- Open Cloud Shell
- Retrieve the Model Artifact Content from the Model Catalog using OCI-CLI:
```
oci data-science model get-artifact-content --model-id <YOUR MODEL'S OCID> --file model.zip
unzip model.zip -r -d model
cd model
```
- Deploy the model to **Oracle Functions** using **Fn**
```
fn -v deploy --app <THE NAME OF YOUR APP>
```
- Go to **OCI-Registery** and **Functions** to verify deployment
​
​
----
#### Create An API-Gateway
- Create an **API Gateway** (under developer services)
- Create a Deployment and select "From Scratch"
- Select POST as method and Oracle Functions as Backend, then selecting the right Function within your application
- Use `Curl` to test for API (a sample json payload file included in this repo):
```
curl -k -X POST <YOUR END POIN>/<Prefix>/<path> -d @payload.json --header "Content-Type: application/json”
```
- sample results like this:
`{"prediction": ["On Time", "Late"]}`


