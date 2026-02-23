new bootstrap.Toast(document.getElementById('welcomeToast'), { delay: 4000 }).show();

const picker = document.getElementById('colorPicker');
picker.addEventListener('input', () => {
    document.getElementById('previewSwatch').style.background = picker.value;
    document.getElementById('previewHex').textContent = picker.value.toUpperCase();
});

let currentPrimaryHex = '';
let currentSelectedHex = '';

async function findColors() {
    const color = picker.value;
    const btn = document.getElementById('searchBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Finding colors...';
    try {
        const res = await fetch('/color-recomend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ color })
        });
        const data = await res.json();
        if (data.error) { showErrorToast(data.error); }
        else {
            bootstrap.Modal.getInstance(document.getElementById('colorModal')).hide();
            renderResults(color, data.colors);
        }
    } catch { showErrorToast('Network error. Please try again.'); }
    finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-wand-magic-sparkles me-2"></i>Find Recommended Colors';
    }
}

async function randomColors() {
    const btn = document.getElementById('randomBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating...';
    try {
        const res = await fetch('/color-random', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.error) { showErrorToast(data.error); }
        else {
            bootstrap.Modal.getInstance(document.getElementById('colorModal')).hide();
            renderResults(data.primary.hex, data.colors);
        }
    } catch { showErrorToast('Network error. Please try again.'); }
    finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-shuffle me-2"></i>Surprise Me';
    }
}

function renderResults(primaryHex, colors) {
    currentPrimaryHex = primaryHex;
    document.getElementById('primarySwatch').style.background = primaryHex;
    document.getElementById('previewPanel').classList.remove('show');
    document.querySelectorAll('.color-chip').forEach(c => c.classList.remove('active'));

    const grid = document.getElementById('colorGrid');
    grid.innerHTML = '';
    colors.forEach(c => {
        const chip = document.createElement('div');
        chip.className = 'color-chip';
        chip.dataset.hex = c.hex;
        chip.innerHTML = `
            <div class="swatch" style="background:${c.hex};"></div>
            <div class="chip-label">
                <span class="chip-name">${c.name}</span>
                <span class="chip-hex">${c.hex.toUpperCase()}</span>
            </div>`;
        chip.onclick = () => showPreview(c.hex, c.name, chip);
        grid.appendChild(chip);
    });

    const card = document.getElementById('resultsCard');
    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showPreview(hex, name, chipEl) {
    currentSelectedHex = hex;

    document.querySelectorAll('.color-chip').forEach(c => c.classList.remove('active'));
    chipEl.classList.add('active');

    document.getElementById('showcasePrimary').style.background = currentPrimaryHex;
    document.getElementById('showcaseSelected').style.background = hex;

    document.getElementById('panelDot').style.background = hex;
    document.getElementById('panelName').textContent = name;
    document.getElementById('panelHex').textContent = hex.toUpperCase();

    const copyBtn = document.getElementById('copyBtn');
    copyBtn.classList.remove('copied');
    copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy Hex';

    const strip = document.getElementById('harmonyStrip');
    strip.innerHTML = '';
    const steps = 8;
    for (let i = 0; i < steps; i++) {
        const seg = document.createElement('div');
        seg.className = 'harmony-seg';
        seg.style.background = blendHex(currentPrimaryHex, hex, i / (steps - 1));
        strip.appendChild(seg);
    }

    document.getElementById('previewPanel').classList.add('show');
}

function blendHex(hex1, hex2, t) {
    const r1 = parseInt(hex1.slice(1,3),16), g1 = parseInt(hex1.slice(3,5),16), b1 = parseInt(hex1.slice(5,7),16);
    const r2 = parseInt(hex2.slice(1,3),16), g2 = parseInt(hex2.slice(3,5),16), b2 = parseInt(hex2.slice(5,7),16);
    const r = Math.round(r1 + (r2-r1)*t), g = Math.round(g1 + (g2-g1)*t), b = Math.round(b1 + (b2-b1)*t);
    return `rgb(${r},${g},${b})`;
}

function doCopy() {
    navigator.clipboard.writeText(currentSelectedHex.toUpperCase());
    const btn = document.getElementById('copyBtn');
    btn.classList.add('copied');
    btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
    setTimeout(() => {
        btn.classList.remove('copied');
        btn.innerHTML = '<i class="fas fa-copy"></i> Copy Hex';
    }, 2000);

    const badge = document.getElementById('copiedBadge');
    badge.classList.add('show');
    setTimeout(() => badge.classList.remove('show'), 2200);
}

function showErrorToast(msg) {
    document.getElementById('errorToastMsg').textContent = msg;
    new bootstrap.Toast(document.getElementById('errorToast'), { delay: 4000 }).show();
}

async function uploadAvatar(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('avatar', file);

    const avatar = document.querySelector('.profile-avatar');
    avatar.style.opacity = '0.5';

    try {
        const res = await fetch('/upload-avatar', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.error) {
            alert(data.error);
        } else {
            avatar.innerHTML = `<img src="${data.avatar}" alt="avatar">`;
            document.getElementById('navAvatar').innerHTML = `<img src="${data.avatar}" alt="avatar">`;
        }
    } catch {
        alert('Upload failed. Please try again.');
    } finally {
        avatar.style.opacity = '1';
    }
}