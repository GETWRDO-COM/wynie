import cn from "classnames";
import useEventsStore from "@/store/useEventsStore";
import IllustrationEmptyList from "../../IllustrationEmptyList";
import styles from "./CompletedTasks.module.sass";

type CompletedTasksProps = {
    isVisible?: boolean;
};

const CompletedTasks = ({ isVisible }: CompletedTasksProps) => {
    const { isOpenActions } = useEventsStore((state) => state);
    return (
        isVisible && (
            <div
                className={cn(styles.completedTasks, {
                    [styles.hide]: isOpenActions,
                })}
            >
                <IllustrationEmptyList
                    className={styles.illustration}
                    completedTasks
                />
                <div className={styles.text}>You have completed all items!</div>
            </div>
        )
    );
};

export default CompletedTasks;
