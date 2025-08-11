import Image from "@/components/Image";
import Button from "@/components/Button";
import styles from "./Item.module.sass";

type ItemProps = {
    activeIndex?: number;
    item: {
        id: string;
        title: string;
        priceMonthly: number;
        priceAnnually: number;
        image: string;
        description: string;
        options: Array<string>;
    };
    index: number;
};

const Item = ({ activeIndex, item, index }: ItemProps) => (
    <div className={styles.item}>
        {index === 1 && (
            <div className={styles.gradient}>
                <Image src="/images/gradient-pricing.png" fill alt="" />
            </div>
        )}
        <div className={styles.inner}>
            <div className={styles.head}>
                <div className={styles.preview}>
                    <Image src={item.image} width={128} height={128} alt="" />
                </div>
                <div className={styles.title}>{item.title}</div>
                <div className={styles.price}>
                    $
                    {activeIndex === 0 ? item.priceAnnually : item.priceMonthly}
                     per member / {activeIndex === 0 ? "year" : "month"}
                </div>
                <div className={styles.duration}>
                    {activeIndex === 0 ? "billed yearly" : "billed monthly"}
                </div>
                <Button className={styles.button} title="Get started" />
            </div>
            <div className={styles.body}>
                <div className={styles.info}>{item.description}</div>
                <div className={styles.list}>
                    {item.options.map((option, index) => (
                        <div className={styles.option} key={index}>
                            {option}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    </div>
);

export default Item;
