#!/bin/bash

# install python requirements
python -m venv venv
pyenv install 3.9.13
pyenv shell 3.9.13
pip install -r requirements.txt

# publish function to function app
func azure functionapp publish 

# create event subscription
az eventgrid system-topic event-subscription create \
    --name VideoUploaded \
    --resource-group transcript-app \
    --system-topic-name BlobEvents \
    --endpoint $(az functionapp function show -g transcript-app -n transcript-app-func-app --function-name TranscribeVideoTrigger -o json | jq .id -r) \
    --endpoint-type azurefunction \
    --subject-begins-with "/blobServices/default/containers/videos" \
    --included-event-types "Microsoft.Storage.BlobCreated"
