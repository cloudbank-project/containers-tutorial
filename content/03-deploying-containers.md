---
draft: false
title: "Part 3: Deploying containers"
aliases:
    /03-deploying-containers.html
---

## Publishing images on Docker Hub

The easiest way to get your new image onto other computers is by **pushing** your image to your Docker Hub account. First things first, log in to your Docker Hub account via the CLI. Open a terminal in VS Code and run:

```bash
docker login
```

Follow the prompts to provide your username and password, and confirm that you see the message `Login Succeeded`.

Next, use the `push` command to publish the image you built in the previous section:

```bash
docker push [DOCKERHUB-USERNAME]/my-textbook
```

replacing `[DOCKERHUB-USERNAME]` appropriately. This will upload the image, including all of the files you copied into it, to Docker Hub. Note that because it will now be publicly available across the web, **you should make sure not to include any sensitive information, like account passwords, in the image itself**. If that kind of data is required, mount the files containing it at run-time or use environment variables.

The CLI will begin the process of uploading your container files to Dockerhub, after which it should display output that looks like the following:

```bash
Using default tag: latest
The push refers to repository [docker.io/naclomi/my-textbook]
3cc02027512c: Pushed 
39712aead534: Pushed 
1fe39d5d8cc8: Pushed 
321644d0af15: Pushed 
520dcae2068c: Mounted from library/python 
929becff1737: Mounted from library/python 
3652ad81051a: Mounted from library/python 
931a85bd816c: Mounted from library/python 
8764e431c07e: Mounted from library/python 
19ab65c2eea3: Mounted from library/python 
d2fb5ee0c8fd: Mounted from library/python 
7d8e945003fe: Mounted from library/python 
70fd9a3b3b80: Mounted from library/python 
latest: digest: sha256:a736b12cdf30fc6fd7605aacdf8487f189102875048fd5b638d3cffd3253041d size: 3054
```

Your image is now on the web! You can see and alter information about it from your account dashboard at https://hub.docker.com/:

![docker_web_dash](../img/docker_web_dash.png)

At this point, others can run your image on their computers using the same `docker run` commands we've practiced before:

```bash
docker run --rm [YOUR-DOCKERHUB-USERNAME]/my-textbook
```

Have a friend try it out on their computer 🙂 .

## Containers in the cloud

We can run instances of our container image in the cloud, if we need access to more powerful computers or more storage than we have available locally. In this way,  we are thinking of the cloud as a supercomputer that we submit jobs to in the form of Docker container images. 

A classic example might be to develop an ML model training script on your computer over a small subset of the data you have access to, and then deploy it to the cloud in a container where it will train on a beefy computer over the full dataset.

## Setting up the Azure CLI

There are many ways to run a Docker container in Microsoft Azure. The most general-purpose of which is a service they provide called **Azure Container Instances**. We'll use the **Azure CLI** to interact with it. Make sure your terminal is logged in to Azure with the command by running this command and then following its instructions. It may ask you which subscription to use -- **your course staff should tell you which one to use for this class. If you're not sure, ask them.**

```bash
az login
```

Next, we'll tell the CLI what **resource group** to work within. The resource group is specific to you, and is like a cloud "folder" containing all of the Azure services you'll create or use. Find its name by running the following command:

```bash
az group list --output table
```

If you have more than one in the output, choose the one with your UW NetID in the name. Copy the full resource group name and set it as the default with this command:

```bash
az configure --defaults group=[GROUP NAME]
```

replacing [GROUP NAME] with the value you just noted down. 

To confirm everything is working, try running the command: 

```bash
az resource list --output table
```

