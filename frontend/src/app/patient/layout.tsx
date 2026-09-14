import { RoleGuard } from "@/components/RoleGuard";

export default function PatientLayout({ children }: { children: React.ReactNode }) {
  return <RoleGuard role="patient">{children}</RoleGuard>;
}
