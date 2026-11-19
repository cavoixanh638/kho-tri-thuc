import type { Item } from './api';

export function itemNeedsRefresh(item: Item) {
  return !item.deleted && (
    [item.source_fetch, item.asset_storage, item.content_extract, item.classification_status].includes('pending')
    || item.assets.some((asset) => asset.status === 'pending')
  );
}
