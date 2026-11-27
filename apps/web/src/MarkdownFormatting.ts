/** Presentation edits on a textarea selection; preserve exact raw line endings and Unicode. */
export type FormatAction='bold'|'italic'|'strike'|'code'|'link'|'h1'|'h2'|'h3'|'bullet'|'number'|'quote'|'task'|'divider'|'fence'|'table';
export type FormatResult={raw:string;start:number;end:number};
export const markdownActions:{id:FormatAction;label:string;symbol:string;block?:boolean}[]=[
 {id:'bold',label:'In đậm',symbol:'B'},{id:'italic',label:'In nghiêng',symbol:'I'},{id:'strike',label:'Gạch ngang',symbol:'S'},
 {id:'code',label:'Mã nội dòng',symbol:'</>'},{id:'link',label:'Chèn liên kết',symbol:'🔗'},
 {id:'h1',label:'Tiêu đề H1',symbol:'H1'},{id:'h2',label:'Tiêu đề H2',symbol:'H2'},{id:'h3',label:'Tiêu đề H3',symbol:'H3'},
 {id:'bullet',label:'Danh sách chấm',symbol:'•'},{id:'number',label:'Danh sách số',symbol:'1.'},
 {id:'quote',label:'Trích dẫn',symbol:'❝'},{id:'task',label:'Danh sách việc cần làm',symbol:'☐'},
 {id:'divider',label:'Đường phân cách',symbol:'—',block:true},{id:'fence',label:'Khối mã',symbol:'Code',block:true},{id:'table',label:'Bảng 2 cột',symbol:'Table',block:true}
];
const display=(raw:string)=>raw.replace(/\r\n?/g,'\n');
const codeRuns=(text:string)=>text.match(/\x60+/g)??[];
export function formatMarkdown(raw:string,from:number,to:number,action:FormatAction):FormatResult{
 const shown=display(raw),offsets=[0];
 for(let i=0;i<raw.length;i++){if(raw[i]==='\r'&&raw[i+1]==='\n')i++;offsets.push(i+1);}
 let start=Math.max(0,Math.min(shown.length,Math.min(from,to))),end=Math.max(start,Math.min(shown.length,Math.max(from,to)));
 const newline=raw.match(/\r\n|\r|\n/)?.[0]??'\n';
 function replace(text:string,selectedStart=display(text).length,selectedEnd=selectedStart):FormatResult{
  return {raw:raw.slice(0,offsets[start])+text+raw.slice(offsets[end]),start:start+selectedStart,end:start+selectedEnd};
 }
 if(/^(h[123]|bullet|number|quote|task)$/.test(action)){
  start=start===0?0:shown.lastIndexOf('\n',start-1)+1;
  const last=shown.indexOf('\n',end>start&&shown[end-1]==='\n'?end-1:end);
  end=last===-1?shown.length:last;
  const selected=raw.slice(offsets[start],offsets[end]);
  let index=0;
  const text=selected.split(/(\r\n|\r|\n)/).map((line,i)=>{
   if(i%2===1)return line;
   const body=/^h[123]$/.test(action)?line.replace(/^ {0,3}#{1,6}[ \t]+/,''):line;
   const prefix=action==='h1'?'# ':action==='h2'?'## ':action==='h3'?'### ':action==='bullet'?'- ':action==='number'?String(++index)+'. ':action==='quote'?'> ':'- [ ] ';
   return prefix+body;
  }).join('');
  return replace(text,0,display(text).length);
 }
 const selected=raw.slice(offsets[start],offsets[end]);
 if(action==='divider'||action==='fence'||action==='table'){
  if(action!=='fence'&&selected)start=end;
  const before=start>0&&!shown.slice(0,start).endsWith('\n\n')?newline+newline:'';
  const after=end<shown.length&&!shown.slice(end).startsWith('\n\n')?newline+newline:'';
  const ticks=String.fromCharCode(96).repeat(codeRuns(selected).reduce((n,x)=>Math.max(n,x.length+1),3));
  const text=action==='divider'?'---':action==='fence'?ticks+newline+selected+newline+ticks:['| Cột 1 | Cột 2 |','| --- | --- |','|  |  |'].join(newline);
  return replace(before+text+after);
 }
 let left='',right='';
 if(action==='bold')left=right='**';else if(action==='italic')left=right='*';else if(action==='strike')left=right='~~';
 else if(action==='code')left=right=String.fromCharCode(96).repeat(codeRuns(selected).reduce((n,x)=>Math.max(n,x.length+1),1));
 else if(action==='link'){left='[';right='](https://)';}
 return replace(left+selected+right,left.length,left.length+display(selected).length);
}
