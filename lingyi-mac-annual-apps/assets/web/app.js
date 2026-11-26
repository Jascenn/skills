/**
 * [INPUT]: 加载 ./data/apps-data.json 与 ./poster-renderer.js，绑定 public/index.html 中的全部表单与交互控件
 * [OUTPUT]: 管理应用状态、分类编辑、软件筛选、URL Hash 分享编解码、JSON/CSV/PNG 一键导出
 * [POS]: mac-annual-apps Web 端主控制器
 * [PROTOCOL]: Update this header on change, then check GEMINI.md
 */

import { BUILTIN_BACKDROPS, renderPoster } from './poster-renderer.js';

const STORAGE_KEY = 'mac-annual-apps-state-v1';

const state = {
  meta: null,
  allApps: [],
  appsById: new Map(),
  defaultGroups: [],
  groups: [],
  title: '2026 我的 Mac 常用软件',
  author: 'lingyi',
  subtitle: '',
  fontStyle: 'sans',
  backdropId: 'night-foliage',
  customBackdropUrl: '',
  scrimOpacity: 55,
  backdropBlur: 0,
  rounded: true,
  showBadge: false,
};

const undoStack = [];
let dragPayload = null;

const els = {
  canvas: document.getElementById('posterCanvas'),
  metaSummary: document.getElementById('metaSummary'),
  titleInput: document.getElementById('titleInput'),
  authorInput: document.getElementById('authorInput'),
  subtitleInput: document.getElementById('subtitleInput'),
  fontSelect: document.getElementById('fontSelect'),
  scrimRange: document.getElementById('scrimRange'),
  scrimValue: document.getElementById('scrimValue'),
  blurRange: document.getElementById('blurRange'),
  blurValue: document.getElementById('blurValue'),
  roundedToggle: document.getElementById('roundedToggle'),
  badgeToggle: document.getElementById('badgeToggle'),
  backdropList: document.getElementById('backdropList'),
  bgUploadInput: document.getElementById('bgUploadInput'),
  groupsContainer: document.getElementById('groupsContainer'),
  libraryList: document.getElementById('libraryList'),
  searchInput: document.getElementById('searchInput'),
  libraryFilter: document.getElementById('libraryFilter'),
  selectedCountBadge: document.getElementById('selectedCountBadge'),
  allCountBadge: document.getElementById('allCountBadge'),
  addGroupBtn: document.getElementById('addGroupBtn'),
  undoBtn: document.getElementById('undoBtn'),
  resetDefaultBtn: document.getElementById('resetDefaultBtn'),
  copyPostBtn: document.getElementById('copyPostBtn'),
  copyPngBtn: document.getElementById('copyPngBtn'),
  downloadPngBtn: document.getElementById('downloadPngBtn'),
  exportCsvBtn: document.getElementById('exportCsvBtn'),
  exportJsonBtn: document.getElementById('exportJsonBtn'),
  importJsonInput: document.getElementById('importJsonInput'),
  shareLinkBtn: document.getElementById('shareLinkBtn'),
  toast: document.getElementById('toast'),
};

let toastTimer = null;
function showToast(msg) {
  els.toast.textContent = msg;
  els.toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => els.toast.classList.remove('show'), 2600);
}

function pushUndoSnapshot() {
  undoStack.push(JSON.parse(JSON.stringify(state.groups)));
  if (undoStack.length > 30) undoStack.shift();
  if (els.undoBtn) els.undoBtn.disabled = undoStack.length === 0;
}

function undoLastChange() {
  if (!undoStack.length) return;
  state.groups = undoStack.pop();
  if (els.undoBtn) els.undoBtn.disabled = undoStack.length === 0;
  persistLocalState();
  updateAllViews();
  showToast('已撤销上一步编排');
}

function getSelectedSet() {
  const set = new Set();
  for (const g of state.groups) {
    for (const id of g.appIds) set.add(id);
  }
  return set;
}

