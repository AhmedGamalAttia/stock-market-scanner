import Link from "next/link";

export default function NotFound() {
  return (
    <div className="panel p-10 text-center">
      <h1 className="text-2xl font-bold mb-2">الصفحة غير موجودة</h1>
      <p className="text-muted mb-4">السهم أو الصفحة اللى بتدور عليها مش موجودة.</p>
      <Link href="/" className="btn-primary">رجوع للرئيسية</Link>
    </div>
  );
}
