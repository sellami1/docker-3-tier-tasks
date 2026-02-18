const mongoose = require("mongoose");

const connectDB = async () => {
  const { DB_HOST, DB_PORT, DB_NAME, DB_APP_USER, DB_APP_PASSWORD } =
    process.env;
  const uri = `mongodb://${DB_APP_USER}:${DB_APP_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?authSource=${DB_NAME}`;

  try {
    await mongoose.connect(uri);
    console.log("MongoDB connected successfully");
  } catch (err) {
    console.error("MongoDB connection error:", err);
    throw err;
  }
};

module.exports = connectDB;