function persistLocalState() {
  try {
    const notes = {};
    const customNames = {};
    for (const a of state.allApps) {
      if (a.note && a.note.trim()) notes[a.id] = a.note.trim();
      if (a._origName && a.name !== a._origName) customNames[a.id] = a.name;
    }
    const snapshot = {
      title: state.title,
      author: state.author,
      subtitle: state.subtitle,
      fontStyle: state.fontStyle,
      backdropId: state.backdropId,
      scrimOpacity: state.scrimOpacity,
      backdropBlur: state.backdropBlur,
      rounded: state.rounded,
      showBadge: state.showBadge,
      groups: state.groups,
      notes,
      customNames,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } catch {
    // 忽略隐私模式存储限制
  }
}

function encodeShareHash() {
  const payload = {
    t: state.title,
    a: state.author,
    s: state.subtitle,
    f: state.fontStyle,
    b: state.backdropId,
    o: state.scrimOpacity,
    bl: state.backdropBlur,
    r: state.rounded ? 1 : 0,
    g: state.groups.map((g) => [
      g.name,
      g.appIds.map((id) => {
        const app = state.appsById.get(id);
        return app ? (app.note ? [app.id, app.name, app.note] : [app.id, app.name]) : [id, id];
      }),
    ]),
  };
  const json = JSON.stringify(payload);
  const bytes = new TextEncoder().encode(json);
  let binary = '';
  bytes.forEach((b) => {
    binary += String.fromCharCode(b);
  });
  return '#share=' + btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function tryLoadFromShareHash() {
  if (!location.hash.startsWith('#share=')) return false;
  try {
    let b64 = location.hash.slice(7).replace(/-/g, '+').replace(/_/g, '/');
    while (b64.length % 4) b64 += '=';
    const binary = atob(b64);
    const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    const parsed = JSON.parse(new TextDecoder().decode(bytes));

    state.title = parsed.t || state.title;
    state.author = parsed.a || '';
    state.subtitle = parsed.s || '';
    state.fontStyle = parsed.f || 'sans';
    state.backdropId = parsed.b || 'night-foliage';
    state.scrimOpacity = typeof parsed.o === 'number' ? parsed.o : 55;
    state.backdropBlur = typeof parsed.bl === 'number' ? parsed.bl : 0;
    state.rounded = parsed.r !== 0;

    if (Array.isArray(parsed.g)) {
      state.groups = parsed.g.map(([name, items], idx) => ({
        id: `share-${idx}`,
        name,
        appIds: items.map(([id, appName, appNote]) => {
          if (!state.appsById.has(id)) {
            const stub = {
              id,
              name: appName,
              category: name,
              activeDaysRecent: 0,
              useCount: 0,
              lastUsedDate: '',
              iconUrl: '',
              note: appNote || '',
            };
            state.appsById.set(id, stub);
            state.allApps.push(stub);
          } else if (appNote) {
            state.appsById.get(id).note = appNote;
          }
          return id;
        }),
      }));
    }
    return true;
  } catch {
    return false;
  }
}

function hydrateDataset(data, skipLocalOverride = false) {
  state.meta = data.meta || {};
  state.allApps = Array.isArray(data.allApps) ? data.allApps.map((a) => ({ ...a, _origName: a._origName || a.name })) : [];
  state.appsById = new Map(state.allApps.map((a) => [a.id, a]));
  state.defaultGroups = JSON.parse(JSON.stringify(data.recommendedGroups || []));
  state.groups = JSON.parse(JSON.stringify(state.defaultGroups));
  state.title = state.meta.defaultTitle || state.title;

  if (!skipLocalOverride) {
    const loadedShare = tryLoadFromShareHash();
    if (!loadedShare) {
      try {
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
        if (saved && Array.isArray(saved.groups)) {
          const validGroups = saved.groups
            .map((g) => ({
              ...g,
              appIds: (g.appIds || []).filter((id) => state.appsById.has(id)),
            }))
            .filter((g) => g.appIds.length > 0);
          if (validGroups.length > 0) {
            state.groups = validGroups;
            state.title = saved.title ?? state.title;
            state.author = saved.author ?? state.author;
            state.subtitle = saved.subtitle ?? state.subtitle;
            state.fontStyle = saved.fontStyle ?? state.fontStyle;
            state.backdropId = saved.backdropId ?? state.backdropId;
            state.scrimOpacity = saved.scrimOpacity ?? state.scrimOpacity;
            state.backdropBlur = saved.backdropBlur ?? state.backdropBlur;
            state.rounded = saved.rounded ?? state.rounded;
            state.showBadge = saved.showBadge ?? state.showBadge;
            if (saved.notes && typeof saved.notes === 'object') {
              for (const [id, noteVal] of Object.entries(saved.notes)) {
                const targetApp = state.appsById.get(id);
                if (targetApp) targetApp.note = String(noteVal || '');
              }
            }
            if (saved.customNames && typeof saved.customNames === 'object') {
              for (const [id, nameVal] of Object.entries(saved.customNames)) {
                const targetApp = state.appsById.get(id);
                if (targetApp && String(nameVal || '').trim()) {
                  targetApp.name = String(nameVal).trim();
                }
              }
            }
          }
        }
      } catch {
        // 使用默认推荐
      }
    }
  }

  syncInputsFromState();
  updateAllViews();
}

function syncBlurControlState() {
  if (!els.blurRange || !els.blurValue) return;
  const activeBg = BUILTIN_BACKDROPS.find((b) => b.id === state.backdropId);
  const isImageBackdrop = Boolean(state.customBackdropUrl) || activeBg?.type === 'image';
  els.blurRange.disabled = !isImageBackdrop;
  els.blurRange.title = isImageBackdrop ? '调整照片背景高斯模糊度' : '仅对照片类背景生效';
  els.blurValue.textContent = isImageBackdrop ? `${state.backdropBlur}px` : '仅照片';
}

function syncInputsFromState() {
  els.titleInput.value = state.title;
  if (els.authorInput) els.authorInput.value = state.author;
  els.subtitleInput.value = state.subtitle;
  els.fontSelect.value = state.fontStyle;
  els.scrimRange.value = String(state.scrimOpacity);
  els.scrimValue.textContent = `${state.scrimOpacity}%`;
  if (els.blurRange && els.blurValue) {
    els.blurRange.value = String(state.backdropBlur);
    syncBlurControlState();
  }
  els.roundedToggle.checked = state.rounded;
  els.badgeToggle.checked = state.showBadge;

  const total = state.meta?.totalInstalled ?? state.allApps.length;
  const active = state.meta?.activeRecentCount ?? 0;
  const days = state.meta?.windowDays ?? 365;
  const rawSource = state.meta?.usageSourceLabel || 'Spotlight 活跃天数';
  const shortSource = rawSource.split(/[（(]/)[0].trim();
  els.metaSummary.textContent = `已扫描 ${total} 款 · 近 ${days} 天活跃 ${active} 款 · 数据源：${shortSource}`;
  els.metaSummary.title = rawSource;
}

function renderBackdropChips() {
  els.backdropList.innerHTML = '';
  for (const bg of BUILTIN_BACKDROPS) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `backdrop-chip${!state.customBackdropUrl && state.backdropId === bg.id ? ' active' : ''}`;
    btn.innerHTML = `<span class="backdrop-swatch" style="background:${bg.swatch}"></span><span>${bg.name}</span>`;
    btn.addEventListener('click', () => {
      state.backdropId = bg.id;
      state.customBackdropUrl = '';
      persistLocalState();
      syncBlurControlState();
      renderBackdropChips();
      redrawCanvas();
    });
    els.backdropList.appendChild(btn);
  }
}

function renderGroupsEditor() {
  els.groupsContainer.innerHTML = '';
  const selectedSet = getSelectedSet();
  els.selectedCountBadge.textContent = String(selectedSet.size);
  els.allCountBadge.textContent = String(state.allApps.length);

  state.groups.forEach((group, gIdx) => {
    const card = document.createElement('div');
    card.className = 'group-card';
    card.addEventListener('dragover', (e) => {
      if (!dragPayload) return;
      e.preventDefault();
      card.classList.add('drag-over');
    });
    card.addEventListener('dragleave', (e) => {
      if (!card.contains(e.relatedTarget)) card.classList.remove('drag-over');
    });
    card.addEventListener('drop', (e) => {
      if (!dragPayload) return;
      e.preventDefault();
      card.classList.remove('drag-over');
      const { fromGroupIdx, fromAppIdx } = dragPayload;
      dragPayload = null;
      if (fromGroupIdx === gIdx) return;
      pushUndoSnapshot();
      const [movedId] = state.groups[fromGroupIdx].appIds.splice(fromAppIdx, 1);
      if (movedId) state.groups[gIdx].appIds.push(movedId);
      persistLocalState();
      updateAllViews();
    });

    const header = document.createElement('div');
    header.className = 'group-header';

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'group-name-input';
    nameInput.value = group.name;
    nameInput.addEventListener('input', (e) => {
      group.name = e.target.value;
      persistLocalState();
      redrawCanvas();
    });

    const upBtn = document.createElement('button');
    upBtn.className = 'icon-btn';
    upBtn.title = '上移分类';
    upBtn.textContent = '↑';
    upBtn.disabled = gIdx === 0;
    upBtn.addEventListener('click', () => {
      pushUndoSnapshot();
      [state.groups[gIdx - 1], state.groups[gIdx]] = [state.groups[gIdx], state.groups[gIdx - 1]];
      persistLocalState();
      updateAllViews();
    });

    const downBtn = document.createElement('button');
    downBtn.className = 'icon-btn';
    downBtn.title = '下移分类';
    downBtn.textContent = '↓';
    downBtn.disabled = gIdx === state.groups.length - 1;
    downBtn.addEventListener('click', () => {
      pushUndoSnapshot();
      [state.groups[gIdx + 1], state.groups[gIdx]] = [state.groups[gIdx], state.groups[gIdx + 1]];
      persistLocalState();
      updateAllViews();
    });

    const delBtn = document.createElement('button');
    delBtn.className = 'icon-btn danger';
    delBtn.title = '删除分类';
    delBtn.textContent = '×';
    delBtn.addEventListener('click', () => {
      pushUndoSnapshot();
      state.groups.splice(gIdx, 1);
      persistLocalState();
      updateAllViews();
    });

    header.append(nameInput, upBtn, downBtn, delBtn);
    card.appendChild(header);

    const list = document.createElement('div');
    list.className = 'group-apps';

    group.appIds.forEach((appId, aIdx) => {
      const app = state.appsById.get(appId);
      if (!app) return;

      const row = document.createElement('div');
      row.className = 'group-app-row';
      row.draggable = true;
      row.addEventListener('dragstart', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
          e.preventDefault();
          return;
        }
        dragPayload = { fromGroupIdx: gIdx, fromAppIdx: aIdx };
        row.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', appId);
      });
      row.addEventListener('dragend', () => {
        row.classList.remove('dragging');
        dragPayload = null;
        document.querySelectorAll('.drag-over').forEach((el) => el.classList.remove('drag-over'));
      });
      row.addEventListener('dragover', (e) => {
        if (!dragPayload) return;
        e.preventDefault();
        e.stopPropagation();
        row.classList.add('drag-over');
      });
      row.addEventListener('dragleave', () => row.classList.remove('drag-over'));
      row.addEventListener('drop', (e) => {
        if (!dragPayload) return;
        e.preventDefault();
        e.stopPropagation();
        row.classList.remove('drag-over');
        const { fromGroupIdx, fromAppIdx } = dragPayload;
        dragPayload = null;
        if (fromGroupIdx === gIdx && fromAppIdx === aIdx) return;
        pushUndoSnapshot();
        const [movedId] = state.groups[fromGroupIdx].appIds.splice(fromAppIdx, 1);
        if (movedId) state.groups[gIdx].appIds.splice(aIdx, 0, movedId);
        persistLocalState();
        updateAllViews();
      });

      const img = document.createElement('img');
      img.src = app.iconUrl || '';
      img.alt = app.name;
      img.onerror = () => {
        img.style.visibility = 'hidden';
      };

      const info = document.createElement('div');
      info.className = 'app-info';
      const winDays = state.meta?.windowDays ?? 365;
      const metaText =
        app.usageHours > 0
          ? `使用 ${app.usageHours} 小时 · 活跃 ${app.activeDaysRecent} 天`
          : app.activeDaysRecent > 0
            ? `近${winDays}天活跃 ${app.activeDaysRecent} 天 · ${app.useCount} 次`
            : app.lastUsedDate
              ? `上次使用 ${app.lastUsedDate}`
              : '已安装应用';
      const nameEdit = document.createElement('input');
      nameEdit.type = 'text';
      nameEdit.className = 'app-name-input';
      nameEdit.maxLength = 48;
      nameEdit.value = app.name;
      nameEdit.title = '点击可自定义海报上的显示名称';
      nameEdit.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        app.name = val || app._origName || app.id;
        persistLocalState();
        redrawCanvas();
      });
      nameEdit.addEventListener('blur', (e) => {
        if (!e.target.value.trim()) e.target.value = app.name;
      });
      const metaEl = document.createElement('div');
      metaEl.className = 'app-meta';
      metaEl.textContent = metaText;
      info.append(nameEdit, metaEl);

      const noteInput = document.createElement('input');
      noteInput.type = 'text';
      noteInput.maxLength = 60;
      noteInput.className = 'app-note-input';
      noteInput.placeholder = '一句话推荐理由（可选，60 字内，写入配文与导出）';
      noteInput.value = app.note || '';
      noteInput.addEventListener('input', (e) => {
        app.note = e.target.value;
        persistLocalState();
      });

      const moveSelect = document.createElement('select');
      moveSelect.className = 'move-select';
      moveSelect.title = '移动到其他分类';
      state.groups.forEach((targetG, tIdx) => {
        const opt = document.createElement('option');
        opt.value = String(tIdx);
        opt.textContent = targetG.name;
        if (tIdx === gIdx) opt.selected = true;
        moveSelect.appendChild(opt);
      });
      moveSelect.addEventListener('change', (e) => {
        const targetIdx = Number(e.target.value);
        if (targetIdx === gIdx) return;
        pushUndoSnapshot();
        group.appIds.splice(aIdx, 1);
        state.groups[targetIdx].appIds.push(appId);
        persistLocalState();
        updateAllViews();
      });

      const leftBtn = document.createElement('button');
      leftBtn.className = 'icon-btn';
      leftBtn.title = '前移';
      leftBtn.textContent = '‹';
      leftBtn.disabled = aIdx === 0;
      leftBtn.addEventListener('click', () => {
        pushUndoSnapshot();
        [group.appIds[aIdx - 1], group.appIds[aIdx]] = [group.appIds[aIdx], group.appIds[aIdx - 1]];
        persistLocalState();
        updateAllViews();
      });

      const rightBtn = document.createElement('button');
      rightBtn.className = 'icon-btn';
      rightBtn.title = '后移';
      rightBtn.textContent = '›';
      rightBtn.disabled = aIdx === group.appIds.length - 1;
      rightBtn.addEventListener('click', () => {
        pushUndoSnapshot();
        [group.appIds[aIdx + 1], group.appIds[aIdx]] = [group.appIds[aIdx], group.appIds[aIdx + 1]];
        persistLocalState();
        updateAllViews();
      });

      const removeBtn = document.createElement('button');
      removeBtn.className = 'icon-btn danger';
      removeBtn.title = '移出海报';
      removeBtn.textContent = '−';
      removeBtn.addEventListener('click', () => {
        pushUndoSnapshot();
        group.appIds.splice(aIdx, 1);
        persistLocalState();
        updateAllViews();
      });

      const grip = document.createElement('span');
      grip.className = 'drag-grip';
      grip.title = '拖拽调整顺序或跨分类移动';
      grip.textContent = '⋮⋮';

      const controls = document.createElement('div');
      controls.className = 'app-row-controls';
      controls.append(moveSelect, leftBtn, rightBtn, removeBtn);

      const topRow = document.createElement('div');
      topRow.className = 'app-row-top';
      topRow.append(grip, img, info, controls);

      row.append(topRow, noteInput);
      list.appendChild(row);
    });

    card.appendChild(list);
    els.groupsContainer.appendChild(card);
  });
}

