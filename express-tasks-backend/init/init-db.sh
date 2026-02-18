#!/usr/bin/env bash

set -e  # Exit on any error

mongosh -u "${MONGO_INITDB_ROOT_USERNAME}" -p "${MONGO_INITDB_ROOT_PASSWORD}" --authenticationDatabase admin <<EOF
// Switch to the app database
db = db.getSiblingDB("${DB_NAME}");

// Create dedicated app user (idempotent)
var appUser = "${DB_APP_USER}";
var appPwd = "${DB_APP_PASSWORD}";

var existingUser = db.getUser(appUser);
if (!existingUser) {
  db.createUser({
    user: appUser,
    pwd: appPwd,
    roles: [{ role: "readWrite", db: "${DB_NAME}" }]
  });
  print("Created dedicated app user: " + appUser);
} else {
  print("Dedicated app user already exists: " + appUser);
}

// Ensure collection exists (optional, insert will create it)
db.createCollection("tasks");

// Insert sample data only if collection is empty (idempotent)
if (db.tasks.countDocuments({}) === 0) {
  db.tasks.insertMany([
    {
      title: "Sample Task 1",
      description: "This is a sample description for task 1.",
      status: "pending"
    },
    {
      title: "Sample Task 2",
      description: "This is a sample description for task 2.",
      status: "in-progress"
    },
    {
      title: "Sample Task 3",
      description: "This is a sample description for task 3.",
      status: "completed"
    }
  ]);
  print("Inserted sample tasks");
} else {
  print("Tasks collection already has data; skipping initialization");
}
EOF