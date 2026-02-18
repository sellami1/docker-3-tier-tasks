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

  if (loading) return <div className="loading">Loading tasks...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="app">
      <header>
        <h1>Task Manager</h1>
      </header>
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
