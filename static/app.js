document.addEventListener('DOMContentLoaded', () => {
  const alertBox = document.getElementById('alertBox');
  const cvLoadedView = document.getElementById('cvLoadedView');
  const cvUploadView = document.getElementById('cvUploadView');
  const cvFileInput = document.getElementById('cvFileInput');
  const cvFilename = document.getElementById('cvFilename');
  const cvMeta = document.getElementById('cvMeta');
  const btnChangeCv = document.getElementById('btnChangeCv');
  
  const searchForm = document.getElementById('searchForm');
  const gmailLabelInput = document.getElementById('gmailLabel');
  const emailCountSelect = document.getElementById('emailCount');
  const btnProcess = document.getElementById('btnProcess');
  const btnText = document.getElementById('btnText');
  const btnSpinner = document.getElementById('btnSpinner');
  const processStatusText = document.getElementById('processStatusText');
  
  const resultsCount = document.getElementById('resultsCount');
  const resultsList = document.getElementById('resultsList');

  let cvLoaded = false;

  function showAlert(message, type = 'error') {
    alertBox.textContent = message;
    alertBox.className = `alert alert-${type}`;
    alertBox.classList.remove('hidden');
    setTimeout(() => {
      alertBox.classList.add('hidden');
    }, 6000);
  }

  // --- CV Management ---
  async function checkCvStatus() {
    try {
      const res = await fetch('/api/cv/status');
      const data = await res.json();
      if (data.exists) {
        showCvLoaded(data);
      } else {
        showCvUpload();
      }
    } catch (err) {
      console.error('Error verificando estado del CV:', err);
    }
  }

  function showCvLoaded(info) {
    cvLoaded = true;
    cvFilename.textContent = info.filename || 'cv.pdf';
    cvMeta.textContent = `${info.pages ? info.pages + ' pág(s)' : ''} · ${info.size_kb ? info.size_kb + ' KB' : 'Cargado'}`;
    cvLoadedView.classList.remove('hidden');
    cvUploadView.classList.add('hidden');
    btnChangeCv.classList.remove('hidden');
  }

  function showCvUpload() {
    cvLoaded = false;
    cvLoadedView.classList.add('hidden');
    cvUploadView.classList.remove('hidden');
    btnChangeCv.classList.add('hidden');
  }

  btnChangeCv.addEventListener('click', () => {
    showCvUpload();
  });

  cvUploadView.addEventListener('click', () => {
    cvFileInput.click();
  });

  cvUploadView.addEventListener('dragover', (e) => {
    e.preventDefault();
    cvUploadView.classList.add('dragover');
  });

  cvUploadView.addEventListener('dragleave', () => {
    cvUploadView.classList.remove('dragover');
  });

  cvUploadView.addEventListener('drop', (e) => {
    e.preventDefault();
    cvUploadView.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleCvFile(e.dataTransfer.files[0]);
    }
  });

  cvFileInput.addEventListener('change', () => {
    if (cvFileInput.files && cvFileInput.files.length > 0) {
      handleCvFile(cvFileInput.files[0]);
    }
  });

  async function handleCvFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showAlert('Por favor seleccioná un archivo PDF válido.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/cv/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        showAlert('CV cargado y guardado correctamente.', 'success');
        showCvLoaded(data);
      } else {
        showAlert(data.detail || 'Error al subir el CV.');
      }
    } catch (err) {
      showAlert('Error de conexión al subir el archivo.');
    }
  }

  // --- Render Job Cards ---
  function renderJobCards(jobs) {
    if (!jobs || jobs.length === 0) {
      resultsCount.textContent = '0 ofertas';
      resultsList.innerHTML = `
        <div class="empty-state">
          <p>No se encontraron ofertas evaluadas para esta etiqueta.</p>
        </div>`;
      return;
    }

    resultsCount.textContent = `${jobs.length} ofertas encontradas`;
    resultsList.innerHTML = '';

    jobs.forEach(job => {
      const card = document.createElement('div');
      card.className = 'job-card';

      let badgeClass = 'badge-no';
      const pct = job.match_percentage || 0;
      if (pct >= 75) {
        badgeClass = 'badge-yes';
      } else if (pct >= 50) {
        badgeClass = 'badge-maybe';
      }

      card.innerHTML = `
        <div class="job-content">
          <div class="job-title-row">
            <h3 class="job-title">${escapeHtml(job.title || 'Oferta de empleo')}</h3>
          </div>
          <div class="job-meta">
            ${escapeHtml(job.company_or_context || 'Digest de correo')} · ${escapeHtml(job.email_subject || '')}
          </div>
          <div class="job-suggestion">
            <strong>Sugerencia:</strong> ${escapeHtml(job.suggestion || 'Sin sugerencias adicionales.')}
          </div>
          <div style="margin-top: 0.9rem;">
            <a href="${escapeHtml(job.link || '#')}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="font-size: 0.825rem; padding: 0.4rem 0.85rem;">
              Ver Oferta Completa ↗
            </a>
          </div>
        </div>
        <div class="match-score-badge ${badgeClass}">
          <div class="match-percentage">${pct}%</div>
          <div class="match-verdict">${escapeHtml(job.verdict || 'Match')}</div>
        </div>
      `;

      resultsList.appendChild(card);
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, (m) => {
      switch (m) {
        case '&': return '&amp;';
        case '<': return '&lt;';
        case '>': return '&gt;';
        case '"': return '&quot;';
        case "'": return '&#39;';
        default: return m;
      }
    });
  }

  // --- Load Latest Matches Cache ---
  async function loadLatestMatches() {
    try {
      const res = await fetch('/api/jobs/latest');
      if (res.ok) {
        const data = await res.json();
        if (data.jobs && data.jobs.length > 0) {
          renderJobCards(data.jobs);
        }
      }
    } catch (e) {
      // Ignorar si no hay caché previa
    }
  }

  // --- Form Search & Process Submit ---
  searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!cvLoaded) {
      showAlert('Por favor subí primero tu CV en PDF para poder evaluar el match.');
      return;
    }

    const label = gmailLabelInput.value.trim();
    const count = parseInt(emailCountSelect.value, 10) || 3;

    if (!label) {
      showAlert('Por favor ingresá una etiqueta de Gmail.');
      return;
    }

    // Set Loading State
    btnProcess.disabled = true;
    btnSpinner.classList.remove('hidden');
    btnText.textContent = 'Procesando...';
    processStatusText.textContent = 'Conectando a Gmail y analizando ofertas...';

    try {
      const res = await fetch('/api/jobs/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: label, count: count })
      });

      const data = await res.json();
      if (res.ok) {
        renderJobCards(data.jobs);
        showAlert(`¡Análisis completado! Se evaluaron ${data.jobs ? data.jobs.length : 0} ofertas.`, 'success');
      } else {
        showAlert(data.detail || 'Ocurrió un error al procesar las ofertas.');
      }
    } catch (err) {
      showAlert('Error de conexión con el servidor local.');
    } finally {
      btnProcess.disabled = false;
      btnSpinner.classList.add('hidden');
      btnText.textContent = 'Buscar y Evaluar Ofertas';
      processStatusText.textContent = '';
    }
  });

  // Init
  checkCvStatus();
  loadLatestMatches();
});
