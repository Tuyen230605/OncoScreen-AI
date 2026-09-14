/** BẮT BUỘC hiển thị trên mọi màn kết quả (S6). Nội dung lấy từ API (session.disclaimer). */
export function Disclaimer({ text }: { text: string }) {
  return (
    <aside role="note" className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
      <strong className="mr-1">Lưu ý quan trọng:</strong>
      {text}
    </aside>
  );
}
