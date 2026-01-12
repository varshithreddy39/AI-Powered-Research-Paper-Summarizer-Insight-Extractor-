// Academic UI Logic - Connected to Backend

document.addEventListener("DOMContentLoaded", () => {
  console.log("[v1] Academic UI Logic initialized")

  let currentDocId = null;

  // --- Dashboard Logic ---
  const dashboardStats = document.querySelector('.metrics-grid');
  if (dashboardStats) {
    fetch('/api/dashboard')
      .then(res => res.json())
      .then(data => {
        // Update Stats
        document.getElementById('stat-uploaded').innerText = data.stats.uploaded;
        document.getElementById('stat-summaries').innerText = data.stats.summaries;
        document.getElementById('stat-insights').innerText = data.stats.insights;

        // Update Recent Docs
        const docList = document.querySelector('.doc-list');
        if (docList && data.recent_documents.length > 0) {
          docList.innerHTML = data.recent_documents.map(doc => `
                      <div class="doc-item">
                        <div class="doc-info">
                          <h4>${doc.metadata?.title || doc.original_filename}</h4>
                          <div class="doc-meta">Uploaded ${new Date(doc.upload_date).toLocaleDateString()}</div>
                        </div>
                        <div class="doc-actions">
                          <span class="status-badge status-completed">Ready</span>
                        </div>
                      </div>
                  `).join('');
        } else if (docList) {
          docList.innerHTML = '<p style="color:var(--text-secondary); text-align:center; padding:2rem;">No documents found.</p>';
        }

        // Initialize Chart
        const ctx = document.getElementById('analyticsChart');
        if (ctx) {
          // Get styles for chart colors
          const style = getComputedStyle(document.body);
          const accent = style.getPropertyValue('--accent-primary').trim();
          const success = style.getPropertyValue('--success-color').trim();
          const textSecondary = style.getPropertyValue('--text-secondary').trim();

          new Chart(ctx, {
            type: 'doughnut',
            data: {
              labels: ['Uploaded Files', 'Summaries', 'Insights'],
              datasets: [{
                data: [data.stats.uploaded, data.stats.summaries, data.stats.insights],
                backgroundColor: [
                  '#3b82f6', // Bright Blue
                  '#10b981', // Emerald
                  '#8b5cf6'  // Violet
                ],
                borderWidth: 0,
                hoverOffset: 4
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'bottom',
                  labels: {
                    font: { family: 'Inter', size: 12 },
                    color: textSecondary,
                    usePointStyle: true,
                    padding: 20
                  }
                }
              },
              cutout: '65%'
            }
          });
        }
      })
      .catch(err => console.error("Failed to load dashboard data", err));
  }

  // --- Theme Management ---
  const themeToggle = document.getElementById("theme-toggle")
  const themeIcon = document.getElementById("theme-icon")

  // Set initial theme
  const savedTheme = localStorage.getItem("theme") || "light"
  document.documentElement.setAttribute("data-theme", savedTheme)
  updateThemeUI(savedTheme)

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const currentTheme = document.documentElement.getAttribute("data-theme")
      const newTheme = currentTheme === "light" ? "dark" : "light"

      document.documentElement.setAttribute("data-theme", newTheme)
      localStorage.setItem("theme", newTheme)
      updateThemeUI(newTheme)
    })
  }

  function updateThemeUI(theme) {
    if (!themeIcon) return
    if (theme === "dark") {
      themeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />` // Sun icon
    } else {
      themeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />` // Moon icon
    }
  }

  // --- Active Link Management ---
  const currentPath = window.location.pathname.split("/").pop() || "index.html"
  const links = document.querySelectorAll(".nav-links a, .sidebar-link")

  links.forEach((link) => {
    const href = link.getAttribute("href")
    if (href === currentPath) {
      link.classList.add("active")
    }
  })

  // --- Upload Logic ---
  const uploadArea = document.getElementById("upload-area")
  const fileInput = document.getElementById("file-input")
  const uploadProgress = document.getElementById("upload-progress")
  const progressBar = document.getElementById("progress-bar")
  const uploadStatus = document.getElementById("upload-status")

  const preUploadState = document.getElementById("pre-upload-state")
  const postUploadState = document.getElementById("post-upload-state")

  if (uploadArea && fileInput) {
    uploadArea.addEventListener("click", () => fileInput.click())

    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0]
      if (file && file.type === "application/pdf") {
        handleUpload(file)
      } else {
        alert("Please upload a valid academic PDF.")
      }
    })

    // Drag and drop
    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault()
      uploadArea.style.borderColor = "var(--accent-primary)"
    })

    uploadArea.addEventListener("dragleave", () => {
      uploadArea.style.borderColor = "var(--border-color)"
    })

    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault()
      uploadArea.style.borderColor = "var(--border-color)"
      const file = e.dataTransfer.files[0]
      if (file && file.type === "application/pdf") {
        handleUpload(file)
      }
    })
  }

  async function handleUpload(file) {
    if (!uploadProgress) return

    uploadProgress.style.display = "block"
    uploadStatus.innerText = `Uploading ${file.name}...`
    if (progressBar) progressBar.style.width = "30%"

    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch("/upload", {
        method: "POST",
        body: formData,
      })
      const data = await response.json()

      if (response.ok) {
        currentDocId = data.doc_id
        uploadStatus.innerText = "Processing text..."
        if (progressBar) progressBar.style.width = "60%"

        // Auto-extract text
        await extractText(currentDocId, file.name)

        if (progressBar) progressBar.style.width = "100%"
        setTimeout(() => {
          if (preUploadState && postUploadState) {
            preUploadState.style.display = "none"
            postUploadState.style.display = "grid"
            console.log("[v1] Transitioned to research split-view")
          }
        }, 500)
      } else {
        uploadStatus.innerText = `Error: ${data.error}`
      }
    } catch (error) {
      console.error("Upload failed", error)
      uploadStatus.innerText = "Upload failed."
    }
  }

  async function extractText(docId, filename) {
    try {
      const response = await fetch("/extract-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: docId })
      })
      const data = await response.json()
      if (response.ok) {
        // Update Top Section Metadata and Text
        const titleEl = document.getElementById("meta-title");
        const authorsEl = document.getElementById("meta-authors");
        const yearEl = document.getElementById("meta-year");
        const sourceEl = document.getElementById("meta-source");

        if (data.metadata) {
          if (titleEl) titleEl.innerText = data.metadata.title || filename;
          if (authorsEl) authorsEl.innerText = data.metadata.authors || "Unknown";
          if (yearEl) yearEl.innerText = data.metadata.year || "Unknown";
          if (sourceEl) sourceEl.innerText = data.metadata.source || "Unknown";
        } else {
          if (titleEl) titleEl.innerText = filename;
        }

        const rawTextBox = document.querySelector(".raw-text-box")
        if (rawTextBox) rawTextBox.innerText = data.text;
      }
    } catch (e) {
      console.error("Text extraction failed", e)
    }
  }

  // --- View Switching & API Calls ---
  window.switchView = async (viewName) => {
    // Hide all views
    const views = document.querySelectorAll('[id^="view-"]')
    views.forEach((view) => (view.style.display = "none"))

    // Show selected view
    const selectedView = document.getElementById(`view-${viewName}`)
    if (selectedView) {
      selectedView.style.display = "block"
      console.log(`[v1] Switched to view: ${viewName}`)

      // Trigger API calls if needed and if data is empty or we want to refresh
      if (viewName === 'summary' && currentDocId) {
        await fetchSummary(currentDocId);
      } else if (viewName === 'concepts' && currentDocId) {
        await fetchConcepts(currentDocId);
      } else if (viewName === 'insights' && currentDocId) {
        await fetchInsights(currentDocId);
      } else if (viewName === 'search') {
        // Enable search input
        const searchInput = document.querySelector('#view-search input');
        if (searchInput) {
          searchInput.disabled = false;
          searchInput.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
              await performSearch(currentDocId, e.target.value);
            }
          });
        }
      }
    }
  }

  async function fetchSummary(docId) {
    const summaryContainer = document.querySelector("#view-summary");
    // Check if already populated with actual content (not placeholder)
    if (summaryContainer.querySelector("h3") && summaryContainer.innerText.includes("Executive Summary")) {
      return; // Already generated
    }

    summaryContainer.innerHTML = '<div class="insight-block"><p>Generating summary...</p></div>';

    try {
      const response = await fetch("/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: docId })
      });
      const data = await response.json();

      if (response.ok) {
        // Simple markdown replacement for bold/headers
        let htmlHtml = data.summary
          .replace(/^### (.*$)/gim, '<h3>$1</h3>')
          .replace(/^## (.*$)/gim, '<h2>$1</h2>')
          .replace(/^# (.*$)/gim, '<h1>$1</h1>')
          .replace(/\*\*(.*)\*\*/gim, '<b>$1</b>')
          .replace(/\n\n/g, '</p><p>')
          .replace(/\n/g, '<br />');

        summaryContainer.innerHTML = `
                <div class="insight-block">
                  <h3>Executive Summary</h3>
                  <p>${htmlHtml}</p>
                </div>`;
      } else {
        const errorMsg = data.error || "Unknown error";
        summaryContainer.innerHTML = `
            <div class="insight-block">
                <p style="color: #ef4444; font-weight: 500;">Generation Failed</p>
                <p style="font-size: 0.9rem; color: var(--text-secondary);">
                    The server returned an error: ${errorMsg}. <br>
                    Please try again or upload a smaller document.
                </p>
            </div>`;
      }
    } catch (e) {
      summaryContainer.innerHTML = `<div class="insight-block"><p style="color:red">Error connecting to server.</p></div>`;
    }
  }

  async function fetchConcepts(docId) {
    const container = document.querySelector("#view-concepts");
    const btn = container.querySelector("button");
    if (btn) btn.style.display = 'none'; // Hide generate button if present

    container.innerHTML = '<div class="insight-block"><p>Extracting concepts...</p></div>';

    try {
      const response = await fetch("/key-concepts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: docId })
      });
      const data = await response.json();

      if (response.ok) {
        const pills = data.concepts.map(c => `<span class="pill">${c}</span>`).join('');
        container.innerHTML = `
                <div class="insight-block">
                  <h3>Key Concepts</h3>
                  <div class="pill-container">${pills}</div>
                </div>`;
      } else {
        container.innerHTML = `<div class="insight-block"><p style="color:red">Error: ${data.error}</p></div>`;
      }
    } catch (e) {
      container.innerHTML = `<div class="insight-block"><p style="color:red">Error connecting to server.</p></div>`;
    }
  }

  async function fetchInsights(docId) {
    const container = document.querySelector("#view-insights");
    container.innerHTML = '<div class="insight-block"><p>Generating insights...</p></div>';

    try {
      const response = await fetch("/insights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: docId })
      });
      const data = await response.json();
      if (response.ok) {
        let htmlHtml = data.insights
          .replace(/^### (.*$)/gim, '<h3>$1</h3>')
          .replace(/\*\*(.*)\*\*/gim, '<b>$1</b>')
          .replace(/\n/g, '<br />');

        container.innerHTML = `
                <div class="insight-block">
                  <h3>Research Insights</h3>
                  <p>${htmlHtml}</p>
                </div>`;
      } else {
        container.innerHTML = `<div class="insight-block"><p style="color:red">Error: ${data.error}</p></div>`;
      }
    } catch (e) {
      container.innerHTML = `<div class="insight-block"><p style="color:red">Error connecting to server.</p></div>`;
    }
  }

  async function performSearch(docId, query) {
    const container = document.querySelector("#view-search div.insight-block");
    // Keep input, remove previous results
    const existingResults = container.querySelectorAll('.search-result');
    existingResults.forEach(e => e.remove());

    const loading = document.createElement('p');
    loading.innerText = 'Searching...';
    container.appendChild(loading);

    try {
      const response = await fetch("/semantic-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: docId, query: query })
      });
      const data = await response.json();
      loading.remove();

      if (response.ok && data.results) {
        if (data.results.length === 0) {
          const noRes = document.createElement('p');
          noRes.innerText = 'No results found.';
          noRes.className = 'search-result';
          container.appendChild(noRes);
        } else {
          data.results.forEach(res => {
            const p = document.createElement('div');
            p.className = 'search-result';
            p.style = "margin-top: 1rem; padding: 1rem; background: var(--bg-hover); border-radius: 4px; border: 1px solid var(--border-color); font-size: 0.9rem;";
            p.innerText = "..." + res + "...";
            container.appendChild(p);
          });
        }
      }
    } catch (e) {
      loading.innerText = 'Search failed.';
    }
  }

  // --- Section Switching (for raw text tabs) ---
  window.switchSection = (sectionName) => {
    // Current placeholder logic does nothing but log
    console.log(`[v1] Switched to section: ${sectionName}`)
  }
})
