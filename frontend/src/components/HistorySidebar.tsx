import type { HistoryItem } from "../types";
import { stagger } from "./stagger";
import { scoreBand } from "./ScoreRing";

interface HistorySidebarProps {
  items: HistoryItem[];
  activeId: number | null;
  error: string | null;
  onSelect: (id: number) => void;
}

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

export function HistorySidebar({ items, activeId, error, onSelect }: HistorySidebarProps) {
  return (
    <aside className="sidebar">
      <nav aria-labelledby="history-title">
        <h2 id="history-title" className="sidebar__title">
          History
          {items.length > 0 && <span className="count">{items.length}</span>}
        </h2>
        {error && <p className="muted">{error}</p>}
        {!error && items.length === 0 && <p className="muted">Your past analyses will appear here.</p>}
        <ul className="history">
          {items.map((item, index) => (
            <li key={item.id} style={stagger(index)}>
              <button
                type="button"
                className="history__item"
                onClick={() => onSelect(item.id)}
                aria-current={item.id === activeId ? "true" : undefined}
              >
                <span className="history__role">{item.role_title}</span>
                <span className="history__meta">
                  <span className={`badge badge--${scoreBand(item.match_score).tone}`}>
                    {item.match_score}
                    <span className="visually-hidden"> percent match</span>
                  </span>
                  <time dateTime={item.created_at}>{dateFormat.format(new Date(item.created_at))}</time>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
