import cn from "classnames";
import Icon from "@/components/Icon";
import useEventsStore from "@/store/useEventsStore";
import styles from "./Head.module.sass";

type HeadProps = {
    search: string;
    setSearch: any;
    addButtonRef: React.RefObject<HTMLButtonElement>;
    counterGroup: number;
};

const Head = ({ search, setSearch, addButtonRef, counterGroup }: HeadProps) => {
    const { isNewGroup, toggleNewGroup, isOpenIcons } = useEventsStore(
        (state) => state
    );

    const handleNewGroup = () => {
        toggleNewGroup();
        setSearch("");
    };

    return (
        <div className={cn(styles.head, { [styles.hide]: isOpenIcons })}>
            {counterGroup !== 0 && (
                <div
                    className={cn(styles.search, { [styles.hide]: isNewGroup })}
                >
                    <button className={styles.result}>
                        <Icon name="search" />
                    </button>
                    <input
                        className={styles.input}
                        type="text"
                        placeholder="Search list"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                    <button
                        className={cn(styles.clear, {
                            [styles.visible]: search !== "",
                        })}
                        onClick={() => setSearch("")}
                    >
                        <Icon name="close-small" />
                    </button>
                </div>
            )}
            <button
                className={cn(styles.add, {
                    [styles.active]: isNewGroup,
                })}
                onClick={handleNewGroup}
                ref={addButtonRef}
            >
                <Icon name="plus" />
                <div className={styles.tooltip}>
                    {isNewGroup ? (
                        "Cancel"
                    ) : (
                        <div className={styles.line}>
                            Add new list <div className={styles.sign}>/</div>
                        </div>
                    )}
                </div>
            </button>
        </div>
    );
};

export default Head;
