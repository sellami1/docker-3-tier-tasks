import TaskItem from "./TaskItem";

function TaskList({ tasks, onTaskUpdated, onTaskDeleted }) {
  return (
    <div className="task-list">
      {tasks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <h3>No tasks yet</h3>
          <p>Add your first task above and start being productive!</p>
        </div>
      ) : (
        tasks.map((task) => (
          <TaskItem
            key={task._id}
            task={task}
            onUpdate={onTaskUpdated}
            onDelete={onTaskDeleted}
          />
        ))
      )}
    </div>
  );
}

export default TaskList;
