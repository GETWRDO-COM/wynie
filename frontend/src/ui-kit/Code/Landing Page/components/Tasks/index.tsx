import cn from "classnames";
import Icon from "@/components/Icon";
import Image from "@/components/Image";
import CompletedTasks from "@/components/CompletedTasks";
import styles from "./Tasks.module.sass";

type TasksProps = {
    className?: string;
    classTooltip?: string;
    titleTooltip?: string;
    classFoot?: string;
    items?: {
        id: string;
        title: string;
        isActions: boolean;
        isHover: boolean;
        isSelected: boolean;
    }[];
    animation?: boolean;
    completed?: boolean;
};

const Tasks = ({
    className,
    classTooltip,
    titleTooltip,
    classFoot,
    items,
    animation,
    completed,
}: TasksProps) => (
    <div
        className={cn(className, styles.tasks, {
            [styles.animation]: animation,
            [styles.completed]: completed,
        })}
    >
        <div className={styles.inner}>
            <div className={styles.head}>
                <div className={styles.back}>
                    <div className={styles.icon}>
                        <Icon name="arrow-left" />
                    </div>
                    {completed ? "Simple list" : "Upcoming"}
                </div>
                <div className={styles.icon}>
                    <Icon name="plus" />
                </div>
            </div>
            {!completed ? (
                <div className={styles.body}>
                    {items?.map((item) => (
                        <div
                            className={cn(styles.task, {
                                [styles.isActions]: item.isActions,
                                [styles.isSelected]: item.isSelected,
                                [styles.isHover]: item.isHover,
                            })}
                            key={item.id}
                        >
                            <div className={styles.in}>
                                <div className={styles.radio}></div>
                                <div className={styles.title}>{item.title}</div>
                                {item.isActions && (
                                    <div className={styles.actions}>
                                        <div className={styles.action}>
                                            <Icon name="trash" />
                                        </div>
                                        <div className={styles.action}>
                                            <Icon name="copy" />
                                        </div>
                                    </div>
                                )}
                                <div className={styles.drag}>
                                    <Icon name="drag" />
                                </div>
                                {!item.isActions && item.isHover && (
                                    <div className={styles.cursor}>
                                        <Image
                                            src="/images/cursor-1.svg"
                                            width={17}
                                            height={17}
                                            alt=""
                                        />
                                        <div
                                            className={cn(
                                                classTooltip,
                                                styles.tooltip
                                            )}
                                        >
                                            {titleTooltip || "Kohaku"}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className={styles.wrap}>
                    <CompletedTasks
                        classPreview={styles.previewCompletedTasks}
                    />
                </div>
            )}
            <div className={cn(classFoot, styles.foot)}>
                <div className={styles.progress}>
                    <div className={styles.circle}>
                        <Image
                            className={styles.image}
                            src={
                                completed
                                    ? "/images/check-circle.svg"
                                    : "/images/circle-progress.svg"
                            }
                            width={32}
                            height={32}
                            alt=""
                        />
                    </div>
                    <div className={styles.result}>
                        completed<span>{completed ? "8/8" : "1/5"}</span>
                    </div>
                </div>
                <div className={styles.icon}>
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    </div>
);

export default Tasks;
