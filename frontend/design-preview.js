const frame = document.querySelector('#screen');
const fields = ['scene', 'design', 'theme', 'width'].map(id => document.getElementById(id));
const params = new URLSearchParams(location.search);
for (const field of fields) if ([...field.options].some(option => option.value === params.get(field.id))) field.value = params.get(field.id);
function render() {
  const [scene, design, theme, width] = fields.map(field => field.value);
  const query = new URLSearchParams({scene});
  if (design === 'calm') { query.set('design', 'calm'); query.set('theme', theme); }
  const url = '/audit-design.html?' + query;
  frame.src = url;
  frame.style.width = width === 'full' ? '100%' : width + 'px';
  frame.style.height = width === '375' ? '900px' : '1100px';
  document.getElementById('direct').href = url;
  document.getElementById('theme').disabled = design === 'before';
  document.getElementById('notice').textContent = design === 'before' ? '기존 화면에는 어두운 테마가 없습니다.' : '';
  history.replaceState(null, '', '?' + new URLSearchParams(Object.fromEntries(fields.map(field => [field.id, field.value]))));
}
fields.forEach(field => field.addEventListener('change', render));
document.getElementById('reset').addEventListener('click', render);
render();
