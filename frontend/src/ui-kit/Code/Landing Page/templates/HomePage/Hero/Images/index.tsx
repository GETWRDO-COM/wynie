import Groups from "@/components/Groups";
import Tasks from "@/components/Tasks";
import StarField from "@/components/StarField";
import styles from "./Images.module.sass";

import { groups1, groups2 } from "@/mocks/groups";
import { tasks } from "@/mocks/tasks";

type ImagesProps = {};

const Images = ({}: ImagesProps) => (
    <div className={styles.images}>
        <div className={styles.inner}>
            <div className={styles.row}>
                <Groups
                    className={styles.group}
                    items={groups1}
                    activeIconIndex={4}
                />
                <Groups
                    className={styles.group}
                    classDropdown={styles.dropdown}
                    items={groups2}
                    activeIconIndex={4}
                    newGroup
                />
            </div>
            <div className={styles.center}>
                <div className={styles.overlay}></div>
                <div className={styles.circle}></div>
                <Tasks className={styles.tasks} items={tasks} animation />
            </div>
        </div>
        <div className={styles.stars}>
            <StarField />
        </div>
    </div>
);

export default Images;
