#!/bin/bash
set -e

# robust_upload.sh
# A wrapper around curl to perform robust uploads to GitHub Releases.
# Useful for unstable networks where the 'gh' CLI fails with TLS errors.

# Configuration
OWNER="AreTaj"
REPO="Migraine-Navigator"

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <TAG_NAME> <FILE_PATH> [GITHUB_TOKEN]"
    echo "Example: $0 v0.1.1 releases/Migraine_Navigator_0.1.0_aarch64.dmg"
    exit 1
fi

TAG_NAME=$1
FILE_PATH=$2
# Try to get token from gh cli if not provided as argument
TOKEN=${3:-$(gh auth token)} 

if [ -z "$TOKEN" ]; then
    echo "Error: GitHub token not found. Please provide it as the 3rd argument or ensure you are logged in with 'gh auth login'."
    exit 1
fi

FILENAME=$(basename "$FILE_PATH")

echo "---------------------------------------------------"
echo "Robust Upload Tool"
echo "Target: $OWNER/$REPO @ $TAG_NAME"
echo "File:   $FILENAME"
echo "---------------------------------------------------"

echo "Fetching Release ID for tag: $TAG_NAME..."
# Get Release ID using gh api (requires jq or gh's --jq flag)
RELEASE_ID=$(gh api "repos/$OWNER/$REPO/releases/tags/$TAG_NAME" --jq '.id')

if [ -z "$RELEASE_ID" ] || [ "$RELEASE_ID" == "null" ]; then
    echo "Error: Could not find release ID for tag '$TAG_NAME'. Does the release exist?"
    exit 1
fi

echo "Found Release ID: $RELEASE_ID"
echo "Starting Upload via curl (HTTP/1.1 forced)..."

UPLOAD_URL="https://uploads.github.com/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=$FILENAME"

# Robust Curl Command
# -v: Verbose (to see handshake)
# --http1.1: Force older protocol (more stable on bad connections)
# --fail: Fail explicitly on server errors
curl -v --fail \
    --http1.1 \
    -H "Authorization: token $TOKEN" \
    -H "Content-Type: application/octet-stream" \
    --data-binary @"$FILE_PATH" \
    "$UPLOAD_URL"

echo -e "\n---------------------------------------------------"
echo "Upload Process Finished."
