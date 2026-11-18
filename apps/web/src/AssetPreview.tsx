import { useState } from 'react';

type PreviewAsset = { asset_id: string; mime: string; status: string };

export function AssetPreview({ assets }: { assets: PreviewAsset[] }) {
  const asset = assets.find((entry) => entry.status === 'verified'
    && (entry.mime.startsWith('image/') || entry.mime.startsWith('video/') || entry.mime === 'application/pdf'));
  const [failedAsset, setFailedAsset] = useState<string>();
  if (!asset || failedAsset === asset.asset_id) return null;
  return <img className="asset-thumbnail" alt="" loading="lazy" decoding="async"
    src={`/api/v1/assets/${encodeURIComponent(asset.asset_id)}/thumbnail`}
    onError={() => setFailedAsset(asset.asset_id)} />;
}
