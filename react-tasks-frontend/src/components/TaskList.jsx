import TaskItem from "./TaskItem";

function TaskList({ tasks, onTaskUpdated, onTaskDeleted }) {
  return (
    <div className="task-list">
      {tasks.length === 0 ? (
        <p>No tasks yet. Add one above!</p>
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
