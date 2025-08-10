import { default as NextImage } from "next/image";
import styles from "./NoResultSearch.module.sass";

type NoResultSearchProps = {
    search: string;
    isVisible: boolean;
};

const NoResultSearch = ({ search, isVisible }: NoResultSearchProps) => {
    return (
        isVisible && (
            <div className={styles.noResult}>
                <div className={styles.preview}>
                    <div className={styles.image}>
                        <NextImage
                            src="/images/oops.svg"
                            width={403}
                            height={575}
                            alt=""
                        />
                    </div>
                    <div className={styles.title}>OOPS</div>
                </div>
                <div className={styles.text}>
                    No result for “<span>{search}</span>”, try again.
                </div>
            </div>
        )
    );
};

export default NoResultSearch;
