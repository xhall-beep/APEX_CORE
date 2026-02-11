#!/bin/bash
REPO_URL=$1
REPO_NAME=$(basename $REPO_URL .git)
echo "🔱 INGESTING: $REPO_NAME..."
mkdir -p ./legacy_vault/ingested_tools
git clone --depth 1 $REPO_URL ./legacy_vault/ingested_tools/$REPO_NAME
rm -rf ./legacy_vault/ingested_tools/$REPO_NAME/.git
# Immediately map to the Global Index
find ./legacy_vault/ingested_tools/$REPO_NAME -maxdepth 2 >> ./deliveries/global_index.txt
echo "🔱 $REPO_NAME INTEGRATED INTO ARSENAL."
