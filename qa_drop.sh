#!/bin/bash

source .env

random_number=$RANDOM
cd output/nodereal-app
git checkout main
git pull
git checkout -b drop-opbnb-qanet-$QANET_NAME-$random_number
rm -rf qa/gitops/init-argocd/auto-aps/$QANET_NAME.gold-digger.yaml
rm -rf qa/gitops/init-argocd/auto-aps/$QANET_NAME.nebula-apus.yaml
rm -rf qa/gitops/init-argocd/spec/$QANET_NAME
rm -rf qa/gitops/qa-us/$QANET_NAME
git add --all
git commit -m "drop opbnb qanet $QANET_NAME"
git push origin drop-opbnb-qanet-$QANET_NAME-$random_number