function renderLibrary() {
  const query = (els.searchInput.value || '').trim().toLowerCase();
  const filter = els.libraryFilter.value;
  const selectedSet = getSelectedSet();

  const filtered = state.allApps.filter((app) => {
    if (filter === 'active' && app.activeDaysRecent <= 0) return false;
    if (filter === 'selected' && !selectedSet.has(app.id)) return false;
    if (query) {
      const text = `${app.name} ${app.bundleId || ''} ${app.category || ''}`.toLowerCase();
      return text.includes(query);
    }
    return true;
  });

  els.libraryList.innerHTML = '';
  const fragment = document.createDocumentFragment();

  filtered.slice(0, 150).forEach((app) => {
    const isSelected = selectedSet.has(app.id);
    const item = document.createElement('div');
    item.className = `library-item${isSelected ? ' selected' : ''}`;

    const img = document.createElement('img');
    img.src = app.iconUrl || '';
    img.alt = app.name;
    img.loading = 'lazy';
    img.onerror = () => {
      img.style.visibility = 'hidden';
    };

    const info = document.createElement('div');
    info.className = 'app-info';
    const stat =
      app.usageHours > 0
        ? `${app.category} · 使用 ${app.usageHours} 小时 / 活跃 ${app.activeDaysRecent} 天`
        : app.activeDaysRecent > 0
          ? `${app.category} · 活跃 ${app.activeDaysRecent} 天 / ${app.useCount} 次`
          : `${app.category} · ${app.lastUsedDate || '近期未打开'}`;
    const nameEl = document.createElement('div');
    nameEl.className = 'app-name';
    nameEl.textContent = app.name;
    const metaEl = document.createElement('div');
    metaEl.className = 'app-meta';
    metaEl.textContent = stat;
    info.append(nameEl, metaEl);

    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = `btn btn-sm ${isSelected ? 'btn-ghost' : 'btn-primary'}`;
    toggleBtn.textContent = isSelected ? '已入选' : '+ 加入';
    toggleBtn.addEventListener('click', () => {
      pushUndoSnapshot();
      if (isSelected) {
        state.groups.forEach((g) => {
          g.appIds = g.appIds.filter((id) => id !== app.id);
        });
      } else {
        let target = state.groups.find((g) => g.name === app.category);
        if (!target) {
          target = state.groups[0];
          if (!target) {
            target = { id: `cat-${Date.now()}`, name: app.category || '常用软件', appIds: [] };
            state.groups.push(target);
          }
        }
        target.appIds.push(app.id);
      }
      persistLocalState();
      updateAllViews();
    });

    item.append(img, info, toggleBtn);
    fragment.appendChild(item);
  });

  if (filtered.length > 150) {
    const moreHint = document.createElement('div');
    moreHint.className = 'library-more-hint';
    moreHint.textContent = `已显示前 150 / ${filtered.length} 款，输入上方关键词可精准筛选`;
    fragment.appendChild(moreHint);
  }

  els.libraryList.appendChild(fragment);
}

