const categoryList = document.getElementById("categoryList");
const playerCountInput = document.getElementById("playerCount");
const playerNamesInput = document.getElementById("playerNames");
const seedInput = document.getElementById("seedInput");
const shareCodeInput = document.getElementById("shareCodeInput");
const loadShareCodeBtn = document.getElementById("loadShareCode");
const toneSelect = document.getElementById("toneSelect");
const durationSelect = document.getElementById("durationSelect");
const generateBtn = document.getElementById("generateBtn");
const regenerateBtn = document.getElementById("regenerateBtn");
const exportBtn = document.getElementById("exportBtn");
const copyShareBtn = document.getElementById("copyShareBtn");
const statusEl = document.getElementById("status");
const spinner = document.getElementById("spinner");
const resultsSection = document.getElementById("results");
const gameTitleEl = document.getElementById("gameTitle");
const themeSummaryEl = document.getElementById("themeSummary");
const shareCodeDisplay = document.getElementById("shareCodeDisplay");
const copyShareInline = document.getElementById("copyShareInline");
const storylineEl = document.getElementById("storyline");
const timelineEl = document.getElementById("timeline");
const howToPlayEl = document.getElementById("howToPlay");
const propsListEl = document.getElementById("propsList");
const characterSelect = document.getElementById("characterSelect");
const characterPacketEl = document.getElementById("characterPacket");
const hostToggle = document.getElementById("hostToggle");
const hostContent = document.getElementById("hostContent");
const revealSolutionBtn = document.getElementById("revealSolution");
const solutionContent = document.getElementById("solutionContent");
const characterCardsEl = document.getElementById("characterCards");
const hostCardEl = document.getElementById("hostCard");
const backToSetupBtn = document.getElementById("backToSetupBtn");
const regenerateGameBtn = document.getElementById("regenerateGameBtn");
const exportGameBtn = document.getElementById("exportGameBtn");
const copyShareGameBtn = document.getElementById("copyShareGameBtn");
const surpriseMeBtn = document.getElementById("surpriseMe");
const setupModeEl = document.getElementById("setupMode");
const modalOverlay = document.getElementById("modalOverlay");
const modalClose = document.getElementById("modalClose");
const modalBody = document.getElementById("modalBody");

let categories = [];
let selectedCategoryId = null;
let lastRequest = null;
let currentGame = null;
let clueMap = new Map();
let mode = "setup";
let activeModal = null;
let hostRevealConfirmed = false;

function on(el, event, handler) {
  if (!el) {
    console.warn(`Missing element for ${event} handler.`);
    return;
  }
  el.addEventListener(event, handler);
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#b32424" : "#117a37";
}

function setLoading(isLoading) {
  spinner.classList.toggle("hidden", !isLoading);
  generateBtn.disabled = isLoading;
  regenerateBtn.disabled = isLoading || !lastRequest;
}

