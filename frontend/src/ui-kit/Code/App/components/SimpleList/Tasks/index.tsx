import { useState, useRef } from "react";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";
import cn from "classnames";
import useEventsStore from "@/store/useEventsStore";
import useTasksStore from "@/store/useTasksStore";
import Head from "./Head";
import Wrap from "./Wrap";
import Foot from "./Foot";
import Overlay from "./Overlay";
import Task from "./Task";
import NewTask from "./NewTask";
import Success from "./Success";
import EmptyTasks from "./EmptyTasks";
import CompletedTasks from "./CompletedTasks";
import styles from "./Tasks.module.sass";

type TasksType = {
    id: string;
    title: string;
    completed: boolean;
};

type ItemType = {
    id: string;
    title: string;
    icon: string;
    iconColor: string;
    showCompleted: boolean;
    tasks: TasksType[];
};

type TasksProps = {
    activeGroupId: string | null;
    item: ItemType;
};

const Tasks = ({ activeGroupId, item }: TasksProps) => {
    const { updateTaskOrder } = useTasksStore((state) => state);
    const { isNewTask, isOpenActions } = useEventsStore((state) => state);
    const [showCompleted, setShowCompleted] = useState(item.showCompleted);
    const [isDragging, setIsDragging] = useState(false);
    const addButtonRef = useRef<HTMLButtonElement>(null);

    const allTasksCompleted =
        item.tasks.length > 0 && item.tasks.every((task) => task.completed);

    const handleDragStart = () => {
        setIsDragging(true);
    };

    const handleDragEnd = (result: any) => {
        setIsDragging(false);
        const { source, destination } = result;
        if (!destination) return;

        updateTaskOrder(activeGroupId, source.index, destination.index);
    };

    return (
        <DragDropContext
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <div className={styles.tasks}>
                <Head title={item.title} addButtonRef={addButtonRef} />
                <Wrap
                    className={cn(styles.wrap, {
                        [styles.hide]: isNewTask || isOpenActions,
                    })}
                    counter={item.tasks.length}
                    isDragging={isDragging}
                >
                    {item.tasks.length > 0 && (
                        <Droppable droppableId={`droppable-${item.id}`}>
                            {(provided) => (
                                <div
                                    {...provided.droppableProps}
                                    ref={(el) => {
                                        provided.innerRef(el);
                                    }}
                                    className={styles.list}
                                >
                                    {(showCompleted
                                        ? item.tasks
                                        : item.tasks.filter(
                                              (task) => !task.completed
                                          )
                                    ).map((task, index) => (
                                        <Draggable
                                            key={task.id}
                                            draggableId={`draggable-${task.id}`}
                                            index={index}
                                        >
                                            {(provided) => (
                                                <div
                                                    className={styles.task}
                                                    ref={provided.innerRef}
                                                    {...provided.draggableProps}
                                                    {...provided.dragHandleProps}
                                                >
                                                    <Task
                                                        item={task}
                                                        index={index}
                                                        groupId={item.id}
                                                    />
                                                </div>
                                            )}
                                        </Draggable>
                                    ))}
                                    {provided.placeholder}
                                </div>
                            )}
                        </Droppable>
                    )}
                    <NewTask groupId={item.id} addButtonRef={addButtonRef} />
                </Wrap>
                <Foot
                    groupId={item.id}
                    tasks={item.tasks}
                    showCompleted={showCompleted}
                    setShowCompleted={setShowCompleted}
                    allTasksCompleted={allTasksCompleted}
                />
                <Success isActive={allTasksCompleted} />
                <EmptyTasks isVisible={item.tasks.length === 0 && !isNewTask} />
                <CompletedTasks
                    isVisible={
                        !isNewTask && !showCompleted && allTasksCompleted
                    }
                />
                <Overlay />
            </div>
        </DragDropContext>
    );
};

export default Tasks;
