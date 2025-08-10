import { useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import OutsideClickHandler from "react-outside-click-handler";
import TextareaAutosize from "react-textarea-autosize";
import cn from "classnames";
import Icon from "@/components/Icon";
import useEventsStore from "@/store/useEventsStore";
import useTasksStore from "@/store/useTasksStore";
import styles from "./NewTask.module.sass";

type NewTaskProps = {
    groupId: string;
    addButtonRef: React.RefObject<HTMLButtonElement>;
};

const NewTask = ({ groupId, addButtonRef }: NewTaskProps) => {
    const [title, setTitle] = useState("");
    const { isNewTask, openNewTask, closeNewTask } = useEventsStore(
        (state) => state
    );
    const { addNewTask } = useTasksStore((state) => state);

    useHotkeys("/", () => {
        setTitle("");
        setTimeout(() => openNewTask(), 0);
    });

    const handleAdd = () => {
        if (title.trim() !== "") {
            addNewTask(groupId, title);
            setTitle("");
            closeNewTask();
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleAdd();
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newTitle = e.target.value;
        if (newTitle.length <= 140) {
            setTitle(newTitle);
        }
    };

    const handleOutsideClick = (event: MouseEvent) => {
        if (
            addButtonRef.current &&
            addButtonRef.current.contains(event.target as Node)
        ) {
            return;
        }
        closeNewTask();
    };

    return (
        isNewTask && (
            <OutsideClickHandler onOutsideClick={handleOutsideClick}>
                <div className={styles.form}>
                    <div className={styles.radio}></div>
                    <div className={styles.field}>
                        <TextareaAutosize
                            className={styles.input}
                            maxRows={5}
                            placeholder="Task name...."
                            autoFocus
                            value={title}
                            onChange={handleChange}
                            onKeyDown={handleKeyDown}
                        />
                    </div>
                    <button
                        className={cn(styles.add, {
                            [styles.visible]: title !== "",
                        })}
                        onClick={handleAdd}
                    >
                        <Icon name="check-circle-fill" />
                    </button>
                </div>
            </OutsideClickHandler>
        )
    );
};

export default NewTask;