function base64UrlEncode(obj) {
  const json = JSON.stringify(obj);
  const base64 = btoa(unescape(encodeURIComponent(json)));
  return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlDecode(code) {
  const padded = code + "===".slice((code.length + 3) % 4);
  const base64 = padded.replace(/-/g, "+").replace(/_/g, "/");
  const json = decodeURIComponent(escape(atob(base64)));
  return JSON.parse(json);
}

async function fetchCategories() {
  const response = await fetch("/api/categories");
  categories = await response.json();
  renderCategories();
}

function renderCategories() {
  categoryList.innerHTML = "";
  categories.forEach((category) => {
    const card = document.createElement("div");
    card.className = "category";
    if (category.id === selectedCategoryId) {
      card.classList.add("selected");
    }
    card.innerHTML = `
      <h4>${category.name}</h4>
      <p>${category.description}</p>
      <small>${category.tone_tags.join(", ")}</small>
    `;
    card.addEventListener("click", () => {
      selectedCategoryId = category.id;
      renderCategories();
    });
    categoryList.appendChild(card);
  });
}

function gatherRequest() {
  const playerCount = parseInt(playerCountInput.value, 10);
  if (Number.isNaN(playerCount) || playerCount < 4 || playerCount > 20) {
    throw new Error("Player count must be between 4 and 20.");
  }
  const names = playerNamesInput.value
    .split(",")
    .map((name) => name.trim())
    .filter(Boolean);
  const seedValue = seedInput.value ? parseInt(seedInput.value, 10) : null;
  const payload = {
    player_count: playerCount,
    player_names: names.length ? names : null,
    category_id: selectedCategoryId || "random",
    tone: toneSelect.value,
    duration: parseInt(durationSelect.value, 10),
    seed: seedValue,
  };
  return payload;
}

function renderGame(game) {
  renderGameBoard(game);
}

function renderSetup() {
  mode = "setup";
  setupModeEl.classList.remove("hidden");
  resultsSection.classList.add("hidden");
}

function renderGameBoard(game) {
  mode = "game";
  setupModeEl.classList.add("hidden");
  resultsSection.classList.remove("hidden");
  gameTitleEl.textContent = game.title;
  themeSummaryEl.textContent = game.theme_summary;
  shareCodeDisplay.textContent = game.meta.share_code;
  clueMap = new Map(game.clues.map((clue) => [clue.clue_id, clue]));
  regenerateGameBtn.disabled = !lastRequest;
  exportGameBtn.disabled = !currentGame;
  copyShareGameBtn.disabled = !currentGame;

  storylineEl.innerHTML = game.storyline_overview
    .map((p) => `<p>${p}</p>`)
    .join("");

  timelineEl.innerHTML = game.timeline
    .map((event) => `<li><strong>${event.time}</strong> - ${event.description}</li>`)
    .join("");

  howToPlayEl.innerHTML = game.how_to_play
    .map(
      (round) =>
        `<li><strong>${round.title}</strong> (${round.minutes} min): ${round.description}</li>`
    )
    .join("");

  if (game.props_list && game.props_list.length) {
    propsListEl.innerHTML = game.props_list.map((prop) => `<li>${prop}</li>`).join("");
    propsListEl.closest(".panel").classList.remove("hidden");
  } else {
    propsListEl.innerHTML = "";
    propsListEl.closest(".panel").classList.add("hidden");
  }

  characterCardsEl.innerHTML = game.character_packets
    .map(
      (character) => `
        <div class="clickable-card" data-character-id="${character.character_id}">
          <h4>${character.name}</h4>
          <p>Click to Reveal</p>
        </div>
      `
    )
    .join("");
  hostRevealConfirmed = false;

  if (characterSelect && characterPacketEl) {
    characterSelect.innerHTML = game.character_packets
      .map((character) => `<option value="${character.character_id}">${character.name}</option>`)
      .join("");
    characterSelect.onchange = () => renderCharacterPacket(game, characterSelect.value);
    renderCharacterPacket(
      game,
      characterSelect.value || game.character_packets[0].character_id
    );
  }
}

function renderClueList(clueIds, clueLookup) {
  if (!clueIds || !clueIds.length) {
    return "<p>No clues assigned.</p>";
  }
  const items = clueIds
    .map((clueId) => {
      const clue = clueLookup.get(clueId);
      if (!clue) {
        return `<li class="clue-card"><strong>${clueId}</strong>: Missing clue details.</li>`;
      }
      return `<li class="clue-card"><strong>${clue.title}</strong>: ${clue.description}</li>`;
    })
    .join("");
  return `<ul class="clue-list">${items}</ul>`;
}

function renderIntroList(lines) {
  if (!lines || !lines.length) {
    return "<p>No intro monologue provided.</p>";
  }
  const items = lines.map((line) => `<li>${line}</li>`).join("");
  return `<ul class="clue-list">${items}</ul>`;
}

function renderCharacterPacket(game, characterId) {
  if (!characterPacketEl) return;
  const packet = game.character_packets.find(
    (character) => character.character_id === characterId
  );
  if (!packet) return;
  characterPacketEl.innerHTML = `
    <h4>${packet.name} (${packet.role_title})</h4>
    <p>${packet.backstory}</p>
    <p><strong>Traits:</strong> ${packet.traits.join(", ")}</p>
    <p><strong>Public goal:</strong> ${packet.public_goal}</p>
    <p><strong>Secret goal:</strong> ${packet.secret_goal}</p>
    <p><strong>Secrets:</strong> ${packet.secrets.join("; ")}</p>
    <p><strong>Alibi:</strong> ${packet.alibi}</p>
    <p><strong>Connection to victim:</strong> ${packet.connection_to_victim}</p>
    <div><strong>Clues:</strong> ${renderClueList(packet.clue_ids, clueMap)}</div>
    <div><strong>Intro:</strong> ${renderIntroList(packet.intro_monologue)}</div>
  `;
}

function renderSolution(game) {
  const murderer = game.character_packets.find(
    (character) => character.character_id === game.solution.murderer_id
  );
  return `
    <div class="modal-section">
      <p><strong>Murderer:</strong> ${murderer ? murderer.name : game.solution.murderer_id}</p>
      <p><strong>Motive:</strong> ${game.solution.motive}</p>
      <p><strong>Method:</strong> ${game.solution.method}</p>
      <p><strong>Opportunity:</strong> ${game.solution.opportunity}</p>
      <p>${game.solution.reveal_explanation}</p>
    </div>
  `;
}

function renderCharacterModal(character) {
  modalBody.innerHTML = `
    <h3>${character.name} (${character.role_title})</h3>
    <div class="modal-section"><p>${character.backstory}</p></div>
    <div class="modal-section"><strong>Traits:</strong> ${character.traits.join(", ")}</div>
    <div class="modal-section"><strong>Public goal:</strong> ${character.public_goal}</div>
    <div class="modal-section"><strong>Secret goal:</strong> ${character.secret_goal}</div>
    <div class="modal-section"><strong>Secrets:</strong> ${character.secrets.join("; ")}</div>
    <div class="modal-section"><strong>Alibi:</strong> ${character.alibi}</div>
    <div class="modal-section"><strong>Connection to victim:</strong> ${character.connection_to_victim}</div>
    <div class="modal-section"><strong>Clues:</strong> ${renderClueList(character.clue_ids, clueMap)}</div>
    <div class="modal-section"><strong>Intro:</strong> ${renderIntroList(character.intro_monologue)}</div>
  `;
}

function renderHostModal(game) {
  const revealSection = hostRevealConfirmed
    ? renderSolution(game)
    : `
      <div class="modal-section">
        <p>This content is for the host only.</p>
        <label class="modal-section">
          <span style="margin-right: 8px; font-weight: 600;">I am the host and understand this reveals the solution.</span>
          <input type="checkbox" id="hostConfirmCheck" />
        </label>
      </div>
      <div class="modal-actions">
        <button id="hostRevealBtn" class="primary" type="button" disabled>Reveal Solution</button>
      </div>
    `;

  modalBody.innerHTML = `
    <h3>Host View</h3>
    ${revealSection}
  `;

  if (!hostRevealConfirmed) {
    const hostConfirmCheck = document.getElementById("hostConfirmCheck");
    const hostRevealBtn = document.getElementById("hostRevealBtn");
    hostConfirmCheck.addEventListener("change", () => {
      hostRevealBtn.disabled = !hostConfirmCheck.checked;
    });
    hostRevealBtn.addEventListener("click", () => {
      hostRevealConfirmed = true;
      renderHostModal(game);
    });
  }
}

function openModal(type, payload) {
  activeModal = { type, payload };
  modalOverlay.classList.remove("hidden");
  if (type === "character") {
    renderCharacterModal(payload);
  }
  if (type === "host") {
    renderHostModal(payload);
  }
}

function closeModal() {
  modalOverlay.classList.add("hidden");
  activeModal = null;
}

async function generateGame(payload) {
  setLoading(true);
  setStatus("Generating game...", false);
  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Generation failed.");
    }
    const game = await response.json();
    currentGame = game;
    lastRequest = payload;
    localStorage.setItem("mp1_last_game", JSON.stringify(game));
    exportBtn.disabled = false;
    copyShareBtn.disabled = false;
    regenerateBtn.disabled = false;
    renderGame(game);
    setStatus("Game generated successfully.", false);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setLoading(false);
  }
}

