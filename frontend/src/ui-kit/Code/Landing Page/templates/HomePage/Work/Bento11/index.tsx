import Image from "@/components/Image";
import Icon from "@/components/Icon";
import styles from "./Bento11.module.sass";

type BentoProps = {};

const Bento = ({}: BentoProps) => (
    <div className={styles.bento}>
        <div className={styles.socials}>
            <div className={styles.social}>
                <Icon name="check-circle" />
            </div>
            <div className={styles.social}>
                <Icon name="calendar" />
            </div>
            <div className={styles.social}>
                <Icon name="sun" />
            </div>
            <div className={styles.plus}>
                <div className={styles.inner}></div>
                <Image
                    className={styles.image}
                    src="/images/bento-11-plus.svg"
                    width={12}
                    height={12}
                    alt=""
                />
            </div>
            <div className={styles.social}>
                <Icon name="airpod" />
            </div>
            <div className={styles.social}>
                <Icon name="chart-lines" />
            </div>
            <div className={styles.social}>
                <Icon name="search" />
            </div>
        </div>
        <div className={styles.circles}>
            <div className={styles.circle}></div>
            <div className={styles.circle}></div>
        </div>
    </div>
);

export default Bento;
