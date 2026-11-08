export function formatClock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

/** "atualizado às 18h05" (hoje) ou "atualizado em 07/11 às 18h05". */
export function formatUpdated(iso: string | null, now: Date = new Date()): string {
  if (!iso) return 'sem episódio ainda';
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const time = mm === '00' ? `${hh}h` : `${hh}h${mm}`;
  if (d.toDateString() === now.toDateString()) return `atualizado às ${time}`;
  const dd = String(d.getDate()).padStart(2, '0');
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  return `atualizado em ${dd}/${mo} às ${time}`;
}

/** "publicada há 3 horas" */
export function formatAgo(iso: string | null, now: Date = new Date()): string {
  if (!iso) return '';
  const minutes = Math.max(0, Math.round((now.getTime() - new Date(iso).getTime()) / 60000));
  if (minutes < 1) return 'publicada agora';
  if (minutes < 60) return `publicada há ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `publicada há ${hours} ${hours === 1 ? 'hora' : 'horas'}`;
  const days = Math.round(hours / 24);
  return `publicada há ${days} ${days === 1 ? 'dia' : 'dias'}`;
}

/** Índice da fala que está tocando, pelo início de cada uma (inicio_s). */
export function currentLineIndex(starts: number[], time: number): number {
  let idx = -1;
  for (let i = 0; i < starts.length; i++) {
    if (starts[i] <= time + 0.05) idx = i;
    else break;
  }
  return idx;
}
