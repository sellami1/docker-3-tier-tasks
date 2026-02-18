const Task = require("../models/task");

// Get all tasks
exports.getAllTasks = async (req, res) => {
  try {
    const tasks = await Task.find().sort({ createdAt: -1 });
    res.status(200).json(tasks);
  } catch (err) {
    res.status(500).json({ message: "Server error", error: err.message });
  }
};

// Get single task by ID
exports.getTaskById = async (req, res) => {
  try {
    const task = await Task.findById(req.params.id);
    if (!task) {
      return res.status(404).json({ message: "Task not found" });
    }
    res.status(200).json(task);
  } catch (err) {
    res.status(500).json({ message: "Server error", error: err.message });
  }
};

// Create new task
exports.createTask = async (req, res) => {
  try {
    const { title, description, status } = req.body;
    const newTask = new Task({ title, description, status });
    await newTask.save();
    res.status(201).json(newTask);
  } catch (err) {
    res.status(400).json({ message: "Invalid data", error: err.message });
  }
};

// Update task by ID
exports.updateTask = async (req, res) => {
  try {
    const updatedTask = await Task.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true,
    });
    if (!updatedTask) {
      return res.status(404).json({ message: "Task not found" });
    }
    res.status(200).json(updatedTask);
  } catch (err) {
    res.status(400).json({ message: "Invalid data", error: err.message });
  }
};

// Delete task by ID
exports.deleteTask = async (req, res) => {
  try {
    const deletedTask = await Task.findByIdAndDelete(req.params.id);
    if (!deletedTask) {
      return res.status(404).json({ message: "Task not found" });
    }
    res.status(200).json({ message: "Task deleted" });
  } catch (err) {
    res.status(500).json({ message: "Server error", error: err.message });
  }
};
