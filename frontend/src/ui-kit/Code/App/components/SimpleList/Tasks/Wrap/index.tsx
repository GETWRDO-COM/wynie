import { useEffect, useRef, useState } from "react";
import cn from "classnames";
import useEventsStore from "@/store/useEventsStore";
import styles from "./Wrap.module.sass";

type WrapProps = {
    className?: string;
    counter: number;
    isDragging: boolean;
    children: React.ReactNode;
};

const Wrap = ({ className, counter, isDragging, children }: WrapProps) => {
    const { isNewTask } = useEventsStore((state) => state);
    const [isScrolled, setIsScrolled] = useState(false);
    const [isStartScrolled, setIsStartScrolled] = useState(false);
    const [isScrolledToBottom, setIsScrolledToBottom] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleScroll = () => {
            if (containerRef.current) {
                const { scrollTop, scrollHeight, clientHeight } =
                    containerRef.current;
                setIsScrolled(scrollHeight > clientHeight);
                setIsScrolledToBottom(
                    scrollTop + clientHeight >= scrollHeight - 1
                );
                if (scrollHeight > clientHeight && scrollTop > 1) {
                    setIsStartScrolled(true);
                } else {
                    setIsStartScrolled(false);
                }
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
    }, [counter, isNewTask]);

    return (
        <div className={styles.outer1}>
            <div
                className={cn(className, styles.outer2, {
                    [styles.mask]:
                        isStartScrolled && !isScrolledToBottom && !isDragging,
                    [styles.maskDown]:
                        isScrolled && !isStartScrolled && !isDragging,
                    [styles.maskUp]:
                        isScrolled && isScrolledToBottom && !isDragging,
                })}
            >
                <div
                    className={cn(className, styles.wrap, {
                        [styles.noScroll]: isNewTask,
                    })}
                    ref={containerRef}
                >
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Wrap;
