export default function PageContainer({ children }: { children: React.ReactNode }) {
  return <main className="flex-1 p-6 overflow-auto">{children}</main>;
}
