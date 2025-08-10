import OutsideClickHandler from "react-outside-click-handler";
import cn from "classnames";
import Icon from "@/components/Icon";
import useEventsStore from "@/store/useEventsStore";
import useTasksStore from "@/store/useTasksStore";
import styles from "./Actions.module.sass";

type ActionsProps = {
    groupId: string;
    showCompleted: boolean;
    setShowCompleted: any;
};

const Actions = ({
    groupId,
    showCompleted,
    setShowCompleted,
}: ActionsProps) => {
    const { isOpenActions, toggleActions, closeActions, setActiveGroupId } =
        useEventsStore((state) => state);
    const { removeGroup, duplicateGroup, toggleShowCompleted, clearGroup } =
        useTasksStore((state) => state);

    const actions = [
        {
            title: "Delete list",
            onClick: () => {
                removeGroup(groupId);
                closeActions();
                setActiveGroupId(null);
            },
        },
        {
            title: "Duplicate",
            onClick: () => {
                duplicateGroup(groupId);
                closeActions();
                setActiveGroupId(null);
            },
        },
        {
            title: "Show completed",
            onClick: () => {
                setShowCompleted(!showCompleted);
                toggleShowCompleted(groupId);
            },
        },
        {
            title: "Clear all",
            onClick: () => {
                clearGroup(groupId);
                closeActions();
            },
        },
    ];

    return (
        <OutsideClickHandler onOutsideClick={closeActions}>
            <div
                className={cn(styles.actions, {
                    [styles.active]: isOpenActions,
                })}
            >
                <button className={styles.head} onClick={toggleActions}>
                    <span></span>
                    <span></span>
                    <span></span>
                    <Icon name="close" />
                </button>
                <div className={styles.body}>
                    {actions.map((action, index) => (
                        <button
                            className={styles.action}
                            key={index}
                            onClick={action.onClick}
                        >
                            {action.title}
                            {action.title === "Show completed" && (
                                <div
                                    className={cn(styles.toggle, {
                                        [styles.active]: showCompleted,
                                    })}
                                ></div>
                            )}
                        </button>
                    ))}
                </div>
            </div>
        </OutsideClickHandler>
    );
};

export default Actions;
