/**
 * [INPUT]: 接收 HTMLCanvasElement、海报状态对象（title, subtitle, fontStyle, scrimOpacity, rounded, showBadge, groups, appsById）与背景配置
 * [OUTPUT]: 导出 BUILTIN_BACKDROPS 常量与 renderPoster 异步渲染函数，在 2400x1350 画布上绘制高清年度软件海报
 * [POS]: mac-annual-apps Web 端纯渲染引擎，与 DOM 交互解耦，供 app.js 实时预览与 PNG 导出复用
 * [PROTOCOL]: Update this header on change, then check GEMINI.md
 */

export const CANVAS_WIDTH = 2400;
export const CANVAS_HEIGHT = 1350;

export const BUILTIN_BACKDROPS = [
  {
    id: 'night-foliage',
    name: '夜色暖光树影',
    type: 'image',
    src: './backgrounds/night-foliage.jpg',
    swatch: 'url(./backgrounds/night-foliage.jpg)',
  },
  {
    id: 'sunset-bridge',
    name: '落日暮海',
    type: 'gradient',
    stops: [
      { pos: 0, color: '#0d1526' },
      { pos: 0.45, color: '#272c48' },
      { pos: 0.78, color: '#6b3e3e' },
      { pos: 1, color: '#b45c36' },
    ],
    glow: { x: 0.78, y: 0.42, r: 0.55, color: 'rgba(255, 166, 84, 0.34)' },
    swatch: 'linear-gradient(135deg, #161d34, #8b4639, #d98245)',
  },
  {
    id: 'alpine-twilight',
    name: '极夜冷蓝',
    type: 'gradient',
    stops: [
      { pos: 0, color: '#070b14' },
      { pos: 0.52, color: '#0f1c2e' },
      { pos: 0.85, color: '#1b344d' },
      { pos: 1, color: '#2f4e63' },
    ],
    glow: { x: 0.82, y: 0.28, r: 0.52, color: 'rgba(120, 195, 255, 0.22)' },
    swatch: 'linear-gradient(135deg, #070b14, #173049, #3b6982)',
  },
  {
    id: 'deep-teal',
    name: '深青极简',
    type: 'gradient',
    stops: [
      { pos: 0, color: '#0e2533' },
      { pos: 0.55, color: '#203941' },
      { pos: 1, color: '#324f4b' },
    ],
    glow: { x: 0.78, y: 0.25, r: 0.55, color: 'rgba(130, 210, 195, 0.14)' },
    swatch: 'linear-gradient(135deg, #0e2533, #203941, #324f4b)',
  },
  {
    id: 'obsidian-minimal',
    name: '纯黑极简',
    type: 'gradient',
    stops: [
      { pos: 0, color: '#08090c' },
      { pos: 0.65, color: '#111319' },
      { pos: 1, color: '#1a1e28' },
    ],
    glow: { x: 0.8, y: 0.2, r: 0.48, color: 'rgba(255, 255, 255, 0.06)' },
    swatch: 'linear-gradient(135deg, #08090c, #1c202b)',
  },
];

const imageCache = new Map();

function loadImage(src) {
  if (!src) return Promise.resolve(null);
  if (imageCache.has(src)) return imageCache.get(src);

  const promise = new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });

  imageCache.set(src, promise);
  return promise;
}

function drawRoundedRectPath(ctx, x, y, w, h, r) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}

function drawCoverImage(ctx, img, w, h) {
  const imgRatio = img.width / img.height;
  const canvasRatio = w / h;
  let drawW = w;
  let drawH = h;
  let offsetX = 0;
  let offsetY = 0;

  if (imgRatio > canvasRatio) {
    drawW = h * imgRatio;
    offsetX = (w - drawW) / 2;
  } else {
    drawH = w / imgRatio;
    offsetY = (h - drawH) / 2;
  }
  ctx.drawImage(img, offsetX, offsetY, drawW, drawH);
}

function truncateText(ctx, text, maxWidth) {
  if (ctx.measureText(text).width <= maxWidth) return text;
  let out = text;
  while (out.length > 1 && ctx.measureText(`${out}…`).width > maxWidth) {
    out = out.slice(0, -1);
  }
  return `${out}…`;
}