let renderSeq = 0;
async function redrawCanvas() {
  const seq = ++renderSeq;
  await renderPoster(els.canvas, state);
  if (seq !== renderSeq) return;
}

function updateAllViews() {
  renderBackdropChips();
  renderGroupsEditor();
  renderLibrary();
  redrawCanvas();
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function bindEvents() {
  // 点击页面空白处或菜单内按钮后自动收起顶部数据下拉菜单
  document.addEventListener('click', (e) => {
    document.querySelectorAll('.action-menu[open]').forEach((menu) => {
      if (!menu.contains(e.target) || e.target.closest('button.menu-item')) {
        menu.removeAttribute('open');
      }
    });
  });

  // Tab 切换
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${btn.dataset.tab}`)?.classList.add('active');
    });
  });

  els.titleInput.addEventListener('input', (e) => {
    state.title = e.target.value;
    persistLocalState();
    redrawCanvas();
  });

  if (els.authorInput) {
    els.authorInput.addEventListener('input', (e) => {
      state.author = e.target.value;
      persistLocalState();
      redrawCanvas();
    });
  }

  els.subtitleInput.addEventListener('input', (e) => {
    state.subtitle = e.target.value;
    persistLocalState();
    redrawCanvas();
  });

  els.fontSelect.addEventListener('change', (e) => {
    state.fontStyle = e.target.value;
    persistLocalState();
    redrawCanvas();
  });

  els.scrimRange.addEventListener('input', (e) => {
    state.scrimOpacity = Number(e.target.value);
    els.scrimValue.textContent = `${state.scrimOpacity}%`;
    persistLocalState();
    redrawCanvas();
  });

  if (els.blurRange && els.blurValue) {
    els.blurRange.addEventListener('input', (e) => {
      state.backdropBlur = Number(e.target.value);
      els.blurValue.textContent = `${state.backdropBlur}px`;
      persistLocalState();
      redrawCanvas();
    });
  }

  els.roundedToggle.addEventListener('change', (e) => {
    state.rounded = e.target.checked;
    persistLocalState();
    redrawCanvas();
  });

  els.badgeToggle.addEventListener('change', (e) => {
    state.showBadge = e.target.checked;
    persistLocalState();
    redrawCanvas();
  });

  els.bgUploadInput.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      state.customBackdropUrl = String(reader.result || '');
      syncBlurControlState();
      renderBackdropChips();
      redrawCanvas();
      showToast('已应用自定义背景图');
    };
    reader.readAsDataURL(file);
  });

  els.addGroupBtn.addEventListener('click', () => {
    pushUndoSnapshot();
    state.groups.push({ id: `cat-${Date.now()}`, name: '自定义分类', appIds: [] });
    persistLocalState();
    updateAllViews();
  });

  if (els.undoBtn) {
    els.undoBtn.addEventListener('click', undoLastChange);
  }

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (undoStack.length > 0) {
        e.preventDefault();
        undoLastChange();
      }
    }
  });

  els.resetDefaultBtn.addEventListener('click', () => {
    pushUndoSnapshot();
    state.groups = JSON.parse(JSON.stringify(state.defaultGroups));
    state.customBackdropUrl = '';
    state.backdropBlur = 0;
    localStorage.removeItem(STORAGE_KEY);
    if (location.hash) history.replaceState(null, '', location.pathname);
    syncInputsFromState();
    updateAllViews();
    const winDays = state.meta?.windowDays ?? 365;
    showToast(`已恢复按近 ${winDays} 天活跃度自动推荐（可点撤销恢复）`);
  });

  els.searchInput.addEventListener('input', renderLibrary);
  els.libraryFilter.addEventListener('change', renderLibrary);

  // 一键复制配文（Markdown / 推文草稿）
  if (els.copyPostBtn) {
    els.copyPostBtn.addEventListener('click', async () => {
      const activeGroups = state.groups.filter((g) => g.appIds.length > 0);
      const totalSelected = activeGroups.reduce((sum, g) => sum + g.appIds.length, 0);
      const lines = [`# ${state.title || '2026 我的 Mac 常用软件'}（共 ${totalSelected} 款）`, ''];
      for (const g of activeGroups) {
        lines.push(`### ${g.name} (${g.appIds.length})`);
        for (const id of g.appIds) {
          const app = state.appsById.get(id);
          if (!app) continue;
          const note = (app.note || '').trim();
          lines.push(note ? `- **${app.name}**：${note}` : `- **${app.name}**`);
        }
        lines.push('');
      }
      if (state.author && state.author.trim()) {
        lines.push(`—— ${state.author.trim()} 的推荐`);
      }
      const text = lines.join('\n').trim();
      try {
        await navigator.clipboard.writeText(text);
        showToast('已复制推文 / Markdown 配文到剪贴板');
      } catch {
        const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
        triggerDownload(blob, 'mac-apps-post.md');
        showToast('剪贴板受限，已改为下载 Markdown 配文');
      }
    });
  }

  // 一键复制 2400x1350 高清海报图片到剪贴板
  if (els.copyPngBtn) {
    els.copyPngBtn.addEventListener('click', async () => {
      await redrawCanvas();
      els.canvas.toBlob(async (blob) => {
        if (!blob) return;
        try {
          if (!navigator.clipboard || typeof ClipboardItem === 'undefined') {
            throw new Error('clipboard unsupported');
          }
          await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
          showToast('已复制高清海报图片，可直接 ⌘V 粘贴');
        } catch {
          showToast('当前浏览器环境不支持复制图片，请点击“下载高清原图”');
        }
      }, 'image/png');
    });
  }

  // 下载 2400x1350 高清原图
  els.downloadPngBtn.addEventListener('click', async () => {
    await redrawCanvas();
    els.canvas.toBlob((blob) => {
      if (!blob) return;
      const safeTitle = (state.title || 'mac-annual-apps').replace(/[\\/:*?"<>|]/g, '-');
      triggerDownload(blob, `${safeTitle}.png`);
      showToast('已导出 2400×1350 高清原图');
    }, 'image/png');
  });

  // 导出 CSV
  els.exportCsvBtn.addEventListener('click', () => {
    const headers = ['name', 'category', 'note', 'usageHours', 'activeDaysRecent', 'activeDaysTotal', 'useCount', 'lastUsedDate', 'bundleId', 'path'];
    const lines = [headers.join(',')];
    for (const app of state.allApps) {
      const row = headers.map((k) => `"${String(app[k] ?? '').replace(/"/g, '""')}"`);
      lines.push(row.join(','));
    }
    const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    triggerDownload(blob, 'mac-apps-usage.csv');
    showToast('已导出全部应用活跃清单 CSV');
  });

  // 导出 JSON 配置
  els.exportJsonBtn.addEventListener('click', () => {
    const out = {
      meta: state.meta,
      recommendedGroups: state.groups,
      allApps: state.allApps,
    };
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
    triggerDownload(blob, 'apps-data.json');
    showToast('已导出配置文件 apps-data.json');
  });

  // 导入 JSON
  els.importJsonInput.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result || '{}'));
        hydrateDataset(parsed, true);
        showToast('已导入新的本机软件清单');
      } catch {
        showToast('JSON 格式解析失败');
      }
    };
    reader.readAsText(file);
  });

  // 复制分享链接
  els.shareLinkBtn.addEventListener('click', async () => {
    const hash = encodeShareHash();
    const shareUrl = `${location.origin}${location.pathname}${hash}`;
    history.replaceState(null, '', hash);
    try {
      await navigator.clipboard.writeText(shareUrl);
      showToast('分享链接已复制到剪贴板');
    } catch {
      showToast('已更新地址栏分享链接，可直接复制');
    }
  });
}

async function init() {
  bindEvents();
  try {
    const res = await fetch('./data/apps-data.json');
    if (!res.ok) throw new Error('load failed');
    const data = await res.json();
    hydrateDataset(data);
  } catch {
    els.metaSummary.textContent = '未检测到默认数据，请点击右上角“导入 JSON”加载本机扫描清单';
    updateAllViews();
  }
}

init();
