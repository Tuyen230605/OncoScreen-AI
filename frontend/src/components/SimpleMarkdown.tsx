import { Fragment, type ReactNode } from "react";

type Block = { kind: "heading"; level: number; text: string } | { kind: "paragraph"; lines: string[] };

/** `**đậm**` → <strong>; phần còn lại là chữ thường (React tự escape, không dùng innerHTML). */
function inline(text: string, key: string): ReactNode[] {
  return text
    .split(/(\*\*[^*\n]+\*\*)/g)
    .filter(Boolean)
    .map((part, i) =>
      part.length > 4 && part.startsWith("**") && part.endsWith("**") ? (
        <strong key={`${key}-${i}`} className="font-semibold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      ) : (
        <Fragment key={`${key}-${i}`}>{part}</Fragment>
      ),
    );
}

function parse(source: string): Block[] {
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  const flush = () => {
    if (paragraph.length) blocks.push({ kind: "paragraph", lines: paragraph });
    paragraph = [];
  };
  for (const raw of source.replace(/\r\n?/g, "\n").split("\n")) {
    const line = raw.trim();
    const heading = /^(#{1,6})\s+(.+)$/.exec(line);
    if (!line) {
      flush();
    } else if (heading) {
      flush();
      blocks.push({ kind: "heading", level: heading[1].length, text: heading[2] });
    } else {
      paragraph.push(line);
    }
  }
  flush();
  return blocks;
}

/**
 * Markdown tối giản cho nội dung giáo dục từ API (`EducationContent.body_md`): chỉ tiêu đề (`#`), chữ đậm (`**…**`)
 * và đoạn văn (giữ xuống dòng). Ký hiệu khác hiển thị nguyên văn; không render HTML từ dữ liệu.
 */
export function SimpleMarkdown({ source }: { source: string }) {
  return (
    <div className="space-y-3">
      {parse(source).map((block, i) =>
        block.kind === "heading" ? (
          block.level <= 3 ? (
            <h3 key={i} className="pt-2 text-base font-semibold text-slate-900">
              {inline(block.text, `h${i}`)}
            </h3>
          ) : (
            <h4 key={i} className="pt-1 text-sm font-semibold text-slate-900">
              {inline(block.text, `h${i}`)}
            </h4>
          )
        ) : (
          <p key={i} className="max-w-prose whitespace-pre-line text-base leading-relaxed text-slate-700">
            {block.lines.map((line, j) => (
              <Fragment key={j}>
                {j > 0 && "\n"}
                {inline(line, `p${i}-${j}`)}
              </Fragment>
            ))}
          </p>
        ),
      )}
    </div>
  );
}
