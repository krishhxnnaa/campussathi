document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
  const searchInput = document.getElementById("searchInput");
  const searchClearBtn = document.getElementById("searchClearBtn");
  const searchSubmitBtn = document.getElementById("searchSubmitBtn");
  const voiceSearchBtn = document.getElementById("voiceSearchBtn");
  const voiceSearchStatus = document.getElementById("voiceSearchStatus");
  const resultsSection = document.getElementById("resultsSection");
  const resultsList = document.getElementById("resultsList");
  const resultsCount = document.getElementById("resultsCount");

  // Report Modal
  const reportModal = document.getElementById("reportModal");
  const openReportLostBtn = document.getElementById("openReportLostBtn");
  const openReportFoundBtn = document.getElementById("openReportFoundBtn");
  const closeReportModal = document.getElementById("closeReportModal");
  const modalTitle = document.getElementById("modalTitle");

  // Report Steps
  const stepInput = document.getElementById("stepInput");
  const stepReview = document.getElementById("stepReview");
  const stepSuccess = document.getElementById("stepSuccess");
  const successRefId = document.getElementById("successRefId");
  const btnDone = document.getElementById("btnDone");

  // Tabs
  const tabVoice = document.getElementById("tabVoice");
  const tabText = document.getElementById("tabText");
  const paneVoice = document.getElementById("paneVoice");

  // Recorder Elements
  const micRecordBtn = document.getElementById("micRecordBtn");
  const recordStatus = document.getElementById("recordStatus");
  const recordTimer = document.getElementById("recordTimer");
  const audioControls = document.getElementById("audioControls");
  const stopRecordBtn = document.getElementById("stopRecordBtn");
  const cancelRecordBtn = document.getElementById("cancelRecordBtn");
  const retryRecordBtn = document.getElementById("retryRecordBtn");
  const rawDescriptionInput = document.getElementById("rawDescriptionInput");
  const aiExtractBtn = document.getElementById("aiExtractBtn");

  // Review Elements
  const aiFollowupBox = document.getElementById("aiFollowupBox");
  const aiFollowupText = document.getElementById("aiFollowupText");
  const followupAnswerInput = document.getElementById("followupAnswerInput");
  const playTTSBtn = document.getElementById("playTTSBtn");
  const fieldReportType = document.getElementById("fieldReportType");
  const fieldName = document.getElementById("fieldName");
  const fieldCategory = document.getElementById("fieldCategory");
  const fieldColor = document.getElementById("fieldColor");
  const fieldLocation = document.getElementById("fieldLocation");
  const fieldTime = document.getElementById("fieldTime");
  const fieldDescription = document.getElementById("fieldDescription");
  const fieldPrivateDetails = document.getElementById("fieldPrivateDetails");
  const fieldContact = document.getElementById("fieldContact");
  const photoFileInput = document.getElementById("photoFileInput");
  const photoPreviewContainer = document.getElementById("photoPreviewContainer");
  const photoPreviewImg = document.getElementById("photoPreviewImg");
  const btnBackToEdit = document.getElementById("btnBackToEdit");
  const btnConfirmSubmit = document.getElementById("btnConfirmSubmit");

  // Contact Modal
  const contactModal = document.getElementById("contactModal");
  const closeContactModal = document.getElementById("closeContactModal");
  const claimReportId = document.getElementById("claimReportId");
  const claimItemSummary = document.getElementById("claimItemSummary");
  const claimantName = document.getElementById("claimantName");
  const claimantContact = document.getElementById("claimantContact");
  const claimantProof = document.getElementById("claimantProof");
  const claimantMessage = document.getElementById("claimantMessage");
  const btnSubmitClaim = document.getElementById("btnSubmitClaim");

  // --- State Variables ---
  let mediaRecorder = null;
  let audioChunks = [];
  let recordInterval = null;
  let recordSeconds = 0;
  let isRecording = false;
  let recordingMode = "report"; // "report" or "search"
  let uploadedImagePath = null;
  let currentFollowUpQuestion = "";

  // Audio Playback
  const ttsAudio = new Audio();

  // --- Voice Search ---
  voiceSearchBtn.addEventListener("click", () => {
    if (isRecording && recordingMode === "search") {
      stopVoiceRecording();
    } else {
      startVoiceRecording("search");
    }
  });

  // --- Text Search ---
  searchInput.addEventListener("input", () => {
    if (searchInput.value.trim().length > 0) {
      searchClearBtn.style.display = "flex";
    } else {
      searchClearBtn.style.display = "none";
    }
  });

  searchClearBtn.addEventListener("click", () => {
    searchInput.value = "";
    searchClearBtn.style.display = "none";
    resultsSection.style.display = "none";
    resultsList.innerHTML = "";
    searchInput.focus();
  });

  searchSubmitBtn.addEventListener("click", () => {
    performSearch(searchInput.value);
  });

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      performSearch(searchInput.value);
    }
  });

  async function performSearch(query) {
    if (!query || query.trim().length < 2) {
      alert("Please enter at least 2 characters to search.");
      return;
    }

    searchClearBtn.style.display = "flex";
    resultsSection.style.display = "block";
    resultsList.innerHTML = `<div class="empty-state"><div class="loading-spinner"></div> Searching campus database for "${escapeHtml(query.trim())}"...</div>`;

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() })
      });

      const data = await res.json();
      resultsCount.textContent = `${data.count} candidate${data.count === 1 ? '' : 's'} found`;

      if (data.count === 0) {
        resultsList.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🔎</div>
            <h4>No matching items found</h4>
            <p style="margin-top: 6px; font-size: 13px;">
              No current reports match "<em>${escapeHtml(query)}</em>". If you lost or found this item, please file a report using the buttons above.
            </p>
          </div>
        `;
        return;
      }

      renderSearchResults(data.results);
    } catch (err) {
      resultsList.innerHTML = `
        <div class="empty-state" style="color: #ef4444;">
          <h4>Error conducting search</h4>
          <p>${escapeHtml(err.message)}</p>
        </div>
      `;
    }
  }

  function renderSearchResults(items) {
    resultsList.innerHTML = items.map(item => {
      const badgeClass = item.report_type === "lost" ? "badge-lost" : "badge-found";
      const badgeLabel = item.report_type.toUpperCase();
      const reasonsHtml = item.match_reasons && item.match_reasons.length > 0
        ? `<div class="match-evidence"><strong>Match evidence:</strong> ${item.match_reasons.join(" • ")}</div>`
        : "";

      const photoHtml = item.image_path
        ? `<img src="${escapeHtml(item.image_path)}" class="result-photo-thumbnail" alt="${escapeHtml(item.item_name)}" />`
        : "";

      return `
        <div class="result-card">
          <div class="result-header">
            <div class="result-title-group">
              <span class="tag-badge ${badgeClass}">${badgeLabel}</span>
              <span class="ref-id-badge">${escapeHtml(item.id)}</span>
              <h4 class="result-title">${escapeHtml(item.item_name)}</h4>
            </div>
            <div class="match-score-pill">${item.match_score}% Match</div>
          </div>

          ${photoHtml}

          <p class="result-desc">${escapeHtml(item.description)}</p>

          <div class="result-meta-grid">
            <div class="meta-item"><strong>Location:</strong> ${escapeHtml(item.location || 'Campus')}</div>
            <div class="meta-item"><strong>Approx Time:</strong> ${escapeHtml(item.approximate_time || 'Recent')}</div>
            <div class="meta-item"><strong>Category:</strong> ${escapeHtml(item.category)}</div>
            ${item.color ? `<div class="meta-item"><strong>Color:</strong> ${escapeHtml(item.color)}</div>` : ''}
          </div>

          ${reasonsHtml}

          <div class="result-actions">
            <button class="btn-claim" onclick="openClaimModal('${item.id}', '${escapeJs(item.item_name)}', '${escapeJs(item.location)}')">
              🤝 Claim / Contact Finder
            </button>
          </div>
        </div>
      `;
    }).join("");
  }

  // --- Report Wizard Modal Opening ---
  openReportLostBtn.addEventListener("click", () => {
    openModalForReport("lost");
  });

  openReportFoundBtn.addEventListener("click", () => {
    openModalForReport("found");
  });

  closeReportModal.addEventListener("click", () => {
    reportModal.classList.remove("active");
    stopVoiceRecording();
  });

  function openModalForReport(type) {
    fieldReportType.value = type;
    modalTitle.textContent = type === "lost" ? "Report a Lost Item" : "Report a Found Item";
    stepInput.style.display = "block";
    stepReview.style.display = "none";
    stepSuccess.style.display = "none";
    rawDescriptionInput.value = "";
    recordStatus.textContent = "Tap the mic to start recording";
    recordTimer.textContent = "Supports English, Hindi, and Hinglish";
    if (retryRecordBtn) retryRecordBtn.style.display = "none";
    audioControls.style.display = "none";
    reportModal.classList.add("active");
  }

  // Tabs for Voice vs Text
  tabVoice.addEventListener("click", () => {
    paneVoice.style.display = "block";
    tabVoice.style.background = "#eff6ff";
    tabVoice.style.color = "#1d4ed8";
    tabVoice.style.borderColor = "#bfdbfe";
    tabText.style.background = "#f1f5f9";
    tabText.style.color = "#334155";
    tabText.style.borderColor = "var(--border-color)";
  });

  tabText.addEventListener("click", () => {
    paneVoice.style.display = "none";
    tabText.style.background = "#eff6ff";
    tabText.style.color = "#1d4ed8";
    tabText.style.borderColor = "#bfdbfe";
    tabVoice.style.background = "#f1f5f9";
    tabVoice.style.color = "#334155";
    tabVoice.style.borderColor = "var(--border-color)";
    rawDescriptionInput.focus();
  });

  // --- Voice Recording via MediaRecorder ---
  micRecordBtn.addEventListener("click", () => {
    if (isRecording) {
      stopVoiceRecording();
    } else {
      startVoiceRecording("report");
    }
  });

  stopRecordBtn.addEventListener("click", () => {
    stopVoiceRecording();
  });

  cancelRecordBtn.addEventListener("click", () => {
    cancelVoiceRecording();
  });

  retryRecordBtn.addEventListener("click", () => {
    retryRecordBtn.style.display = "none";
    startVoiceRecording("report");
  });

  async function startVoiceRecording(mode = "report") {
    recordingMode = mode;
    retryRecordBtn.style.display = "none";
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      recordSeconds = 0;

      // Prefer audio/webm if supported, fallback to wav
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : (MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "");

      mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
        await handleAudioRecorded(audioBlob);
      };

      mediaRecorder.start();
      isRecording = true;

      if (mode === "search") {
        voiceSearchBtn.classList.add("recording");
        voiceSearchStatus.style.display = "block";
      } else {
        micRecordBtn.classList.add("recording");
        recordStatus.textContent = "Listening... Speak naturally in English, Hindi, or Hinglish";
        audioControls.style.display = "flex";
      }

      recordInterval = setInterval(() => {
        recordSeconds++;
        const mins = String(Math.floor(recordSeconds / 60)).padStart(2, '0');
        const secs = String(recordSeconds % 60).padStart(2, '0');
        if (mode === "report") {
          recordTimer.textContent = `Recording: ${mins}:${secs} (Tap Stop when done)`;
        }
      }, 1000);

    } catch (err) {
      alert("Microphone access was denied or not available: " + err.message);
    }
  }

  function stopVoiceRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      clearInterval(recordInterval);
      if (recordingMode === "search") {
        voiceSearchBtn.classList.remove("recording");
        voiceSearchStatus.textContent = "⚡ Transcribing with Sarvam Saaras STT...";
      } else {
        micRecordBtn.classList.remove("recording");
        recordStatus.textContent = "⚡ Transcribing audio with Sarvam Saaras STT...";
        audioControls.style.display = "none";
      }
    }
  }

  function cancelVoiceRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      clearInterval(recordInterval);
      audioChunks = [];
      micRecordBtn.classList.remove("recording");
      recordStatus.textContent = "Recording cancelled.";
      audioControls.style.display = "none";
    }
  }

  async function handleAudioRecorded(blob) {
    if (blob.size < 500) {
      alert("No audio was recorded. Please try speaking into your microphone.");
      return;
    }

    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");

    try {
      const res = await fetch("/api/sarvam/transcribe", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Transcription error");

      const transcript = data.transcript ? data.transcript.trim() : "";
      if (recordingMode === "search") {
        voiceSearchStatus.style.display = "none";
        if (!transcript) {
          alert("No speech detected in your audio. Please speak clearly into your microphone or type your search.");
          return;
        }
        searchInput.value = transcript;
        performSearch(transcript);
      } else {
        if (!transcript) {
          recordStatus.textContent = "No speech detected in audio. Tap mic to retry or type below.";
          retryRecordBtn.style.display = "block";
          return;
        }
        rawDescriptionInput.value = transcript;
        recordStatus.textContent = `✅ Transcribed: "${transcript}"`;
        recordTimer.textContent = `Language: ${data.language_code || 'Auto-detected'} • Edit below if needed`;
        retryRecordBtn.style.display = "block";
      }
    } catch (err) {
      alert("Failed to transcribe audio with Saaras: " + err.message);
      if (recordingMode === "search") {
        voiceSearchStatus.style.display = "none";
      } else {
        recordStatus.textContent = "Transcription error. You can still type your description below.";
        retryRecordBtn.style.display = "block";
      }
    }
  }

  // --- Sarvam AI Reasoning Extraction ---
  aiExtractBtn.addEventListener("click", async () => {
    const text = rawDescriptionInput.value.trim();
    if (!text) {
      alert("Please provide a description (either by speaking or typing) before extracting.");
      return;
    }

    aiExtractBtn.disabled = true;
    aiExtractBtn.innerHTML = `<span class="loading-spinner"></span> Extracting with Sarvam Reasoning AI...`;

    try {
      const res = await fetch("/api/sarvam/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      const result = await res.json();
      const extracted = result.data || {};

      // Populate review fields
      if (extracted.reportType) fieldReportType.value = extracted.reportType;
      fieldName.value = extracted.itemName || "";
      if (extracted.category) fieldCategory.value = extracted.category;
      fieldColor.value = extracted.color || "";
      fieldLocation.value = extracted.location || "";
      fieldTime.value = extracted.approximateTime || "";
      fieldDescription.value = extracted.description || text;
      fieldPrivateDetails.value = extracted.identifiableAttributes || "";

      // Check for follow-up clarification question
      currentFollowUpQuestion = extracted.followUpQuestion || "";
      if (currentFollowUpQuestion && currentFollowUpQuestion.trim().length > 5) {
        aiFollowupText.textContent = currentFollowUpQuestion;
        aiFollowupBox.style.display = "block";
      } else {
        aiFollowupBox.style.display = "none";
      }

      // Switch to Step 2 Review
      stepInput.style.display = "none";
      stepReview.style.display = "block";

    } catch (err) {
      alert("Could not extract with Sarvam AI: " + err.message);
      // Fallback: copy raw text to description and let user fill form
      fieldDescription.value = text;
      stepInput.style.display = "none";
      stepReview.style.display = "block";
    } finally {
      aiExtractBtn.disabled = false;
      aiExtractBtn.textContent = "✨ Extract Details with Sarvam AI";
    }
  });

  // TTS audio playback for clarification
  playTTSBtn.addEventListener("click", async () => {
    if (!currentFollowUpQuestion) return;
    playTTSBtn.textContent = "⏳ Generating...";
    playTTSBtn.disabled = true;

    try {
      const res = await fetch("/api/sarvam/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: currentFollowUpQuestion, language_code: "en-IN" })
      });

      const data = await res.json();
      if (data.audio_base64) {
        ttsAudio.src = "data:audio/wav;base64," + data.audio_base64;
        ttsAudio.play();
        playTTSBtn.textContent = "🔊 Playing";
        ttsAudio.onended = () => {
          playTTSBtn.textContent = "🔊 Listen";
          playTTSBtn.disabled = false;
        };
      }
    } catch (err) {
      alert("TTS playback failed: " + err.message);
      playTTSBtn.textContent = "🔊 Listen";
      playTTSBtn.disabled = false;
    }
  });

  btnBackToEdit.addEventListener("click", () => {
    stepReview.style.display = "none";
    stepInput.style.display = "block";
  });

  // Image Upload Handling
  photoFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch("/api/upload-image", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Image upload failed");

      uploadedImagePath = data.image_path;
      photoPreviewImg.src = uploadedImagePath;
      photoPreviewContainer.style.display = "block";
    } catch (err) {
      alert("Image upload error: " + err.message);
    }
  });

  // --- Final Explicit User Confirmation & Publish ---
  btnConfirmSubmit.addEventListener("click", async () => {
    const itemNameVal = fieldName.value.trim();
    const locationVal = fieldLocation.value.trim();
    const descVal = fieldDescription.value.trim();
    const contactVal = fieldContact.value.trim();

    if (!itemNameVal || !locationVal || !descVal || !contactVal) {
      alert("Please fill in all required fields (Item Name, Campus Location, Description, and Contact).");
      return;
    }

    // Append clarification answer to description if provided
    let finalDesc = descVal;
    const answer = followupAnswerInput.value.trim();
    if (answer) {
      finalDesc += ` (Clarification: ${answer})`;
    }

    const payload = {
      report_type: fieldReportType.value,
      item_name: itemNameVal,
      category: fieldCategory.value,
      color: fieldColor.value.trim(),
      description: finalDesc,
      location: locationVal,
      approximate_time: fieldTime.value.trim(),
      image_path: uploadedImagePath,
      private_verification_details: fieldPrivateDetails.value.trim(),
      reporter_contact: contactVal,
      reporter_name: "Verified Student"
    };

    btnConfirmSubmit.disabled = true;
    btnConfirmSubmit.innerHTML = `<span class="loading-spinner"></span> Saving Report...`;

    try {
      const res = await fetch("/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Submission failed");

      successRefId.textContent = data.report_id;
      stepReview.style.display = "none";
      stepSuccess.style.display = "block";

    } catch (err) {
      alert("Error saving report: " + err.message);
    } finally {
      btnConfirmSubmit.disabled = false;
      btnConfirmSubmit.textContent = "✅ Confirm & Publish Report";
    }
  });

  btnDone.addEventListener("click", () => {
    reportModal.classList.remove("active");
  });

  // --- Safe Contact Request Modal ---
  window.openClaimModal = function(id, name, location) {
    claimReportId.value = id;
    claimItemSummary.textContent = `${name} (Found/Lost at: ${location}) [ID: ${id}]`;
    claimantName.value = "";
    claimantContact.value = "";
    claimantProof.value = "";
    claimantMessage.value = "";
    contactModal.classList.add("active");
  };

  closeContactModal.addEventListener("click", () => {
    contactModal.classList.remove("active");
  });

  // Close modals when clicking backdrop
  window.addEventListener("click", (e) => {
    if (e.target === reportModal) {
      reportModal.classList.remove("active");
      stopVoiceRecording();
    }
    if (e.target === contactModal) {
      contactModal.classList.remove("active");
    }
  });

  btnSubmitClaim.addEventListener("click", async () => {
    const reportId = claimReportId.value;
    const name = claimantName.value.trim();
    const contact = claimantContact.value.trim();
    const proof = claimantProof.value.trim();
    const msg = claimantMessage.value.trim();

    if (!name || !contact || !proof) {
      alert("Please enter your name, contact information, and specific proof of ownership.");
      return;
    }

    btnSubmitClaim.disabled = true;
    btnSubmitClaim.textContent = "Submitting claim...";

    try {
      const res = await fetch("/api/contact-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_id: reportId,
          requester_name: name,
          requester_contact: contact,
          claim_verification_proof: proof,
          message: msg
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Claim request failed");

      alert("✅ Verification Claim Submitted!\nYour ownership details have been securely transmitted to the item custodian. They will reach out to you once verified.");
      contactModal.classList.remove("active");
    } catch (err) {
      alert("Error submitting claim: " + err.message);
    } finally {
      btnSubmitClaim.disabled = false;
      btnSubmitClaim.textContent = "Submit Verification Claim";
    }
  });

  // Utilities
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeJs(str) {
    if (!str) return "";
    return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
  }
});