function drawFallbackIcon(ctx, x, y, size, name) {
  ctx.save();
  drawRoundedRectPath(ctx, x, y, size, size, size * 0.22);
  const grad = ctx.createLinearGradient(x, y, x + size, y + size);
  grad.addColorStop(0, '#334155');
  grad.addColorStop(1, '#1e293b');
  ctx.fillStyle = grad;
  ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.18)';
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.fillStyle = '#ffffff';
  ctx.font = `600 ${Math.round(size * 0.42)}px -apple-system, "PingFang SC", sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText((name || '?').slice(0, 1).toUpperCase(), x + size / 2, y + size / 2 + 2);
  ctx.restore();
}

export async function renderPoster(canvas, state) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  canvas.width = CANVAS_WIDTH;
  canvas.height = CANVAS_HEIGHT;
  ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  ctx.save();
  if (state.rounded) {
    drawRoundedRectPath(ctx, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, 56);
    ctx.clip();
  }

  // 1. 绘制背景
  const backdrop =
    state.customBackdropUrl
      ? { type: 'image', src: state.customBackdropUrl }
      : BUILTIN_BACKDROPS.find((b) => b.id === state.backdropId) || BUILTIN_BACKDROPS[0];

  if (backdrop.type === 'image') {
    const bgImg = await loadImage(backdrop.src);
    if (bgImg) {
      const blurPx = Math.max(0, Math.min(24, Number(state.backdropBlur || 0)));
      if (blurPx > 0) {
        // 模糊时适当外扩绘制区域，避免画布四周出现透明/暗边伪影
        const pad = blurPx * 3;
        ctx.save();
        ctx.filter = `blur(${blurPx * 1.6}px)`;
        ctx.translate(-pad, -pad);
        drawCoverImage(ctx, bgImg, CANVAS_WIDTH + pad * 2, CANVAS_HEIGHT + pad * 2);
        ctx.restore();
      } else {
        drawCoverImage(ctx, bgImg, CANVAS_WIDTH, CANVAS_HEIGHT);
      }
    } else {
      ctx.fillStyle = '#0c0e12';
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    }
  } else {
    const grad = ctx.createLinearGradient(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    for (const stop of backdrop.stops) {
      grad.addColorStop(stop.pos, stop.color);
    }
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    if (backdrop.glow) {
      const gx = CANVAS_WIDTH * backdrop.glow.x;
      const gy = CANVAS_HEIGHT * backdrop.glow.y;
      const gr = CANVAS_WIDTH * backdrop.glow.r;
      const radial = ctx.createRadialGradient(gx, gy, 0, gx, gy, gr);
      radial.addColorStop(0, backdrop.glow.color);
      radial.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = radial;
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    }
  }

  // 2. 左侧文字可读性暗角渐变遮罩
  const scrimAlpha = Math.max(0.1, Math.min(0.88, (state.scrimOpacity ?? 55) / 100));
  const leftScrim = ctx.createLinearGradient(0, 0, CANVAS_WIDTH, 0);
  leftScrim.addColorStop(0, `rgba(6, 8, 12, ${Math.min(0.92, scrimAlpha + 0.22)})`);
  leftScrim.addColorStop(0.55, `rgba(6, 8, 12, ${scrimAlpha * 0.78})`);
  leftScrim.addColorStop(1, `rgba(6, 8, 12, ${scrimAlpha * 0.22})`);
  ctx.fillStyle = leftScrim;
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  const bottomScrim = ctx.createLinearGradient(0, CANVAS_HEIGHT * 0.65, 0, CANVAS_HEIGHT);
  bottomScrim.addColorStop(0, 'rgba(0,0,0,0)');
  bottomScrim.addColorStop(1, 'rgba(0,0,0,0.42)');
  ctx.fillStyle = bottomScrim;
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  // 3. 字体族配置
  const titleFontFamily =
    state.fontStyle === 'serif'
      ? '"Songti SC", "STSong", "Noto Serif CJK SC", Georgia, serif'
      : '"PingFang SC", -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif';
  const uiFontFamily =
    '"PingFang SC", -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif';

  // 4. 顶部主标题
  const padX = 112;
  const titleY = 128;
  ctx.save();
  ctx.fillStyle = '#ffffff';
  ctx.font = `700 84px ${titleFontFamily}`;
  ctx.textBaseline = 'top';
  ctx.textAlign = 'left';
  ctx.shadowColor = 'rgba(0, 0, 0, 0.45)';
  ctx.shadowBlur = 18;
  ctx.shadowOffsetY = 6;
  ctx.fillText(state.title || '2026 我的 Mac 常用软件', padX, titleY);
  ctx.restore();

  // 5. 计算各分类行布局（自适应 1~6 行，每行最多 10 个图标）
  const activeGroups = (state.groups || []).filter((g) => g.appIds && g.appIds.length > 0);
  const rowCount = Math.max(1, activeGroups.length);
  const gridTop = 276;
  const gridBottom = CANVAS_HEIGHT - 98;
  const availableH = gridBottom - gridTop;

  const labelColWidth = 230;
  const iconsStartX = padX + labelColWidth;
  const iconsAreaWidth = CANVAS_WIDTH - iconsStartX - padX;

  const maxRowItems = Math.max(1, ...activeGroups.map((g) => g.appIds.length));
  const idealRowH = availableH / rowCount;
  const iconSize = Math.round(
    Math.min(
      142,
      Math.max(88, idealRowH - 68),
      Math.max(88, (iconsAreaWidth - (maxRowItems - 1) * 44) / Math.max(maxRowItems, 6))
    )
  );
  const colGap = Math.round(
    Math.min(
      68,
      maxRowItems > 1 ? Math.max(26, (iconsAreaWidth - maxRowItems * iconSize) / (maxRowItems - 1)) : 60
    )
  );

  // 预加载当前海报上需要绘制的所有图标
  const uniqueIds = new Set();
  for (const g of activeGroups) {
    for (const id of g.appIds) uniqueIds.add(id);
  }
  const iconImages = new Map();
  await Promise.all(
    Array.from(uniqueIds).map(async (id) => {
      const app = state.appsById.get(id);
      if (app?.iconUrl) {
        iconImages.set(id, await loadImage(app.iconUrl));
      }
    })
  );

  // 6. 逐行绘制分类与图标
  activeGroups.forEach((group, rowIdx) => {
    const rowCenterY = gridTop + idealRowH * (rowIdx + 0.5);
    const iconTopY = Math.round(rowCenterY - (iconSize + 36) / 2);

    // 左侧分类标题（宋体模式下同步使用宋体，与主标题视觉统一）
    ctx.save();
    ctx.fillStyle = 'rgba(255, 255, 255, 0.94)';
    ctx.font =
      state.fontStyle === 'serif'
        ? `700 38px ${titleFontFamily}`
        : `600 34px ${uiFontFamily}`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.55)';
    ctx.shadowBlur = 10;
    ctx.fillText(truncateText(ctx, group.name, labelColWidth - 28), padX, iconTopY + iconSize / 2);
    ctx.restore();

    // 该行图标序列
    group.appIds.forEach((appId, colIdx) => {
      const app = state.appsById.get(appId);
      if (!app) return;

      const x = iconsStartX + colIdx * (iconSize + colGap);
      const y = iconTopY;
      const img = iconImages.get(appId);

      // 图标投影与绘制
      ctx.save();
      ctx.shadowColor = 'rgba(0, 0, 0, 0.42)';
      ctx.shadowBlur = 22;
      ctx.shadowOffsetY = 10;
      if (img) {
        ctx.drawImage(img, x, y, iconSize, iconSize);
      } else {
        drawFallbackIcon(ctx, x, y, iconSize, app.name);
      }
      ctx.restore();

      // 可选：优先展示真实使用时长（小时/分钟），无时长数据时回退显示活跃天数
      const usageHours = Number(app.usageHours || 0);
      const badgeText =
        usageHours >= 1
          ? `${usageHours >= 10 ? Math.round(usageHours) : usageHours.toFixed(1)}h`
          : usageHours > 0
            ? `${Math.max(1, Math.round(usageHours * 60))}m`
            : app.activeDaysRecent > 0
              ? `${app.activeDaysRecent}d`
              : '';
      if (state.showBadge && badgeText) {
        ctx.save();
        ctx.font = `600 18px ${uiFontFamily}`;
        const tw = ctx.measureText(badgeText).width;
        const bw = tw + 18;
        const bh = 28;
        const bx = x + iconSize - bw + 6;
        const by = y - 6;

        drawRoundedRectPath(ctx, bx, by, bw, bh, 14);
        ctx.fillStyle = 'rgba(15, 18, 25, 0.85)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.fillStyle = '#fbbf24';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(badgeText, bx + bw / 2, by + bh / 2 + 1);
        ctx.restore();
      }

      // 图标下方软件名称
      ctx.save();
      ctx.fillStyle = 'rgba(255, 255, 255, 0.94)';
      ctx.font = `500 24px ${uiFontFamily}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.72)';
      ctx.shadowBlur = 8;
      ctx.shadowOffsetY = 2;
      const label = truncateText(ctx, app.name, iconSize + colGap - 12);
      ctx.fillText(label, x + iconSize / 2, y + iconSize + 14);
      ctx.restore();
    });
  });

  // 7. 底部左右信息栏（左下角署名 + 右下角统计/备注）
  if (state.author && state.author.trim()) {
    const rawAuthor = state.author.trim();
    const needsSpace = /[A-Za-z0-9]$/.test(rawAuthor);
    const authorLabel = rawAuthor.endsWith('推荐')
      ? rawAuthor
      : `${rawAuthor}${needsSpace ? ' ' : ''}的推荐`;
    ctx.save();
    ctx.fillStyle = 'rgba(255, 255, 255, 0.72)';
    ctx.font = `500 24px ${uiFontFamily}`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.6)';
    ctx.shadowBlur = 8;
    ctx.fillText(authorLabel, padX, CANVAS_HEIGHT - 44);
    ctx.restore();
  }

  if (state.subtitle && state.subtitle.trim()) {
    ctx.save();
    ctx.fillStyle = 'rgba(255, 255, 255, 0.68)';
    ctx.font = `400 24px ${uiFontFamily}`;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'bottom';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.6)';
    ctx.shadowBlur = 8;
    ctx.fillText(state.subtitle.trim(), CANVAS_WIDTH - 88, CANVAS_HEIGHT - 44);
    ctx.restore();
  }

  // 内描边高光，提升精致卡片感
  if (state.rounded) {
    drawRoundedRectPath(ctx, 1, 1, CANVAS_WIDTH - 2, CANVAS_HEIGHT - 2, 55);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.14)';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  ctx.restore();
}
