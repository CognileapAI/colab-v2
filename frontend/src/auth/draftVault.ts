const drafts = new Map<string, unknown>();
const id = (accountId: string, key: string) => `${accountId}:\0${key}`;

export function saveDraft(accountId: string, key: string, value: unknown): void {
  drafts.set(id(accountId, key), value);
}
export function readDraft(accountId: string, key: string): unknown {
  return drafts.get(id(accountId, key));
}
export function deleteDraft(accountId: string, key: string): void {
  drafts.delete(id(accountId, key));
}
export function discardDrafts(accountId: string): void {
  const prefix = `${accountId}:\0`;
  for (const key of drafts.keys()) if (key.startsWith(prefix)) drafts.delete(key);
}
