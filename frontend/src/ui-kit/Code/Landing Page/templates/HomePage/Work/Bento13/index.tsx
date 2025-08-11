import Image from "@/components/Image";
import styles from "./Bento13.module.sass";

type BentoProps = {};

const Bento = ({}: BentoProps) => (
    <div className={styles.bento}>
        <div className={styles.inner}>
            <div className={styles.preview}>
                <Image
                    className={styles.image}
                    src="/images/bento-13.svg"
                    width={524}
                    height={336}
                    alt=""
                />
            </div>
        </div>
    </div>
);

export default Bento;
