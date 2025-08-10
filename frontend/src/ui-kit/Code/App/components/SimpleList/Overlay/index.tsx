import cn from "classnames";
import useEventsStore from "@/store/useEventsStore";
import styles from "./Overlay.module.sass";

type OverlayProps = {};

const Overlay = ({}: OverlayProps) => {
    const { isOpenIcons, closeIcons, isNewGroup, closeNewGroup } =
        useEventsStore((state) => state);
    return (
        <div
            className={cn(styles.overlay, {
                [styles.visible]: isNewGroup || isOpenIcons,
            })}
            onClick={() => {
                closeNewGroup();
                closeIcons();
            }}
        ></div>
    );
};

export default Overlay;
