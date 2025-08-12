import IllustrationEmptyList from "../../IllustrationEmptyList";
import styles from "./EmptyTasks.module.sass";

type EmptyTasksProps = {
    isVisible?: boolean;
};

const EmptyTasks = ({ isVisible }: EmptyTasksProps) => {
    return (
        isVisible && (
            <div className={styles.emptyList}>
                <IllustrationEmptyList
                    className={styles.illustration}
                    emptyTasks
                />
                <div className={styles.text}>
                    This list is lonely. Add some items.
                </div>
            </div>
        )
    );
};

export default EmptyTasks;
