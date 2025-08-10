import { Parallax } from "react-scroll-parallax";
import Groups from "@/components/Groups";
import Image from "@/components/Image";
import styles from "./Illustration1.module.sass";

import { groups1 } from "@/mocks/groups";

const items = [
    {
        title: "Brand your list",
        image: "/images/draft.svg",
        translate: ["30px", "-60px"],
    },
    {
        title: "Minimal icons",
        image: "/images/calculator.svg",
        translate: ["-50px", "30px"],
    },
    {
        title: "Unlimited list creation",
        image: "/images/numbers.svg",
        translate: ["20px", "-20px"],
    },
];

type Illustration1Props = {};

const Illustration1 = ({}: Illustration1Props) => (
    <div className={styles.illustration}>
        <Groups
            className={styles.groups}
            classDropdown={styles.dropdown}
            classField={styles.field}
            classList={styles.list}
            items={groups1}
            activeIconIndex={0}
            newGroup
        />
        <div className="">
            {items.map((item: any, index) => (
                <Parallax
                    className={styles.item}
                    key={index}
                    translateX={item.translate}
                >
                    <div className={styles.icon}>
                        <Image
                            className={styles.image}
                            src={item.image}
                            width={24}
                            height={24}
                            alt=""
                        />
                    </div>
                    <div className={styles.title}>{item.title}</div>
                </Parallax>
            ))}
        </div>
    </div>
);

export default Illustration1;
