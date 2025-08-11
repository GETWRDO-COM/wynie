import cn from "classnames";
import styles from "./Button.module.sass";

type ButtonProps = {
    className?: string;
    title: string;
    href?: any;
    props?: any;
};

const Button = ({ className, title, href, ...props }: ButtonProps) => {
    const CreatedTag = href ? "a" : "button";

    return (
        <CreatedTag
            className={cn(className, styles.button)}
            href={href}
            // target={href ? "_blank" : undefined}
            rel={href ? "noopener noreferrer" : undefined}
            {...props}
        >
            <span className={styles.title}>{title}</span>
            <span className={styles.circle}></span>
        </CreatedTag>
    );
};

export default Button;
