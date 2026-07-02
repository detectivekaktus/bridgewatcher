#!/usr/bin/env bash

set -e

echo "Starting MongoDB setup script"

mongosh admin <<EOF
    db = db.getSiblingDB("admin");

    db.createUser({
        user: "${MONGO_USERNAME}",
        pwd: "${MONGO_PASSWORD}",
        roles: [
            { role: "readWrite", db :"${MONGO_DB}" }
        ]
    });
EOF

echo "Setup script finished"