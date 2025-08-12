import cn from "classnames";
import Icon from "@/components/Icon";
import useEventsStore from "@/store/useEventsStore";
import styles from "./Head.module.sass";

type HeadProps = {
    title: string;
    addButtonRef: React.RefObject<HTMLButtonElement>;
};

const Head = ({ title, addButtonRef }: HeadProps) => {
    const { isOpenActions, isNewTask, toggleNewTask, setActiveGroupId } =
        useEventsStore((state) => state);

    return (
        <div className={cn(styles.head, { [styles.hide]: isOpenActions })}>
            <div
                className={cn(styles.back, { [styles.hide]: isNewTask })}
                onClick={() => setActiveGroupId(null)}
            >
                <button className={styles.arrow}>
                    <Icon name="arrow-left" />
                </button>
                <span>{title}</span>
            </div>
            <button
                className={cn(styles.add, {
                    [styles.active]: isNewTask,
                })}
                onClick={toggleNewTask}
                ref={addButtonRef}
            >
                <Icon name="plus" />
                <div className={styles.tooltip}>
                    {isNewTask ? (
                        "Cancel"
                    ) : (
                        <div className={styles.line}>
                            Add new item <div className={styles.sign}>/</div>
                        </div>
                    )}
                </div>
            </button>
        </div>
    );
};

export default Head;
