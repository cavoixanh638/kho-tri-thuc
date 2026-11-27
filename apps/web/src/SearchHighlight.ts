export type SearchHighlightPart={text:string;match:boolean};
const words=()=>/[\p{L}\p{N}][\p{L}\p{M}\p{N}]*/gu;
const normalize=(word:string)=>word.normalize('NFD').toLocaleLowerCase('vi').replace(/\p{M}/gu,'').replace(/đ/g,'d');

/** Match visible lexical tokens only. Preserve every original character and
 * return text fragments (never HTML); fuzzy/semantic matches without a visible
 * exact token intentionally receive no artificial highlight. */
export function highlightSearch(text:string,query:string):SearchHighlightPart[]{
  const tokens=new Set([...query.matchAll(words())].map(row=>normalize(row[0])));
  const parts:SearchHighlightPart[]=[];
  let cursor=0;
  if(tokens.size)for(const row of text.matchAll(words())){
    if(!tokens.has(normalize(row[0])))continue;
    const start=row.index??0;
    if(start>cursor)parts.push({text:text.slice(cursor,start),match:false});
    parts.push({text:row[0],match:true});
    cursor=start+row[0].length;
  }
  if(cursor<text.length||!parts.length)parts.push({text:text.slice(cursor),match:false});
  return parts;
}
