import { useState } from "react";
import OutsideClickHandler from "react-outside-click-handler";
import TextareaAutosize from "react-textarea-autosize";
import { useHotkeys } from "react-hotkeys-hook";
import cn from "classnames";
import Icon from "@/components/Icon";
import useEventsStore from "@/store/useEventsStore";
import useTasksStore from "@/store/useTasksStore";
import IconSelection from "../IconSelection";
import styles from "./NewGroup.module.sass";

type NewGroupProps = {
    addButtonRef: React.RefObject<HTMLButtonElement>;
    setActiveGroupIcons: (id: string) => void;
};

const NewGroup = ({ addButtonRef, setActiveGroupIcons }: NewGroupProps) => {
    const { isNewGroup, openNewGroup, closeNewGroup } = useEventsStore(
        (state) => state
    );
    const { addNewGroup } = useTasksStore((state) => state);
    const [title, setTitle] = useState("");
    const [icon, setIcon] = useState("smile");
    const [color, setColor] = useState("#CBCBCB");

    useHotkeys("/", () => {
        setTitle("");
        setTimeout(() => openNewGroup(), 0);
    });

    const handleAdd = () => {
        if (title.trim() !== "") {
            addNewGroup(title, icon, color);
            setTitle("");
            closeNewGroup();
        }
    };

    const handleKeyDown = (e: any) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleAdd();
            setIcon("smile");
            setColor("#CBCBCB");
        }
    };

    const handleChange = (e: any) => {
        const newTitle = e.target.value;
        if (newTitle.length <= 70) {
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
        closeNewGroup();
        setIcon("smile");
        setColor("#CBCBCB");
    };

    return (
        isNewGroup && (
            <OutsideClickHandler onOutsideClick={handleOutsideClick}>
                <div className={styles.form}>
                    <IconSelection
                        selectedIcon={icon}
                        setSelectedIcon={setIcon}
                        selectedColor={color}
                        setSelectedColor={setColor}
                        activeGroupIcons="new-group"
                        setActiveGroupIcons={setActiveGroupIcons}
                        groupId="new-group"
                    />
                    <div className={styles.field}>
                        <TextareaAutosize
                            className={styles.input}
                            maxRows={5}
                            placeholder="List name...."
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

export default NewGroup;
