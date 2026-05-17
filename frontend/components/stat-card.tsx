import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  accent?: "primary" | "success" | "warning" | "danger" | "info";
}) {
  const colors: Record<string, string> = {
    primary: "text-[hsl(var(--primary))]",
    success: "text-emerald-500",
    warning: "text-amber-500",
    danger: "text-red-500",
    info: "text-sky-500",
  };
  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-3 pt-5">
        <div>
          <p className="text-xs uppercase tracking-wider text-[hsl(var(--muted-foreground))]">{label}</p>
          <p className="mt-1 text-2xl font-semibold">{value}</p>
        </div>
        {icon && <div className={cn("text-3xl", accent && colors[accent])}>{icon}</div>}
      </CardContent>
    </Card>
  );
}
