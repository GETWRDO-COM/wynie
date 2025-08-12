import cn from "classnames";
import styles from "./Label.module.sass";

type LabelProps = {
    className?: string;
    title: string;
    href?: any;
    props?: any;
};

const Label = ({ className, title }: LabelProps) => {
    return (
        <div className={cn(className, styles.label)}>
            <span className={styles.title}>{title}</span>
            <span className={styles.circle}></span>
        </div>
    );
};

export default Label;
