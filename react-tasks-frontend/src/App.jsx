import { useState, useEffect } from "react";
import TaskForm from "./components/TaskForm";
import TaskList from "./components/TaskList";
import api from "./api";
import "./App.css";

function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await api.get("/api/tasks");
      setTasks(response.data);
    } catch (err) {
      setError("Failed to load tasks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleTaskAdded = (newTask) => {
    setTasks([newTask, ...tasks]);
  };

  const handleTaskUpdated = (updatedTask) => {
    setTasks(tasks.map((t) => (t._id === updatedTask._id ? updatedTask : t)));
  };

  const handleTaskDeleted = (id) => {
    setTasks(tasks.filter((t) => t._id !== id));
  };

  const stats = {
    total: tasks.length,
    pending: tasks.filter(t => t.status === "pending").length,
    inProgress: tasks.filter(t => t.status === "in-progress").length,
    completed: tasks.filter(t => t.status === "completed").length,
  };

  if (loading) return <div className="loading">Loading tasks...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="app">
      <header>
        <h1>✨ Task Manager</h1>
        <p>Organize your work, achieve your goals</p>
      </header>
      
      <div className="stats-bar">
        <div className="stat-card">
          <span className="number">{stats.total}</span>
          <span className="label">Total</span>
        </div>
        <div className="stat-card">
          <span className="number">{stats.pending}</span>
          <span className="label">Pending</span>
        </div>
        <div className="stat-card">
          <span className="number">{stats.inProgress}</span>
          <span className="label">In Progress</span>
        </div>
        <div className="stat-card">
          <span className="number">{stats.completed}</span>
          <span className="label">Done</span>
        </div>
      </div>

      <main>
        <TaskForm onTaskAdded={handleTaskAdded} />
        <TaskList
          tasks={tasks}
          onTaskUpdated={handleTaskUpdated}
          onTaskDeleted={handleTaskDeleted}
        />
      </main>
    </div>
  );
}

export default App;
