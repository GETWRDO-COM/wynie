import { useEffect, useState } from "react";
import cn from "classnames";
import Icon from "@/components/Icon";
import useEventsStore from "@/store/useEventsStore";
import useTasksStore from "@/store/useTasksStore";
import IconSelection from "../IconSelection";
import Options from "../Options";
import Title from "./Title";
import styles from "./Group.module.sass";

type TasksType = {
    id: string;
    title: string;
    completed: boolean;
};

type ItemType = {
    id: string;
    title: string;
    icon: string;
    tasks: TasksType[];
    iconColor: string;
};

type GroupProps = {
    item: ItemType;
    index: number;
    onClick: () => void;
    iconSelectionDown?: boolean;
    activeGroupIcons: string;
    setActiveGroupIcons: (id: string) => void;
};

const Group = ({
    item,
    index,
    onClick,
    iconSelectionDown,
    activeGroupIcons,
    setActiveGroupIcons,
}: GroupProps) => {
    const [edit, setEdit] = useState(false);
    const [selectedIcon, setSelectedIcon] = useState(item.icon);
    const [selectedColor, setSelectedColor] = useState(item.iconColor);
    const [isFadingOut, setIsFadingOut] = useState(false);
    const [isFadingIn, setIsFadingIn] = useState(false);

    const {
        isOpenIcons,
        isNewGroup,
        activeGroupOptionsId,
        setActiveGroupOptionsId,
        toggleActiveGroupOptionsId,
    } = useEventsStore((state) => state);
    const {
        duplicateGroup,
        removeGroup,
        updateIconGroup,
        updateIconColorGroup,
    } = useTasksStore((state) => state);

    const options = [
        {
            title: "Duplicate",
            icon: "copy",
            onClick: () => {
                setIsFadingIn(true);
                duplicateGroup(item.id);
            },
        },
        {
            title: "Delete",
            icon: "trash",
            onClick: () => {
                setIsFadingOut(true);
                setTimeout(() => removeGroup(item.id), 150);
            },
        },
    ];

    useEffect(() => {
        if (isFadingOut) {
            const timer = setTimeout(() => {
                setIsFadingOut(false);
            }, 150);
            return () => clearTimeout(timer);
        }
        if (isFadingIn) {
            const timer = setTimeout(() => {
                setIsFadingIn(false);
            }, 150);
            return () => clearTimeout(timer);
        }
    }, [isFadingOut, isFadingIn]);

    const handleIconChange = (newIcon: string) => {
        setSelectedIcon(newIcon);
        updateIconGroup(item.id, newIcon);
    };

    const handleColorChange = (newColor: string) => {
        setSelectedColor(newColor);
        updateIconColorGroup(item.id, newColor);
    };

    const handleDragClick = () => {
        toggleActiveGroupOptionsId(item.id);
        setEdit(false);
    };

    return (
        <div
            className={cn(styles.group, {
                [styles.hide]: isOpenIcons || isNewGroup,
                [styles.active]: activeGroupIcons === item.id && !isNewGroup,
                [styles.showOptions]: activeGroupOptionsId === item.id,
                [styles.fadeOut]: isFadingOut,
                [styles.fadeIn]: isFadingIn,
            })}
        >
            <div className={styles.head}>
                <div
                    className={styles.main}
                    onClick={() => {
                        onClick();
                        setActiveGroupOptionsId(null);
                    }}
                ></div>
                <IconSelection
                    selectedIcon={selectedIcon}
                    setSelectedIcon={handleIconChange}
                    selectedColor={selectedColor}
                    setSelectedColor={handleColorChange}
                    down={iconSelectionDown}
                    activeGroupIcons={activeGroupIcons}
                    setActiveGroupIcons={setActiveGroupIcons}
                    groupId={item.id}
                    onClick={() => setEdit(false)}
                />
                <Title
                    className={styles.title}
                    groupId={item.id}
                    value={item.title}
                    edit={edit}
                    setEdit={setEdit}
                />
                <div className={styles.counter}>{item.tasks.length}</div>
                <div className={styles.drag} onClick={handleDragClick}>
                    <Icon name="drag" />
                </div>
                <Options
                    className={styles.options}
                    items={options}
                    index={index}
                    isActive={activeGroupOptionsId === item.id}
                />
            </div>
        </div>
    );
};

export default Group;