on(generateBtn, "click", async () => {
  try {
    const payload = gatherRequest();
    await generateGame(payload);
  } catch (error) {
    setStatus(error.message, true);
  }
});

on(regenerateBtn, "click", async () => {
  if (lastRequest) {
    await generateGame(lastRequest);
  }
});

on(exportBtn, "click", () => {
  if (!currentGame) return;
  const blob = new Blob([JSON.stringify(currentGame, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "murder_mystery_game.json";
  link.click();
  URL.revokeObjectURL(url);
});

on(copyShareBtn, "click", async () => {
  if (!currentGame) return;
  await navigator.clipboard.writeText(currentGame.meta.share_code);
  setStatus("Share code copied to clipboard.", false);
});

on(copyShareInline, "click", async () => {
  if (!currentGame) return;
  await navigator.clipboard.writeText(currentGame.meta.share_code);
  setStatus("Share code copied to clipboard.", false);
});

on(loadShareCodeBtn, "click", () => {
  if (!shareCodeInput.value.trim()) return;
  try {
    const data = base64UrlDecode(shareCodeInput.value.trim());
    seedInput.value = data.seed;
    playerCountInput.value = data.player_count;
    toneSelect.value = data.tone;
    durationSelect.value = data.duration;
    selectedCategoryId = data.category_id;
    renderCategories();
    setStatus("Share code loaded. Click Generate to recreate.", false);
  } catch (error) {
    setStatus("Invalid share code.", true);
  }
});

on(hostToggle, "click", () => {
  if (hostContent.classList.contains("hidden")) {
    const confirmed = window.confirm("Host view reveals the solution. Continue?");
    if (!confirmed) return;
    hostContent.classList.remove("hidden");
    hostToggle.textContent = "Hide host view";
  } else {
    hostContent.classList.add("hidden");
    hostToggle.textContent = "I am the host";
  }
});

on(revealSolutionBtn, "click", () => {
  const confirmed = window.confirm("Reveal the solution to all players?");
  if (!confirmed) return;
  solutionContent.classList.remove("hidden");
  renderSolution(currentGame);
});

on(surpriseMeBtn, "click", () => {
  selectedCategoryId = "random";
  categoryList.querySelectorAll(".category").forEach((card) => card.classList.remove("selected"));
  setStatus("Surprise Me selected.", false);
});

function hydrateFromStorage() {
  const saved = localStorage.getItem("mp1_last_game");
  if (!saved) return;
  try {
    const game = JSON.parse(saved);
    currentGame = game;
    renderGame(game);
    exportBtn.disabled = false;
    copyShareBtn.disabled = false;
    setStatus("Loaded last generated game from storage.", false);
  } catch (error) {
    localStorage.removeItem("mp1_last_game");
  }
}

fetchCategories()
  .then(() => hydrateFromStorage())
  .catch(() => setStatus("Failed to load categories.", true));

on(backToSetupBtn, "click", () => {
  renderSetup();
});

on(regenerateGameBtn, "click", async () => {
  if (lastRequest) {
    await generateGame(lastRequest);
  }
});

on(exportGameBtn, "click", () => {
  exportBtn.click();
});

on(copyShareGameBtn, "click", () => {
  copyShareBtn.click();
});

on(characterCardsEl, "click", (event) => {
  const card = event.target.closest("[data-character-id]");
  if (!card || !currentGame) return;
  const character = currentGame.character_packets.find(
    (packet) => packet.character_id === card.dataset.characterId
  );
  if (character) {
    openModal("character", character);
  }
});

on(hostCardEl, "click", () => {
  if (!currentGame) return;
  openModal("host", currentGame);
});

on(modalClose, "click", closeModal);
on(modalOverlay, "click", (event) => {
  if (event.target === modalOverlay) {
    closeModal();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && modalOverlay && !modalOverlay.classList.contains("hidden")) {
    closeModal();
  }
});
