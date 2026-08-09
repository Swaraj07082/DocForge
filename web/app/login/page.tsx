import { auth, signIn } from "@/auth";
import { redirect } from "next/navigation";
import styles from "./login.module.css";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const session = await auth();
  if (session?.user) {
    redirect("/");
  }

  const params = await searchParams;
  const error = params.error;

  return (
    <main className={styles.page}>
      <div className={styles.panel}>
        <p className={styles.brand}>DocForge</p>
        <h1 className={styles.title}>Sign in to review code</h1>
        <p className={styles.sub}>
          Google OAuth via Auth.js. Session stays in an httpOnly JWT cookie —
          your browser never holds an API token.
        </p>

        {error ? (
          <p className={styles.error} role="alert">
            Sign-in failed ({error}). Check Google OAuth credentials and
            authorized redirect URIs.
          </p>
        ) : null}

        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/" });
          }}
        >
          <button type="submit" className={styles.googleBtn}>
            Continue with Google
          </button>
        </form>
      </div>
    </main>
  );
}
