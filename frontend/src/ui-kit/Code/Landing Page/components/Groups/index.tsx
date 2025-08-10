import cn from "classnames";
import Icon from "@/components/Icon";
import Image from "@/components/Image";
import styles from "./Groups.module.sass";

const icons = [
    "smile",
    "home",
    "car",
    "fire",
    "favorite",
    "eye",
    "add-user",
    "web3",
    "memory",
    "quotes",
    "heart",
    "image",
    "location",
    "star",
];

const colors = [
    "#CBCBCB",
    "#FF7474",
    "#FFA502",
    "#FFFA65",
    "#2ECC71",
    "#DEB4F6",
    "#B4AAFF",
];

type GroupsProps = {
    className?: string;
    classField?: string;
    classDropdown?: string;
    classList?: string;
    items: {
        id: string;
        title: string;
        counter: number;
        icon: string;
        isHover: boolean;
    }[];
    newGroup?: boolean;
    activeIconIndex: number;
};

const Groups = ({
    className,
    classField,
    classDropdown,
    classList,
    items,
    newGroup,
    activeIconIndex,
}: GroupsProps) => (
    <div className={cn(className, styles.groups)}>
        <div className={styles.inner}>
            <div className={cn(styles.head, { [styles.hide]: newGroup })}>
                <div className={styles.search}>
                    <Icon name="search" />
                    Search list...
                </div>
                <div className={styles.add}>
                    <Icon name="plus" />
                </div>
            </div>
            <div
                className={cn(classList, styles.list, {
                    [styles.hide]: newGroup,
                })}
            >
                {items.map((group) => (
                    <div
                        className={cn(styles.group, {
                            [styles.hover]: group.isHover,
                        })}
                        key={group.id}
                    >
                        <div className={styles.icon}>
                            <Icon name={group.icon} />
                        </div>
                        <div className={styles.title}>{group.title}</div>
                        <div className={styles.counter}>{group.counter}</div>
                        {group.isHover && (
                            <div className={styles.cursor}>
                                <Image
                                    src="/images/cursor.svg"
                                    width={17}
                                    height={17}
                                    alt=""
                                />
                                <div className={styles.tooltip}>Totoro</div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
            {newGroup && (
                <div className={styles.new}>
                    <div className={cn(classField, styles.field)}>
                        <div className={styles.icon}>
                            <Icon name="smile" />
                        </div>
                        <div className={styles.subtitle}>List name....</div>
                    </div>
                    <div className={cn(classDropdown, styles.dropdown)}>
                        <div className={styles.box}>
                            <div className={styles.category}>Icon</div>
                            <div className={styles.wrap}>
                                {icons.map((icon, index) => (
                                    <div
                                        className={cn(styles.icon, {
                                            [styles.active]:
                                                index === activeIconIndex,
                                        })}
                                        key={index}
                                    >
                                        <Icon name={icon} />
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className={styles.box}>
                            <div className={styles.category}>Color</div>
                            <div className={styles.wrap}>
                                {colors.map((color, index) => (
                                    <div
                                        className={cn(styles.color, {
                                            [styles.active]: index === 0,
                                        })}
                                        key={index}
                                        style={{ backgroundColor: color }}
                                    ></div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    </div>
);

export default Groups;
