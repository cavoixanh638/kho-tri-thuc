import test from 'node:test';
import assert from 'node:assert/strict';
import {highlightSearch} from '../src/SearchHighlight.ts';

test('SEARCH-04 preserves Vietnamese NFC/NFD, đ and whitespace while highlighting exact tokens',()=>{
 const text='Tie\u0302\u0301ng Việt, Đường phố!  Giữ nguyên.';
 const parts=highlightSearch(text,'tieng viet duong');
 assert.deepEqual(parts.filter(p=>p.match).map(p=>p.text),['Tie\u0302\u0301ng','Việt','Đường']);
 assert.equal(parts.map(p=>p.text).join(''),text);
});
test('SEARCH-04 does not invent a fuzzy match or return HTML markup',()=>{
 const text='<img src=x> mất đuôi câu nói';
 assert.deepEqual(highlightSearch(text,'không tồn tại'),[{text,match:false}]);
 const parts=highlightSearch(text,'img câu');
 assert.equal(parts.map(p=>p.text).join(''),text);
 assert.deepEqual(parts.filter(p=>p.match).map(p=>p.text),['img','câu']);
 assert.deepEqual(highlightSearch(text,'  '),[{text,match:false}]);
});
