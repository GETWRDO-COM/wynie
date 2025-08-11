import { useState, useRef, useEffect } from "react";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";
import cn from "classnames";
import Group from "./Group";
import NewGroup from "./NewGroup";
import Tasks from "./Tasks";
import useTasksStore from "@/store/useTasksStore";
import useEventsStore from "@/store/useEventsStore";
import Head from "./Head";
import Wrap from "./Wrap";
import Overlay from "./Overlay";
import EmptyList from "./EmptyList";
import NoResultSearch from "./NoResultSearch";
import styles from "./SimpleList.module.sass";

type SimpleListProps = {
    className?: string;
};

const SimpleList = ({ className }: SimpleListProps) => {
    const { tasks, updateGroupOrder } = useTasksStore((state) => state);
    const { isNewGroup, activeGroupId, setActiveGroupId, closeIcons } =
        useEventsStore((state) => state);
    const [search, setSearch] = useState("");
    const [minHeight, setMinHeight] = useState(472);
    const [activeGroupIcons, setActiveGroupIcons] = useState("");
    const [isDragging, setIsDragging] = useState(false);
    const simpleListRef = useRef<HTMLDivElement>(null);
    const addButtonRef = useRef<HTMLButtonElement>(null);
    const listRef = useRef<HTMLDivElement>(null);

    const filteredGroup = tasks.filter((group) =>
        group.title.toLowerCase().includes(search.toLowerCase())
    );

    function mergeRefs(...refs: any) {
        return (node: any) => {
            refs.forEach((ref: any) => {
                if (typeof ref === "function") {
                    ref(node);
                } else if (ref != null) {
                    ref.current = node;
                }
            });
        };
    }

    const handleDragStart = () => {
        setActiveGroupId(null);
        closeIcons();
        setIsDragging(true);
    };

    const handleDragEnd = (result: any) => {
        setIsDragging(false);
        setActiveGroupId(null);
        const { source, destination } = result;
        if (!destination) return;
        updateGroupOrder(source.index, destination.index);
    };

    useEffect(() => {
        const simpleListHeight =
            simpleListRef.current?.offsetHeight ?? minHeight;
        setMinHeight(
            simpleListHeight > minHeight ? simpleListHeight : minHeight
        );
    }, [minHeight]);

    useEffect(() => {
        if (search !== "") {
            const simpleListHeight =
                simpleListRef.current?.offsetHeight ?? minHeight;
            setMinHeight(
                simpleListHeight > minHeight ? simpleListHeight : minHeight
            );
        }
    }, [search, minHeight]);

    return (
        <DragDropContext
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <div
                className={cn(className, styles.simpleList)}
                ref={simpleListRef}
                style={{ minHeight }}
            >
                <div
                    className={cn(styles.wrap, {
                        [styles.hide]: activeGroupId !== null,
                    })}
                >
                    <Head
                        search={search}
                        setSearch={setSearch}
                        addButtonRef={addButtonRef}
                        counterGroup={tasks.length}
                    />
                    <Wrap
                        search={search}
                        counter={tasks.length}
                        listRef={listRef}
                        isDragging={isDragging}
                    >
                        <Droppable droppableId="droppable-groups">
                            {(provided) => (
                                <div
                                    className={styles.list}
                                    ref={mergeRefs(listRef, provided.innerRef)}
                                    {...provided.droppableProps}
                                >
                                    {filteredGroup.length > 0 &&
                                        filteredGroup.map((group, index) => (
                                            <Draggable
                                                key={group.id}
                                                draggableId={group.id}
                                                index={index}
                                            >
                                                {(provided) => (
                                                    <div
                                                        className={styles.group}
                                                        ref={provided.innerRef}
                                                        {...provided.draggableProps}
                                                        {...provided.dragHandleProps}
                                                    >
                                                        <Group
                                                            item={group}
                                                            index={index}
                                                            onClick={() =>
                                                                setActiveGroupId(
                                                                    isDragging
                                                                        ? null
                                                                        : group.id
                                                                )
                                                            }
                                                            iconSelectionDown={
                                                                index < 3
                                                            }
                                                            activeGroupIcons={
                                                                activeGroupIcons
                                                            }
                                                            setActiveGroupIcons={
                                                                setActiveGroupIcons
                                                            }
                                                        />
                                                    </div>
                                                )}
                                            </Draggable>
                                        ))}
                                    {provided.placeholder}
                                </div>
                            )}
                        </Droppable>
                        <NewGroup
                            addButtonRef={addButtonRef}
                            setActiveGroupIcons={setActiveGroupIcons}
                        />
                    </Wrap>
                    <NoResultSearch
                        isVisible={
                            !isNewGroup &&
                            filteredGroup.length === 0 &&
                            search !== ""
                        }
                        search={search}
                    />
                    <EmptyList />
                    <Overlay />
                </div>
                {filteredGroup
                    .filter((item) => item.id === activeGroupId)
                    .map((item) => (
                        <Tasks
                            item={item}
                            key={item.id}
                            activeGroupId={activeGroupId}
                        />
                    ))}
            </div>
        </DragDropContext>
    );
};

export default SimpleList;
