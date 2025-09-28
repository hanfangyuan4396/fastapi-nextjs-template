export function Footer() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-center text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:text-left">
        <p>© {new Date().getFullYear()} Student Manager</p>
        <p>Powered by Next.js · FastAPI · shadcn/ui</p>
      </div>
    </footer>
  );
}
