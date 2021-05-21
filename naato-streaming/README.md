### Table of Contents
1. Provision the Infrastructure
2. Pull the code repo
3. Build the docker image and push to OCIR
4. Kubernetes deployment
  - Making the deployment YAML file
  - Applying deployment to cluster
5. Verify Deployment
​
​
### Provision the Infrastructure
​
For this project we'll be using the following services:
- OCI Streaming Service
  - Configure Dynamic Groups
  - Write IAM policy for Dynamic Group
- OCI Container Registry Service (OCIR)
  - Generating an Authentication Token
- OCI Container Engine for Kubernetes (OKE)
  - Connecting to your OKE cluster
​
​
#### OCI Streaming Service
For this project we don't need to worry about creating the Streaming Service itself in OCI as once properly configured the code responsible for producing data will create the stream for us. With that in mind we'll be using Dynamic Groups in order to give access to the nodes in the cluster to Streaming Service.
​
First up creating a Dynamic Group:
1. Navigate to the menu in the upper right hand corner and scroll down all the way to Identity > Dynamic Groups
2. Click "Create Dynamic Group"
3. Give it a name & description, we used **Streaming_Group**
4. Use the following rule:
​
`instance.compartment.id = [your_compartment_OCID]`
5. Go to Identity > Policies, click "Create Policy"
6. Give it a name & description, we used **Streaming_Policy**
7. In the Policy Builder click "Customize" to paste in the following policy
​
`Allow dynamic-group [Streaming_Group] to manage streams in tenancy`
​
With this we setup any instance within the compartment of your choice to access OCI Streaming Service without having to store credentials on the instance itself such as API Auth Tokens.
​
If you wanted to get granular with our policy one could narrow down the matching policy in the Dynamic Group by using tags instead of matching on the compartment but this isn't covered in this project.
​
​
#### OCI Container Registry Service (OCIR)
There are actually two ways you go about setting up a repository in OCIR:
- Use the OCI console to create an empty repository
- Using Docker push your tagged image to OCIR were it will create the repository if it doesn't already exist.
​
We'll be using the Docker to create ours as it gives us a chance to demonstrate how to login into OCIR from Docker.
​
Follow the documented steps regarding [pushing images to OCIR](https://docs.cloud.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm).
​
Additional steps include the following:
1. In the directory where you pulled the code run:
`docker build .`
2. This should create the image you'll push to the repo, follow the directions in the documentation and tag accordingly.
​
#### OCI Container Engine for Kubernetes (OKE)
For our project we'll use a K8s cluster to deploy our container we made in the previous step.
1. Provision a cluster in the OCI Console by navigating the top left menu under Solutions and Platform, Developer Services > Kubernetes Clusters
2. Click "Create Cluster"
3. Choose "Quick Create" and click "Launch Workflow"
4. Give it a name, we used **iot_cluster**.
  - Specify the compartment you choose to use when creating the Dynamic Group matching rule.
  - Leave the default for the Kubernetes Version (v1.18.10)
  - Choose Public
  - Select the Shape "VM.Standard.E2.1"
  - Number of Nodes: **3**
  - (Optionally) Click advance and paste a public SSH key.
5. Click "Next" and review the resources to be created before clicking "Create Cluster".
6. Wait for cluster to provision before clicking "Access Cluster". We used Cloud Shell but follow the instructions for method of connection.
7. Once you have your kubeconfig file from the cluster run the following command:
`kubectl apply -f deployment.yaml`
- (Optional) You can display information about the deployment but using `kubectl get deployments producer`, `kubectl describe deployments producer` and `kubectl get pods`. However since there is no front-end for this code there isn't much to interact with the nodes themselves. Good for checking if it is running though.
​
#### Verify Deployment
By now all the necessary infrastructure and code should be up and running.
- Check to see if the nodes are posting to the streaming service by navigating to
 `Solutions and Platform, Analytics > Streaming`.
- You should see a stream called **IoT_Stream** if you didn't modify the code, click on it to see the details of the stream.
- On the details page click "Load Messages", you should see the output of all the nodes posting log data to the stream in the last minute.  
​
Congratulations, you should be successfully posting simulated package data to OCI Streaming Service where it is ready to be consumed by other services such as our Autonomous Database or Front-End package tracker.