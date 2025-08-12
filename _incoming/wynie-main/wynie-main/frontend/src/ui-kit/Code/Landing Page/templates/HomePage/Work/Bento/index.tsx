import styles from "./Bento.module.sass";

type BentoProps = {
    title: string;
    content: string;
    number: number;
    children: React.ReactNode;
};

const Bento = ({ title, content, number, children }: BentoProps) => (
    <div className={styles.bento}>
        <div className={styles.inner}>
            <div className={styles.number}>
                <span>{number}</span>
            </div>
            <div className={styles.preview}>
                <div className={styles.illustration}>{children}</div>
            </div>
            <div className={styles.details}>
                <div className={styles.subtitle}>{title}</div>
                <div className={styles.content}>{content}</div>
            </div>
        </div>
    </div>
);

export default Bento;