If your CLI is configured properly, this command will return all of the Azure services and objects currently in your resource group (which you can also inspect through the Azure web portal -- it's the same stuff, just a different method of interacting with it).

## Running containers in Azure

### Getting the image into Azure

We already pushed our image to Dockerhub, but to use it in the Azure cloud we'll need to push it there too. Azure accounts can store container images very much like Dockerhub does, in something called a **container registry**. Dockerhub itself is a container registry that's public and accessible from your laptop. For this section, we're going to use a private container registry housed in your Azure resource group. 

Scroll back up to the output of that `az resource list --output table` command you ran. You should find a container registry named like `contreg[_____]`, where the `[_____]` is your UW NetID:

![](../img/contreg.png)
 
We can connect the `docker` command to it (so that we can push images to it) by running the command:

```bash
 az acr login --name [YOUR-REGISTRY-NAME]
```

Where the `[YOUR-REGISTRY-NAME]` is replaced with your container registry's name (including the `contreg` part at the beginning). If it worked, you should see the message `Login Succeeded`.

Next, try running the command:

```bash
az acr show-endpoints --name [YOUR-REGISTRY-NAME] --output table
```

This will show us a table of URLs. The 'LoginServer' represents the registry's location on the internet. **We'll call this "the registry's URL" from here on out**:

![](../img/contreg-url.png)

We can push and pull images from the registry by preceding any image name with that URL and a slash. So, while this would refer to Naomi's textbook image on Dockerhub:

```bash
nananaomi/my-textbook
```

this would refer to the same image stored in her Azure container registry:

```bash
contregnananaomi.azurecr.io/nananaomi/my-textbook
```

With all that out of the way, let's push our textbook writer to the container registry. Start by adding a new tag to your image that starts with your registry URL, replacing the `[...]` segments as necessary in the command below:

```bash
docker tag [YOUR-DOCKERHUB-USERNAME]/my-textbook [YOUR-CONTAINER-REGISTRY-URL/[YOUR-DOCKERHUB-USERNAME]/my-textbook
```

Then push it:

```bash
docker push [YOUR-CONTAINER-REGISTRY-URL/[YOUR-DOCKERHUB-USERNAME]/my-textbook
```

The image will take a few minutes to upload. After it's done, you should be able to verify Azure has it with this command:

```bash
az acr repository list --name [YOUR-CONTAINER-REGISTRY-NAME]
```

If it's not there, ask your course staff for help.

### Running your image

To run a container as an Azure Container Instance we'll use the `az container create` command, which is like a cloud version of `docker pull` and `docker run` combined into one command. It'll take the following form:

```bash
az container create \
  --name [INSTANCE NAME] \
  --image [PUSHED IMAGE NAME]
  --os-type Linux \
  --cpu [CORES] \
  --memory [GB RAM] \
  --registry-login-server [CONTAINER REGISTRY NAME].azurecr.io \
  --registry-username $(az acr credential show --name [CONTAINER REGISTRY NAME] --output tsv --query 'username') \
  --registry-password $(az acr credential show --name [CONTAINER REGISTRY NAME] --output tsv --query 'passwords[0].value') \
  --restart-policy Never \
  --no-wait
```

There's a lot going on here. Let's step through it:

* The `[INSTANCE NAME]` is a name you'll use to refer to this container in your cloud account. It can be whatever you want as long as it doesn't have spaces. Let's use something like `my-cloud-textbook`.
* The `[PUSHED IMAGE NAME]` refers to the image you pushed to your container registry. In the case of this tutorial, that was `[YOUR CONTAINTER REGISTRY URL]/[DOCKERHUB USERNAME]/my-textbook`
* The `--os-type Linux` flag specifies the operating system our image uses. That is: Linux.
* The `--cpu [CORES]` flag specifies how many CPU cores we need to run our container. We're not doing much computation for this example, so to save money let's set it to something small like `0.5`. 
* The `--memory [GB RAM]` flag specifies how much RAM we need to run our container. Similarly to the CPU flag, let's use `0.5`. 
* The `--registry-login-server`, `--registry-username` and `--registry-password` fields all tell Azure how to log into and get images out of your container registry. There is a lot of complex stuff here -- just make sure to fill in your registry's URL in the right spot in each flag, and you should be fine. Ask your course staff if you're curious about how these lines work.
* The `--restart-policy Never` flag tells Azure that after our container finishes running, it should just be left in a stopped state. **This is important**, because without it **the container would get re-run in a loop indefinitely**, until we manually stopped it, and this could use up a lot of resources (eg, $$$). The default behavior is useful when a container runs an always-available service like a web server, but for our purposes is really really not what we want.
* The `--no-wait` flag tells the terminal to not hang and wait until the container is set up. Deployment can take a while, since Azure has to find an unused computer in the cloud and download our image to it, so this will let us do other terminal operations while that all is happening.

We'll master all of those options, the more we use Azure. For now, just copy and paste the command with the appropriate values replacing the blanks denoted by `[]`s. It might help to copy it into a text editor first, fill in the `[]`-blanks there, and then copy _that_ to your termainal.

To confirm that your container was created, run the following command which _should_ show your new container in the table:

```bash
az container list --output table
```

![new_container](../img/az-container-list.png)

Right now the container's status is `Pending`, but after a few minutes it should change to `Succeeded`. Once it does, try running the command:

```bash
az container logs --name my-cloud-textbook
```

If you named your container instance something else, just replace `my-cloud-textbook` with the appropriate value.

This command will print the output of the container (the stuff that would show up in our terminal automatically after `docker run`, if we were running locally). You should now see some quality garbage:

![cloud_garb](../img/cloud_garb.png)

If the command doesn't output anything, or returns an error, try waiting a bit longer for the cloud to finish pulling your image. If it's taking a while, you can see Azure's progress with the command:

```bash
az container show --name my-cloud-textbook
```

This outputs a lot of detailed information about the container, including when it started and completed pulling the image from the container registry:

![cloud_progress](../img/cloud_progress.png)

In general you want to delete cloud resources like this as soon as you're done with them, to ensure they don't use up funds. That said, if this container is going to be reviewed as a part of your class grade **you should wait to delete it until your TA has looked it over**. Once you _are_ ready to delete it, you can do so with this command:

```bash
az container delete --name my-cloud-textbook
```

**Do make sure to remember to go back and delete the container once your TA has looked at it**, to make sure you don't leave resources in the cloud that may use up funds. To be sure it's deleted, try running the `az container list --output table` command again and confirming that the table is empty.

## Using cloud file stores for Azure container input/output

To get files in and out of a container running in Azure, we can mount Azure file stores similarly to how we mount folders when we use `docker run` locally. Let's get some practice with this by asking our docker image to export its text as a file rather than printing it to the screen.

### Creating a file store

Let's start by creating a file store for the container output. It's a little convoluted, but Azure file stores exist within an administration hierarchy that looks like this:

```bash
Subscription (eg, billing)
  ┕━ Resource Group
      ┕━ Storage Account
          ┕━ File Share
              ┕━ Your files
```

Yikes, right? Anyway, we need to create a new storage account, and then within that create a file share. Then, when we start our Docker container, we can point it towards that file share and it put stuff in it.

Start by going to the Azure portal and searching `storage` at the top. Select the `Storage Accounts` option:

![](../img/az-storage-1.png)

From the storage accounts dashboard, click `+ Create` to make a new one:

![](../img/az-storage-2.png)

From here, we'll be able to choose some options for the new account:

![](../img/az-storage-3.png)

Make the following selections:

- **Subscription**: Make sure to select the proper subscription for this class (that includes the term `MSE544`)
- **Storage account name**: This name has to be globally unique on Azure's cloud, so choose something that starts with your UW NetID. Unfortunately, it can only include letters and numbers (no spaces, dashes or other symbols).
- **Redundancy**: This option controls how your data is backed up. Select **`Locally redundant storage (LRS)`**, which keeps backups of your data in the same physical datacenter as the main account. Geo-rendundant storage is more expensive and keeps backups in different physical regions of the world, which is generally good practice but overdoing it for this exercise.

When you're done, click the blue `Review + create` button at the bottom, and then the blue `create` button at the confirmation screen to finish the process.

After a minute or two, the storage account will become available and you'll see a blue `Go to resource` button. Click that:

![](../img/az-storage-4.png)

From this dashboard, we can see and manage the file shares that will actually contain our data. Let's create a file share to hold the textbook our docker container outputs.

Choose `File shares` from the menu on the left (1), and then click the `+ File share` button (2) to create a new one within our storage account:
![](../img/az-storage-new-fileshare.png)

Give the file share a name like `container-output`. This doesn't have to be globally unique across the whole cloud, so we don't have to put our NetID in the name or anything like that. When you're done, click the `Next: Backup >` button:

![](../img/az-storage-new-fileshare-2.png)

Uncheck the `Enable backup` option, which isn't generally a bad thing but unneeded for this exercise (you can always just rerun your container if for some reason the output gets lost):
![](../img/az-storage-new-fileshare-3.png)

Finally, click the `Review + create` button at the bottom, and then the blue `Create` button to finish creating the file share.
Now we're ready to run a container that connects to it.

We'll be brought to a summary page showing the file share. This is how we'll download our container output later, but for now, return to the storage account dashboard by clicking the right-most link in the path at the top of the screen (circled in red here):

![](../img/az-storage-fileshare-back.png)

### Mounting file stores in containers

To connect the file share to our cloud containers, we'll add a few extra options to our `az container create` command:

- `--azure-file-volume-account-name [NAME]`
  The name of the storage account that we created.

- `--azure-file-volume-account-key [KEY]`
  The key to the storage account that we created. In the command exmaple below, we retrieve it with some fancy terminal magic similar to how we got the container registry password.

- `--azure-file-volume-share-name [NAME]`
  The name of the file share *within* the storage account we created.

- `--azure-file-volume-mount-path [CONTAINER PATH]`
  The path inside of the container to mount the share to. This is like the second half of the `-v [LOCAL PATH]:[CONTAINER PATH]` flag that you pass to `docker run` when running containers on your workstation or personal computer.

In addition to the above flags that mount a file share to our container, we also need to tell the container to generate file output instead of screen output. Unlike the Docker CLI, Azure doesn't let us add extra flags when we run the container, it only lets us replace the entrypoint entirely:

- `--command-line "[COMMAND HERE]"`
  This flag will replace the container entrypoint with whatever you specify in double-quotes. This is the equivalent of `--entrypoint` when using `docker run`.

We'll mount the file share to the location `/output` in our container, and then save a file there called `text.txt` by using then entrypoint "`python3 src/main.py --txt /output/textbook.txt`".

Copy and execute the command line below, replacing the `[ ]`-indicated blanks with their appropriate values. It's probably a good idea to first copy this content into a blank text file, replace the `[ ]`-blanks, and then copy _that_ into your terminal.

The command will look like:

```bash
az container create \
   --name my-cloud-textbook \
   --image [PUSHED IMAGE NAME] \
   --cpu 0.5 --memory 0.5 \
   --restart-policy Never --no-wait \
   --command-line "python3 src/main.py --txt /output/textbook.txt" \
   --registry-login-server [CONTAINER REGISTRY NAME].azurecr.io \
   --registry-username $(az acr credential show --name [CONTAINER REGISTRY NAME] --output tsv --query 'username') \
   --registry-password $(az acr credential show --name [CONTAINER REGISTRY NAME] --output tsv --query 'passwords[0].value') \
   --azure-file-volume-account-name [STORAGE ACCOUNT NAME] \
   --azure-file-volume-account-key $(az storage account keys list --account-name [STORAGE ACCOUNT NAME] --query '[0].value' --output tsv) \
   --azure-file-volume-share-name [FILE SHARE NAME] \
   --azure-file-volume-mount-path output
```

Oof, it's complicated, but it's powerful. Good job command line warrior. Run it, and then wait a minute or two for Azure to complete its work. As before, you can check the status of the container with the command:

`az container list --output table`

Once the status reports `Succeeded`, go to your storage account's web dashboard and select `File shares` (1), then open your file share (2):

![](../img/az-file-dl-1.png)

From here, select `Browse` on the left (1) to view the files inside the store. We should see the text file our container created! Click it (2). This will open a file properties box, from which we can hit the `Download` button (3):

![](../img/az-file-dl-2.png)

From here, we can open the file up using your computer's file explorer:

![downloaded_pdf](../img/downloaded_pdf.png)

Congratulations -- this was a lot of steps for some pretty advanced computing, and you did it!

Now that the file share is created, you can rerun the container with `az container start` or create new ones that connect to the share with `az container create` as much as you like. The steps preceding the `az container create` command only have to be done once.

## Stretch challenge #1

Did you add PDF generation support to your image in the previous tutorial's stretch challenge? If so, change your cloud container here to generate a PDF instead of a TXT file. If not, go back and add PDF support!

### Cleaning up

Wait until your course staff have recorded that you've successfully run the tutorial, and then delete all of the resources you used from Azure once you're done.

Use the `az container delete --name [NAME]` command to delete any containers shown by the `az container list --output table` for the containers.

Delete your storage account by going to `Overview` on the storage account dashboard (1) and clicking `Delete` (2). Then, follow the confirmation instructions to finish deleting it:

![](../img/az-file-delete.png)
