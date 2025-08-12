import { useState } from "react";
import cn from "classnames";
import { SlideDown } from "react-slidedown";
import styles from "./Item.module.sass";
import "react-slidedown/lib/slidedown.css";

type ItemProps = {
    item: {
        id: string;
        title: string;
        content: string;
    };
};

const Item = ({ item }: ItemProps) => {
    const [open, setOpen] = useState<boolean>(false);

    return (
        <div className={cn(styles.item, { [styles.open]: open })}>
            <div className={styles.head} onClick={() => setOpen(!open)}>
                <div className={styles.title}>{item.title}</div>
                <div className={styles.plus}>
                    <span></span>
                    <span></span>
                </div>
            </div>
            <div className={cn(styles.body, { [styles.open]: open })}>
                <SlideDown className={styles.body}>
                    {open ? item.content : null}
                </SlideDown>
            </div>
        </div>
    );
};

export default Item;
