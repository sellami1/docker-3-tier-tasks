import { useState } from "react";
import api from "../api";

function TaskForm({ onTaskAdded }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("pending");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;

    try {
      const response = await api.post("/api/tasks", {
        title,
        description,
        status,
      });
      onTaskAdded(response.data);
      setTitle("");
      setDescription("");
      setStatus("pending");
    } catch (err) {
      alert("Failed to add task");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
      <input
        type="text"
        placeholder="✏️ What needs to be done?"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
      />
      <textarea
        placeholder="📝 Add a description..."
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        required
      />
      <div className="form-row">
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="pending">⏳ Pending</option>
          <option value="in-progress">🔥 In Progress</option>
          <option value="completed">✅ Completed</option>
        </select>
        <button type="submit">➕ Add Task</button>
      </div>
    </form>
  );
}

export default TaskForm;
