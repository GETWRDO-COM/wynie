import Tasks from "@/components/Tasks";
import styles from "./Illustration3.module.sass";

import { tasks } from "@/mocks/tasks";

type Illustration3Props = {};

const Illustration3 = ({}: Illustration3Props) => (
    <div className={styles.illustration}>
        <Tasks className={styles.tasks} completed />
    </div>
);

export default Illustration3;
