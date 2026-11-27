// Offline catalog contract. No dependency install, network, secrets or database.
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

function validateCatalog(markdown){
  const minimum={WS:10,TREE:11,EDIT:16,TYPE:12,VIEW:17,LINK:10,NAV:6,CAP:15,CLIP:11,SOURCE:17,SEARCH:8,ORG:8,AI:16,MEET:8,VIS:5,PORT:14,GATE:9};
  const reports=[[43,6],[42,6],[45,6],[46,6],[40,6],[41,6],[38,6],[36,5],[34,6],[39,5],[44,5],[32,5],[37,5],[33,5],[31,5],[35,5],[30,6]];
  const expected=new Map();
  reports.forEach(([pr,n],i)=>{const group='G'+String(i+1).padStart(2,'0');for(let j=1;j<=n;j++)expected.set(group+'.'+j,{pr,group});});
  const states=['CÓ MÃ','MỘT PHẦN','THIẾU','HOÃN CÓ ĐIỀU KIỆN'];
  const rows=new Map(),reverse=new Map(),counts=Object.fromEntries(states.map(s=>[s,0]));
  let group;
  const check=(condition,message)=>{if(!condition)throw new Error(message);};
  for(const line of markdown.split(/\r?\n/)){
    const heading=/^### ([A-Z]+) — /.exec(line);
    if(heading){group=heading[1];continue;}
    if(/^\| [A-Z]+-\d{2,} \|/.test(line)){
      const fields=line.split('|').slice(1,-1).map(s=>s.trim());
      check(fields.length===5,`Malformed feature row ${fields[0]}`);
      const [id,status,name,sources,acceptance]=fields;
      check(!rows.has(id),`Duplicate feature ID ${id}`);
      check(group===id.split('-')[0],`Wrong section for ${id}`);
      check(states.includes(status)&&name&&sources&&acceptance,`Incomplete feature row ${id}`);
      const codes=sources.split(/\s+/).filter(source=>/^G\d{2}\.\d+$/.test(source));
      for(const code of codes)check(expected.has(code),`Unknown original proposal ${code}`);
      rows.set(id,{codes:new Set(codes),status});counts[status]++;
    }else if(/^\| \[G\d{2} /.test(line)){
      const fields=line.split('|').slice(1,-1).map(s=>s.trim());
      check(fields.length===3,'Malformed reverse mapping');
      const [link,proposal,list]=fields,code=/^G\d{2}\.\d+(?=\s|$)/.exec(proposal)?.[0],spec=expected.get(code);
      check(spec,`Unknown proposal ${proposal}`);
      check(link.startsWith('['+spec.group+' ')&&link.includes('/pull/'+spec.pr+')'),`Wrong research PR ${code}`);
      check(!reverse.has(code),`Duplicate proposal ${code}`);
      const ids=list.split(',').map(s=>s.trim()).filter(Boolean);
      check(ids.length>0&&new Set(ids).size===ids.length,`Missing/duplicate mapping ${code}`);
      reverse.set(code,new Set(ids));
    }
  }
  for(const [group,n] of Object.entries(minimum))for(let i=1;i<=n;i++){
    const id=group+'-'+String(i).padStart(2,'0');check(rows.has(id),`Removed baseline ID ${id}`);
  }
  for(const code of expected.keys()){
    const refs=reverse.get(code);check(refs,`Removed original proposal ${code}`);
    const forward=[...rows].filter(([,row])=>row.codes.has(code)).map(([id])=>id);
    check(forward.length===refs.size&&forward.every(id=>refs.has(id)),`Forward/reverse mismatch ${code}`);
    for(const id of refs)check(rows.has(id),`Unknown mapped ID ${id}`);
  }
  const summary=markdown.split(/\r?\n/).find(line=>line.startsWith('**Kiểm kê:**'));
  const totals=summary&&/(\d+) ID trong (\d+) nhóm, (\d+)\/(\d+) đề xuất/.exec(summary);
  check(totals&&Number(totals[1])===rows.size&&Number(totals[2])===new Set([...rows.keys()].map(id=>id.split('-')[0])).size&&Number(totals[3])===reverse.size&&Number(totals[4])===expected.size,'Stale catalog totals');
  for(const state of states){
    const match=new RegExp(state+': (\\d+)').exec(summary);check(match&&Number(match[1])===counts[state],`Stale status count ${state}`);
  }
  return {features:rows.size,groups:Number(totals[2]),originalProposals:expected.size,statuses:counts};
}

function negativeFixtures(catalog){
  const first=catalog.split(/\r?\n/).find(line=>line.startsWith('| WS-01 |'));
  const mapping=catalog.split(/\r?\n/).find(line=>line.startsWith('| [G01 Notion')&&line.includes(' | G01.1 '));
  const mapped=mapping.split('|')[3].trim().split(', ');
  const changedMap=mapping.replace(mapped.join(', '),mapped.slice(1).join(', '));
  return [
    ['missing baseline feature',catalog.replace(first,'')],
    ['duplicate baseline ID',catalog.replace(first,first+'\n'+first)],
    ['missing original mapping',catalog.replace(mapping,'')],
    ['wrong research PR',catalog.replace(mapping,mapping.replace('/pull/43)','/pull/42)'))],
    ['unmatched reverse mapping',catalog.replace(mapping,changedMap)],
    ['stale summary',catalog.replace(/(\*\*Kiểm kê:\*\* )(\d+) ID/,(_,prefix,n)=>prefix+(Number(n)+1)+' ID')],
  ];
}

const catalog=readFileSync(new URL('../../docs/FEATURE_CATALOG_AND_PLAN.md',import.meta.url),'utf8');
const result=validateCatalog(catalog);
const negatives=negativeFixtures(catalog);
for(const [name,mutated] of negatives){assert.notEqual(mutated,catalog,name+' fixture changed');assert.throws(()=>validateCatalog(mutated),undefined,name);}
console.log(JSON.stringify({status:'PASS',...result,negativeCases:negatives.length}));
