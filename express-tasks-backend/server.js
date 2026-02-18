const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const connectDB = require("./config/db");
const taskRoutes = require("./routes/taskRoutes");

dotenv.config();

const app = express();

// Middleware
const origin = process.env.ORIGIN;
app.use(cors({ origin: origin })); // Enable CORS for all routes
app.use(express.json()); // Parse JSON bodies

// Health check endpoint
app.get("/health", (req, res) => {
  res.status(200).json({ status: "healthy" });
});

// Routes
app.use("/api/tasks", taskRoutes);

// Connect to DB and start server
const PORT = process.env.PORT;
connectDB()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error("Failed to connect to DB:", err);
    process.exit(1);
  });
