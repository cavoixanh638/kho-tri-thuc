import assert from 'node:assert/strict';

// P11 standalone deterministic fixture oracle. This is NOT an ORM/HTTP/DB
// performance test; see test_parallel_collections.py for that.
const items = Array.from({ length: 10000 }, (_, n) => ({
  id: n + 1, owner: 'one', groups: new Set([n % 100, (n + 7) % 100]),
  favorite: n % 5 === 0, saved: n % 7, published: n % 11,
}));
items.push({ id: 10001, owner: 'two', groups: new Set([0]), favorite: true });

const queries = [
  () => true,
  item => item.favorite,
  item => item.groups.has(0) || item.groups.has(1),
  item => item.groups.has(0) && item.groups.has(7) && !item.groups.has(1),
  item => !item.favorite,
];
const totals = [];
for (const query of queries) {
  const result = items.filter(item => item.owner === 'one' && query(item));
  const paged = [];
  for (let start = 0; start < result.length; start += 100)
    paged.push(...result.slice(start, start + 100).map(item => item.id));
  assert.deepEqual(paged, result.map(item => item.id));
  assert.equal(new Set(paged).size, result.length);
  totals.push(result.length);
}
let fixtureCount = 0;
const clauses = [
  [[0], [], []], [[0, 2], [], []], [[], [0, 1], []],
  [[0, 1], [], [2]], [[], [2], [0]],
];
for (const kind of ['topics', 'projects', 'tags']) {
  for (const [any, all, exclude] of clauses) {
    for (const favorite of [null, true]) {
      const result = items.filter(item =>
        item.owner === 'one' &&
        (!any.length || any.some(id => item.groups.has(id))) &&
        all.every(id => item.groups.has(id)) &&
        exclude.every(id => !item.groups.has(id)) &&
        (favorite === null || item.favorite === favorite));
      assert.equal(result.length, new Set(result.map(item => item.id)).size);
      fixtureCount++;
    }
  }
}
assert.equal(fixtureCount, 30);
const tableOrder = ['A', 'B', 'C'];
const timelineOrder = ['A', 'C', 'B'];
assert.deepEqual(new Set(tableOrder), new Set(timelineOrder));
assert.notDeepEqual(tableOrder, timelineOrder);
console.log(JSON.stringify({
  status: 'PASS',
  scope: 'independent deterministic JS oracle, NOT Django/PG/HTTP',
  items: 10000, groups: 100, owners: 2, saved_queries: 5,
  filter_fixtures: fixtureCount, result_counts: totals,
  timeline_order_divergence: true,
}));
