import { RoleGuard } from "@/components/RoleGuard";

export default function DoctorLayout({ children }: { children: React.ReactNode }) {
  return <RoleGuard role="doctor">{children}</RoleGuard>;
}
