const mongoose = require("mongoose");

const taskSchema = new mongoose.Schema(
  {
    title: {
      type: String,
      required: [true, "Title is required"],
      trim: true,
      maxlength: [100, "Title cannot exceed 100 characters"],
    },
    description: {
      type: String,
      required: [true, "Description is required"],
      trim: true,
    },
    status: {
      type: String,
      required: [true, "Status is required"],
      enum: ["pending", "in-progress", "completed"],
      default: "pending",
    },
  },
  {
    timestamps: true, // Adds createdAt and updatedAt
  },
);

module.exports = mongoose.model("Task", taskSchema);
