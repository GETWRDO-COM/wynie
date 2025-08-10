import { useState } from "react";
import cn from "classnames";
import Label from "@/components/Label";
import Item from "./Item";
import Rating from "./Rating";
import styles from "./Pricing.module.sass";

import { pricing } from "@/mocks/pricing";

type PricingProps = {};

const Pricing = ({}: PricingProps) => {
    const [activeIndex, setActiveIndex] = useState(0);
    const tabs = ["Billed annually", "Billed monthly"];

    return (
        <div className={cn("section", styles.pricing)}>
            <div className={cn("container", styles.container)}>
                <div className={styles.head}>
                    <Label title="pricing" />
                    <div className={cn("h2", styles.title)}>
                        Choose your simplicity level
                    </div>
                    <div className={styles.info}>
                        Every journey begins with a list. Choose your SimpleList
                        plan and watch your efficiency soar!
                    </div>
                    <div
                        className={cn(styles.tabs, {
                            [styles.active]: activeIndex === 1,
                        })}
                    >
                        {tabs.map((tab, index) => (
                            <button
                                className={cn(styles.tab, {
                                    [styles.active]: activeIndex === index,
                                })}
                                key={index}
                                onClick={() => setActiveIndex(index)}
                            >
                                {tab}
                            </button>
                        ))}
                    </div>
                </div>
                <div className={styles.list}>
                    {pricing.map((item, index) => (
                        <Item
                            item={item}
                            key={item.id}
                            index={index}
                            activeIndex={activeIndex}
                        />
                    ))}
                </div>
                <div className={styles.foot}>
                    <Rating />
                </div>
            </div>
        </div>
    );
};

export default Pricing;
