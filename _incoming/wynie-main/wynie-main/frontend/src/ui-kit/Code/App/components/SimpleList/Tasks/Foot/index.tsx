import { CircularProgressbar, buildStyles } from "react-circular-progressbar";
import cn from "classnames";
import useEventsStore from "@/store/useEventsStore";
import Actions from "../Actions";
import "react-circular-progressbar/dist/styles.css";
import styles from "./Foot.module.sass";

type TasksType = {
    id: string;
    title: string;
    completed: boolean;
};

type FootProps = {
    groupId: string;
    tasks: TasksType[];
    showCompleted: boolean;
    setShowCompleted: any;
    allTasksCompleted?: boolean;
};

const Foot = ({
    groupId,
    tasks,
    showCompleted,
    setShowCompleted,
    allTasksCompleted,
}: FootProps) => {
    const { isOpenActions, isNewTask } = useEventsStore((state) => state);

    const completedTaskCount = tasks.filter((task) => task.completed).length;

    const progress =
        tasks.length > 0 ? (completedTaskCount / tasks.length) * 100 : 0;

    return (
        tasks.length > 0 && (
            <div
                className={cn(styles.foot, {
                    [styles.hide]: isNewTask,
                })}
            >
                <div
                    className={cn(styles.status, {
                        [styles.hide]: isOpenActions,
                    })}
                >
                    <div className={styles.progress}>
                        {!showCompleted && allTasksCompleted ? (
                            <div className={styles.check}></div>
                        ) : (
                            <CircularProgressbar
                                value={progress}
                                strokeWidth={16}
                                styles={buildStyles({
                                    pathColor: "rgba(248,248,248,.7)",
                                    trailColor: "rgba(248,248,248,.05)",
                                })}
                            />
                        )}
                    </div>
                    <div className={styles.counter}>
                        completed:
                        <span>
                            {completedTaskCount}/{tasks.length}
                        </span>
                    </div>
                </div>
                <Actions
                    groupId={groupId}
                    showCompleted={showCompleted}
                    setShowCompleted={setShowCompleted}
                />
            </div>
        )
    );
};

export default Foot;
