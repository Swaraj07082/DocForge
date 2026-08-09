import { auth } from "@/auth";
import { AnalyseForm } from "@/app/components/AnalyseForm";
import { SignOutButton } from "@/app/components/SignOutButton";
import { redirect } from "next/navigation";
import styles from "./page.module.css";

export default async function HomePage() {
  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <div>
          <p className={styles.brand}>DocForge</p>
          <p className={styles.user}>
            Signed in as {session.user.email ?? session.user.name}
          </p>
        </div>
        <SignOutButton />
      </header>
      <p className={styles.lede}>
        Requests go through the Next.js BFF with your httpOnly session cookie.
        FastAPI only accepts a short-lived Bearer JWT minted server-side.
      </p>
      <AnalyseForm />
    </main>
  );
}
