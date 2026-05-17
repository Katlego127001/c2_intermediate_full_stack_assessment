export function Empty({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-md border border-dashed border-[hsl(var(--border))] p-10 text-center">
      <p className="font-medium">{title}</p>
      {hint && <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">{hint}</p>}
    </div>
  );
}
