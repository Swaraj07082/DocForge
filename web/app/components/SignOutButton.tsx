import { signOut } from "@/auth";
import styles from "./SignOutButton.module.css";

export function SignOutButton() {
  return (
    <form
      action={async () => {
        "use server";
        await signOut({ redirectTo: "/login" });
      }}
    >
      <button type="submit" className={styles.btn}>
        Sign out
      </button>
    </form>
  );
}
