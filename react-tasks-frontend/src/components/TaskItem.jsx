import { useState } from "react";
import { FaEdit, FaTrash, FaCheck } from "react-icons/fa";
import api from "../api";

function TaskItem({ task, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description);
  const [status, setStatus] = useState(task.status);

  const handleUpdate = async () => {
    try {
      const response = await api.put(`/api/tasks/${task._id}`, {
        title,
        description,
        status,
      });
      onUpdate(response.data);
      setIsEditing(false);
    } catch (err) {
      alert("Failed to update");
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Delete this task?")) return;
    try {
      await api.delete(`/api/tasks/${task._id}`);
      onDelete(task._id);
    } catch (err) {
      alert("Failed to delete");
    }
  };

  const toggleComplete = async () => {
    const newStatus = status === "completed" ? "pending" : "completed";
    try {
      const response = await api.put(`/api/tasks/${task._id}`, {
        status: newStatus,
      });
      onUpdate(response.data);
    } catch (err) {
      alert("Failed to update status");
    }
  };

  if (isEditing) {
    return (
      <div className="task-item editing">
        <input 
          value={title} 
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task title"
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description"
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="pending">⏳ Pending</option>
          <option value="in-progress">🔥 In Progress</option>
          <option value="completed">✅ Completed</option>
        </select>
        <div className="edit-actions">
          <button className="save-btn" onClick={handleUpdate}>💾 Save</button>
          <button className="cancel-btn" onClick={() => setIsEditing(false)}>❌ Cancel</button>
        </div>
      </div>
    );
  }

  const statusLabels = {
    pending: "⏳ Pending",
    "in-progress": "🔥 In Progress",
    completed: "✅ Completed"
  };

  return (
    <div className={`task-item ${task.status}`}>
      <div className="task-content">
        <h3>{task.title}</h3>
        <p>{task.description}</p>
        <span className={`status-badge ${task.status}`}>
          {statusLabels[task.status]}
        </span>
      </div>
      <div className="actions">
        <button className="edit" onClick={() => setIsEditing(true)} title="Edit">
          <FaEdit />
        </button>
        <button className="complete" onClick={toggleComplete} title="Toggle Complete">
          <FaCheck />
        </button>
        <button className="delete" onClick={handleDelete} title="Delete">
          <FaTrash />
        </button>
      </div>
    </div>
  );
}

export default TaskItem;
