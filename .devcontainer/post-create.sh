#!/bin/bash
set -e

echo "Installing Azure Functions Core Tools..."
npm install -g azure-functions-core-tools@4 --unsafe-perm true

echo "Post-create setup complete!"
