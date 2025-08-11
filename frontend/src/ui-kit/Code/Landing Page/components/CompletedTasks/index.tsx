import cn from "classnames";
import Image from "@/components/Image";
import styles from "./CompletedTasks.module.sass";

type CompletedTasksProps = {
    classPreview?: string;
};

const CompletedTasks = ({ classPreview }: CompletedTasksProps) => {
    return (
        <div className={styles.completedTasks}>
            <div className={styles.illustration}>
                <div className={styles.circles}>
                    <div className={styles.circle}></div>
                    <div className={styles.circle}></div>
                </div>
                <div className={styles.box}></div>
                <div className={cn(classPreview, styles.preview)}>
                    <Image
                        className={styles.image}
                        src="/images/completed-tasks.svg"
                        width={414}
                        height={390}
                        alt=""
                    />
                </div>
            </div>
        </div>
    );
};

export default CompletedTasks;
