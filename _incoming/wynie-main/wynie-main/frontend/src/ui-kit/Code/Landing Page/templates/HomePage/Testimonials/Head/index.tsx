import cn from "classnames";
import Label from "@/components/Label";
import Image from "@/components/Image";
import styles from "./Head.module.sass";

type HeadProps = {};

const Head = ({}: HeadProps) => (
    <div className={styles.head}>
        <div className={styles.illustrations}>
            <div className={styles.illustration}>
                <Image
                    className={styles.image}
                    src="/images/testimonials-illustration.svg"
                    width={368}
                    height={368}
                    alt=""
                />
                <div className={styles.keyboards}>
                    <Image
                        className={styles.image}
                        src="/images/testimonials-keyboard.svg"
                        width={148}
                        height={17}
                        alt=""
                    />
                </div>
            </div>
            <div className={styles.illustration}>
                <Image
                    className={styles.image}
                    src="/images/testimonials-dots.svg"
                    width={368}
                    height={368}
                    alt=""
                />
            </div>
        </div>
        <Label title="testimonialS" />
        <div className={cn("h2", styles.title)}>List. Organize. Conquer.</div>
        <div className={styles.info}>Used by seriously productive people.</div>
    </div>
);

export default Head;
