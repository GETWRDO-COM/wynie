import { useEffect, useRef, useState } from "react";
import cn from "classnames";
import useEventsStore from "@/store/useEventsStore";
import styles from "./Wrap.module.sass";

type WrapProps = {
    search?: string;
    counter: number;
    listRef: React.RefObject<HTMLDivElement>;
    isDragging: boolean;
    children: React.ReactNode;
};

const Wrap = ({
    search,
    counter,
    listRef,
    isDragging,
    children,
}: WrapProps) => {
    const { isNewGroup } = useEventsStore((state) => state);
    const [isScrolled, setIsScrolled] = useState(false);
    const [isStartScrolled, setIsStartScrolled] = useState(false);
    const [isScrolledToBottom, setIsScrolledToBottom] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleScroll = () => {
            if (containerRef.current) {
                const { scrollTop, scrollHeight, clientHeight } =
                    containerRef.current;
                if (listRef.current) {
                    const listElement = listRef.current;
                    const listHeight = parseFloat(
                        getComputedStyle(listElement).height
                    );
                    if (listHeight > clientHeight) {
                        setIsScrolled(true);
                    } else {
                        setIsScrolled(false);
                    }
                    if (listHeight > clientHeight && scrollTop > 1) {
                        setIsStartScrolled(true);
                    } else {
                        setIsStartScrolled(false);
                    }
                }
                setIsScrolledToBottom(
                    scrollTop + clientHeight >= scrollHeight - 1
                );
            }
        };

        const container = containerRef.current;
        if (container) {
            container.addEventListener("scroll", handleScroll);
        }

        handleScroll();

        return () => {
            if (container) {
                container.removeEventListener("scroll", handleScroll);
            }
        };
    }, [counter, isNewGroup, listRef, search]);

    return (
        <div
            className={cn(styles.outer, {
                [styles.mask]:
                    isStartScrolled &&
                    !isScrolledToBottom &&
                    !isNewGroup &&
                    !isDragging,
                [styles.maskDown]:
                    isScrolled &&
                    !isStartScrolled &&
                    // !isScrolledToBottom &&
                    !isNewGroup &&
                    !isDragging,
                [styles.maskUp]:
                    isScrolled && isScrolledToBottom && !isDragging,
            })}
        >
            <div
                className={cn(styles.wrap, {
                    [styles.hidden]: counter > 6,
                    [styles.scroll]: isScrolled,
                    [styles.noScroll]: isNewGroup,
                })}
                ref={containerRef}
            >
                {children}
            </div>
        </div>
    );
};

export default Wrap;
