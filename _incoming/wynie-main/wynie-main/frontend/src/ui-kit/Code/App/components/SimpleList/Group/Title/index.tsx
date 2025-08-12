import { useEffect, useRef, useState } from "react";
import cn from "classnames";
import TextareaAutosize from "react-textarea-autosize";
import useTasksStore from "@/store/useTasksStore";
import useEventsStore from "@/store/useEventsStore";
import styles from "./Title.module.sass";

type TitleProps = {
    className?: string;
    groupId: string;
    value: string;
    edit: boolean;
    setEdit: (edit: boolean) => void;
};

const Title = ({ className, groupId, value, edit, setEdit }: TitleProps) => {
    const { updateTitleGroup } = useTasksStore((state) => state);
    const { setActiveGroupOptionsId } = useEventsStore((state) => state);
    const [title, setTitle] = useState(value);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleTitleChange = (e: any) => {
        const newTitle = e.target.value;
        if (newTitle.length <= 60) {
            setTitle(newTitle);
        }
    };

    const handleTitleKeyDown = (e: any) => {
        if (e.key === "Enter") {
            e.preventDefault();
            updateTitleGroup(groupId, title);
            setEdit(false);
        }
    };

    const handleBlur = () => {
        updateTitleGroup(groupId, title);
        setEdit(false);
    };

    const focusTextareaAtEnd = () => {
        if (textareaRef.current) {
            const len = textareaRef.current.value.length;
            textareaRef.current.setSelectionRange(len, len);
            textareaRef.current.focus();
        }
    };

    useEffect(() => {
        if (edit) {
            focusTextareaAtEnd();
        }
    }, [edit]);

    return edit ? (
        <TextareaAutosize
            className={styles.input}
            maxRows={5}
            autoFocus
            value={title}
            onChange={handleTitleChange}
            onKeyDown={handleTitleKeyDown}
            onBlur={handleBlur}
            ref={textareaRef}
        />
    ) : (
        <div
            className={cn(className, styles.title)}
            onClick={() => {
                setEdit(true);
                setActiveGroupOptionsId(null);
            }}
        >
            {value}
        </div>
    );
};

export default Title;
