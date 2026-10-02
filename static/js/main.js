/**
 * ComicCraft - Client-Side Interactive Scripts
 * Handles prompt chips, live creation loaders, and PDF download triggers
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Handle Prompt Inspiration Chips
  const promptChips = document.querySelectorAll('.chip-btn');
  const storyPromptInput = document.getElementById('story_prompt');
  const characterNameInput = document.getElementById('character_name');

  promptChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const promptText = chip.getAttribute('data-prompt');
      const charName = chip.getAttribute('data-char');
      const settingVal = chip.getAttribute('data-setting');
      const toneVal = chip.getAttribute('data-tone');
      const styleVal = chip.getAttribute('data-style');

      if (promptText && storyPromptInput) {
        storyPromptInput.value = promptText;
        storyPromptInput.focus();
      }
      if (charName && characterNameInput) {
        characterNameInput.value = charName;
      }
      if (settingVal) {
        const radio = document.querySelector(`input[name="setting"][value="${settingVal}"]`);
        if (radio) radio.checked = true;
      }
      if (toneVal) {
        const radio = document.querySelector(`input[name="tone"][value="${toneVal}"]`);
        if (radio) radio.checked = true;
      }
      if (styleVal) {
        const radio = document.querySelector(`input[name="art_style"][value="${styleVal}"]`);
        if (radio) radio.checked = true;
      }
    });
  });

  // 2. Handle Comic Generation Loading Overlay
  const comicForm = document.getElementById('comicForm');
  const loadingOverlay = document.getElementById('loadingOverlay');
  const stepTitle = document.getElementById('loadingStepTitle');
  const stepDesc = document.getElementById('loadingStepDesc');
  const progressFill = document.getElementById('loadingProgressFill');

  if (comicForm && loadingOverlay) {
    comicForm.addEventListener('submit', () => {
      loadingOverlay.classList.add('active');
      simulateGenerationProgress();
    });
  }

  function simulateGenerationProgress() {
    const steps = [
      { pct: 15, title: "1. Brainstorming Story Arc", desc: "Gemini Flash is structuring a 5-panel narrative arc..." },
      { pct: 35, title: "2. Scripting Narration & Dialogues", desc: "Gemini Pro is composing character voice and scene captions..." },
      { pct: 65, title: "3. Illustrating Comic Panels", desc: "Rendering vivid comic-style illustrations for each scene..." },
      { pct: 85, title: "4. Assembling Comic Layout", desc: "Binding panels, speech bubbles, and captions..." },
      { pct: 95, title: "5. Compiling Printable PDF", desc: "Generating high-resolution multi-page PDF document..." }
    ];

    let current = 0;
    const interval = setInterval(() => {
      current++;
      if (current < steps.length) {
        const s = steps[current];
        if (progressFill) progressFill.style.width = `${s.pct}%`;
        if (stepTitle) stepTitle.textContent = s.title;
        if (stepDesc) stepDesc.textContent = s.desc;

        // Highlight checklist
        const items = document.querySelectorAll('.step-checklist li');
        items.forEach((item, idx) => {
          if (idx < current) {
            item.className = 'done';
          } else if (idx === current) {
            item.className = 'active';
          }
        });
      } else {
        clearInterval(interval);
      }
    }, 2800);
  }

  // 3. Download & Export Trigger on Comic Preview Page
  const downloadBtn = document.getElementById('downloadComicBtn');
  if (downloadBtn) {
    downloadBtn.addEventListener('click', (e) => {
      const pdfUrl = downloadBtn.getAttribute('data-pdf-url');
      const comicTitle = downloadBtn.getAttribute('data-title') || 'Your Comic';
      const charName = downloadBtn.getAttribute('data-char') || 'Hero';
      
      if (pdfUrl) {
        // Trigger browser download via invisible link
        const a = document.createElement('a');
        a.href = pdfUrl;
        a.download = pdfUrl.split('/').pop() || 'comic.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        // Redirect to export success page after a short moment
        setTimeout(() => {
          const exportUrl = `/export-success?pdf=${encodeURIComponent(pdfUrl)}&title=${encodeURIComponent(comicTitle)}&character=${encodeURIComponent(charName)}`;
          window.location.href = exportUrl;
        }, 1200);
      }
    });
  }
});
