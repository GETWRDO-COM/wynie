import Image from "@/components/Image";
import styles from "./Rating.module.sass";

type RatingProps = {};

const Rating = ({}: RatingProps) => (
    <div className={styles.rating}>
        <div className={styles.stars}>
            <div className={styles.star}>
                <Image src="/images/star.svg" width={24} height={24} alt="" />
            </div>
            <div className={styles.star}>
                <Image src="/images/star.svg" width={24} height={24} alt="" />
            </div>
            <div className={styles.star}>
                <Image src="/images/star.svg" width={24} height={24} alt="" />
            </div>
            <div className={styles.star}>
                <Image src="/images/star.svg" width={24} height={24} alt="" />
            </div>
            <div className={styles.star}>
                <Image src="/images/star.svg" width={24} height={24} alt="" />
            </div>
        </div>
        <div className={styles.row}>
            <div className={styles.text}>
                <span>50K reviews</span> on Appstore
            </div>
            <div className={styles.logo}>
                <Image
                    src="/images/app-store.svg"
                    width={24}
                    height={24}
                    alt=""
                />
            </div>
        </div>
    </div>
);

export default Rating;
