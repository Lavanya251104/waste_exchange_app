async function registerUser() {
  const username = document.getElementById('reg_username').value.trim();
  if (!username) return alert('Enter username');

  const res = await fetch('/api/register', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({username})
  });

  const data = await res.json();
  document.getElementById('reg_result').textContent = data.message || data.error;
}

async function addWaste() {
  const user_id = parseInt(document.getElementById('waste_user_id').value);
  const type = document.getElementById('waste_type').value.trim();
  const quantity = parseFloat(document.getElementById('waste_quantity').value);
  const description = document.getElementById('waste_desc').value.trim();

  if (!user_id || !type || !quantity) return alert('Fill all required fields');

  const res = await fetch('/api/waste', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({user_id, type, quantity, description})
  });

  const data = await res.json();
  document.getElementById('add_waste_result').textContent = data.message || data.error;
  loadWaste();
}

async function loadWaste() {
  const res = await fetch('/api/waste');
  const wastes = await res.json();

  const ul = document.getElementById('waste_list');
  ul.innerHTML = '';

  wastes.forEach(w => {
    const li = document.createElement('li');
    li.textContent = `ID:${w.id} | Type:${w.type} | Qty:${w.quantity} | Seller:${w.username} | Desc:${w.description}`;
    ul.appendChild(li);
  });
}

async function createRequest() {
  const buyer_id = parseInt(document.getElementById('buyer_id').value);
  const waste_id = parseInt(document.getElementById('request_waste_id').value);

  if (!buyer_id || !waste_id) return alert('Fill all fields');

  const res = await fetch('/api/request', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({buyer_id, waste_id})
  });

  const data = await res.json();
  document.getElementById('request_result').textContent = data.message || data.error;
}

async function loadRequests() {
  const user_id = parseInt(document.getElementById('seller_id').value);
  if (!user_id) return alert('Enter seller ID');

  const res = await fetch(`/api/requests/${user_id}`);
  const requests = await res.json();

  const ul = document.getElementById('requests_list');
  ul.innerHTML = '';

  requests.forEach(r => {
    const li = document.createElement('li');
    li.textContent = `Request ID:${r.id} | Buyer:${r.buyer_name} | Waste:${r.type} (${r.quantity}) | Status:${r.status}`;
    ul.appendChild(li);
  });
}

async function loadMatches() {
  const buyer_id = parseInt(document.getElementById('match_buyer_id').value);
  if (!buyer_id) return alert('Enter buyer ID');

  const res = await fetch(`/api/match/${buyer_id}`);
  const data = await res.json();

  const ul = document.getElementById('matches_list');
  ul.innerHTML = '';

  data.matches.forEach(m => {
    const li = document.createElement('li');
    li.textContent = `Waste ID:${m.waste_id} | Type:${m.type} | Qty:${m.quantity} | Seller:${m.seller}`;
    ul.appendChild(li);
  });
}