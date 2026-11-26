---
name: static-html-domstub-test
description: 给单文件 HTML 应用（自研工作台/看板/本地工具页）做回归测试：用最小 DOM 桩把页面里那段 JS 真加载起来、喂真实数据、逐条断言渲染结果，不启浏览器；桩抓不到的（拖动/手势/同一屏多处一致性）再用真浏览器（Playwright/Chromium）点一遍冒烟。当需要验证排序/筛选/表单编辑/数据归一/分组归并/交互控件，或怀疑"界面看着正常但语义是错的"时使用。也包含一套针对"静默故障"的检查清单（含新增顶层状态键的"三道关"、归并功能的守恒断言、缓存快照的重算校验、假断言的识别），以及"哪些逻辑桩验不了"的判断标准。
---

# 单文件 HTML 应用的 DOM 桩回归测试

## 何时用这个技能

- 改了一个自包含的 HTML 应用（内嵌 `<script>`，数据来自 `fetch('/data.json')` 或 localStorage）
- 需要验证：**排序方向、筛选命中数、表单回填与保存、归一函数、字段守恒**
- 页面「能打开、有数据、看着正常」，但你怀疑语义是错的
- 没有前端构建、没有测试框架，也不想为了跑几条断言去起 Playwright

**判断信号**：只要你开始想"我手动点一遍就知道了"——换成写断言。手动点一遍抓不到
"首行日期是错的""筛选命中 0 条"这类问题，因为界面不会报错。

## 核心思路

页面 `workbench.html` 里的那段 `<script>` 是**纯函数 + DOM 操作**，不依赖任何框架。
所以只要提供一个最小 DOM 桩，就能把它 `new Function(...)` 加载起来直接调用。

```js
const src = fs.readFileSync('workbench.html', 'utf8');
const js  = [...src.matchAll(/<script>([\s\S]*?)<\/script>/g)].pop()[1];  // 取最后一个 script

const api = new Function('document','localStorage','location','alert','setInterval','fetch',
  js + `\nreturn { renderAll, renderLedger, editEarn, saveEarn };`)(doc, localStorage, location, alertFn, () => 1, fetchFn);

await new Promise(r => setTimeout(r, 0));   // 让文件末尾的 boot IIFE 里那个 await 落地
```

**取最后一个 `<script>`** 很重要：如果页面里还有别的 script（比如离线兜底页会注入
`<script id="wb-seed">`），用 `.pop()` 才拿到主脚本；而且 `<script>` 的精确匹配
（不带属性）天然排除了 `<script id="...">`。

## DOM 桩的必备成员

```js
const els = new Map();
const el = id => els.get(id) || (els.set(id, new El(id)), els.get(id));

const doc = {
  getElementById: el,                                    // 用 Map 自动生成任意 id
  querySelectorAll: sel => sel === '.ov' ? [el('projOv'), el('earnOv')] : [],   // 见下方坑 2
  querySelector: s => el(s),
  documentElement: new El('html'),
  addEventListener: () => {},
  createElement: () => new El('tmp'),
  body: new El('body'),
};
const store = new Map([['wb', JSON.stringify(realData)]]);   // 用真实数据播种 localStorage
const localStorage = { getItem: k => store.get(k) ?? null, setItem: (k,v) => store.set(k, String(v)) };
const location = { protocol: 'http:', search: '?token=' + TOKEN, href: BASE + '/x.html' };
```

`El` 类最小实现（关键是 `value` 的 setter 语义）：

```js
class El {
  constructor(id){ this.id=id; this._value=''; this._html=''; this._opts=null;
    this.textContent=''; this.className=''; this.disabled=false; this.style={}; this._attr={}; this._q={}; }
  get value(){ return this._value; }
  // 复刻真实 DOM：设成不在 option 列表里的值 → 退化成 ""。不复刻就会漏掉"选项与取值不一致"的 bug
  set value(v){ v=String(v??''); this._value = this._opts ? (this._opts.includes(v)?v:'') : v; }
  get innerHTML(){ return this._html; }
  set innerHTML(h){ this._html=String(h);
    const f=[...this._html.matchAll(/<option(?: value="([^"]*)")?>([^<]*)<\/option>/g)];
    this._opts = /<option/.test(this._html) ? f.map(m => m[1]!==undefined?m[1]:m[2]) : null; }
  querySelector(s){ return this._q[s] || (this._q[s]=new El(this.id+' '+s)); }   // tbody 之类
  classList = { _s:new Set(), add(c){this._s.add(c)}, remove(c){this._s.delete(c)}, contains(c){return this._s.has(c)} };
  getAttribute(k){ return this._attr[k] ?? null; } setAttribute(k,v){ this._attr[k]=String(v); }
  focus(){} click(){}
}
```

拿到渲染结果后**当字符串断言**：

```js
const tbody = el('ledger').querySelector('tbody');
const dates = [...tbody.innerHTML.matchAll(/<td>(\d{2}-\d{2})<\/td>/g)].map(m => m[1]);
// 断言首行日期、是否降序、命中条数、tag 文案…
```

## 两个必须复刻的桩设计（踩过才知道，不复刻会得到假失败）

1. **`select.value = x` 的隐式退化**：x 不在 option 列表里时，真实 DOM 会把它变成 `""`。
   桩不复刻这条，就会掩盖"选项文本与 value 不一致"的 bug（例如把 value 设成标签文案而非真实值）。
2. **`document.querySelectorAll(".ov")` 不能返回空数组**。若页面里 `closeOv()` 靠
   `querySelectorAll(".ov").forEach(o=>o.classList.remove("show"))` 关弹窗，
   返回空数组会让它变成空操作 → 一串"弹窗已关闭"断言**全部假失败**，白查一轮。
   **规律：桩必须覆盖被测代码实际会碰到的每一个 DOM 面。**

## 断言清单（针对「静默故障」的七类检查）

按这七条写断言，命中率最高——它们都是**不报错、不崩、界面看着正常**的错误：

| # | 检查 | 怎么写 |
|---|---|---|
| 1 | **字段守恒 / 归一无损** | 对比 `Object.keys(normalize(raw))` 与 `Object.keys(raw)`：**只查"丢"的那一向，不查"多"的那一向**。少一个键 = 用户点一次保存就会抹掉它（若保存是整体回写）；而 normalize 多出一个键是**合法**的 —— 页面新加的顶层键在用户还没触发那次保存之前，本来就不在数据文件里。写成"键集必须完全相等"会把"新功能刚上线还没落盘"判成"丢字段"，实测假红过一次。放宽到子集不会漏掉真问题：键名打错（`goals`→`goalsX`）照样让原键消失，仍然会红 |
| 2 | **排序作用在最终渲染数组上** | 从渲染结果里正则提取日期/序号，断言首行是**最新**（或最旧）的那条，且整体单调 |
| 3 | **筛选命中数 == 按条件的直接计数** | `assert(filters().length === raw.filter(cond).length)`。别只看"有没有结果"——命中恒为 0 时列表是空的，页面看起来只是"暂无数据" |
| 4 | **CSS 类名都有定义** | 搜一遍新写的类名在 `<style>` 里是否存在。只写类名不写样式不会报错，只会"看着还行" |
| 5 | **归并 / 分组类功能必须断言"守恒"** | 见下方专节。只断言"分成几组、每组多少"**抓不到丢记录** |
| 6 | **不写"检查能否编译"式校验，也不写假断言** | 三类"永远通过"的假断言：① 校验生成物里的缓存统计是否过期，只查"格式合法/能编译"永远通过，必须**重算再比**；② 断言本身是恒等式；③ **带后门的条件**（`if (由被测代码算出的值 === 魔数) 才比对，否则 return true` —— 代码一坏那个值本身就变了，条件不成立、静默放行）。②③ 见下 |
| 7 | **别写死"口径派生值"** | 组数 / 行数 / 标签文案这类**随口径变化**的值从实际结果派生（`st.merged.length`），只有**数据真值**才写死 |

再补几条通用的：只读记录不渲染编辑/删除入口、保存是**原位更新**而非新增、必填校验拦住非法输入、
以及"元数据（`xReadonly`/`xSource`）在渲染里确实生效"。

### 检查 1 的实操：新增一个顶层状态键，要过「三道关」

这条已经踩过 5 次（同一个应用）。把三道关分开看，能立刻定位该改哪里：

| # | 关卡 | 要确认什么 | 常见结论 |
|---|---|---|---|
| 1 | **同步 / 拉取脚本**会不会冲掉它？ | 该脚本是"只改固定键、其余整体回写"，还是"重建整个对象"？ | 前者**安全**（未知键天然保留） |
| 2 | **写盘接口**（POST/PUT handler）会不会裁剪？ | 是 `json.dump(obj)` 原样落盘，还是按白名单重建？ | 常见是"只校验必需键**存在**"→ **安全** |
| 3 | **前端归一函数 + 整体回写**会不会丢？ | `normalize()` 是不是重建对象？保存是不是把归一结果整体 POST 回去？ | ⚠️ **这里才是真陷阱**，而且**当场不报错** |

**关键认知：前两道关"安全"往往是巧合，第三道关是结构性必然。**
所以规则只有一条：**加了顶层键，就必须同时加进归一函数的透传列表，并且有断言守着。**
别指望"记性"——把这条写进断言，才在下一次重构时不会重演：

```js
['sourceMap','earningsReadonly','earningsSource','projectsSource','notionMeta'].forEach(k => {
  t(`normalize() 透传 ${k}`, roundTrip[k] !== undefined && roundTrip[k] !== null);
});
```

### 检查 5 的实操：归并类功能必须断言守恒

写"分组 / 归并 / 分类汇总 / 来源排行"时，断言"分成 8 组、每组 12 笔"是**不够的**——
分组数对、总额少一笔完全可能同时成立。要断言的是**守恒**：

```js
t('笔数守恒', mergedN + tailN === incomeN);
t('金额守恒', Math.abs(mergedV + tailV - total) < 0.005);   // 浮点别用 ===
```

守恒断言负责**发现**问题，但**定位**还得靠"逐个写死真值"：

```js
[['客户A',42,4200.00], ['客户B',15,750.00], ['渠道C',10,1200.00]]
  .forEach(([n, cnt, amt]) => t(`${n} = ${cnt} 笔 ${amt}`, /* 断言组名→笔数→金额 */));
```

> [!warning] 守恒的边界：**能"发现"，不能"定位"**
> 匹配**范围**写错时，钱和笔数照样平（`154+95=249` 成立），守恒断言**全绿**。
> 所以守恒之外**必须**再给每个分组写死真值 —— 那才是定位手段。
> 只写守恒 = 拿到一个"永远通过"的假安心。

**三个真实教训**：
1. **规则顺序即优先级（首个命中生效）。** 一条记录同时命中"社群规则"和"含指定关键词的雇主规则"时，
   顺序反了就会被吞进错的那组，总额居然还是守恒的 —— 守恒抓不到，只有写死真值才抓到。
2. **匹配范围要比"默认只看第一段"想得更多。** 备注的真实结构常常是
   **「任务 | 给&lt;客户&gt;做某事」——客户名在第二段**。只按首段归类时，
   `${任务} | 给客户A…` 会被归给 `任务` 那一组：**客户A 被少算一半（21 笔 → 42 笔）**，
   另有 31 笔归错。修法是给规则加 `scope` 字段（`seg1` 默认 / `note` 匹配整条），
   显式客户标记用 `scope:"note"` 且**必须排最前**。
   ⚠️ 这类错误**守恒和组数断言全都抓不到**，只能**逐组翻原始行**发现。
   → 归并/分类功能上线后，**必须抽样翻看真实输出**（导出的 CSV / 渲染出的行），
   不能只看汇总数字。
3. **"不归并"和"已撤销"的组都要留痕。** 故意没归并的组写进 `notMerged: [{name, reason}]`；
   已确认后又发现归错的组，**不是删掉了事**，而是同样写进 `notMerged` 并注明撤销原因 ——
   否则以后会有人以为是漏了。同时补一条"它确实不再成组"的负向断言。

### 检查 6 的实操：缓存快照必须**重算**才能判过期

如果生成物里带了一份写入时刻的统计快照（组数 / 笔数 / 金额），数据一变快照就过期。
`--verify` 只检查"规则能否编译""JSON 是否合法"是**永远通过**的：

```python
# ✗ 永远通过
for r in rules:
    for p in r['patterns']: re.compile(p)

# ✓ 用规则在当前数据上重算，与快照比对
merged, tail = group(rows, compile_rules())
for msg in diff_against_snapshot(merged, tail):   # 有偏差就报"快照已过期"
    print('⚠ ' + msg)
return 1 if stale else 0
```

**必须用负向测试验它真的会红**：故意把快照里的 `count` 改成 999，跑一遍，
确认退出码非 0 且报出偏差，再还原。
（这一步别省——不然你写的是"永远绿"的校验，比没有更危险。）

### 检查 7 的实操：别写死"口径派生值"

同一批断言里要区分两类数字，混了就会**每次调口径都陪一批假红**：

| 类型 | 例子 | 怎么写 |
|---|---|---|
| **数据真值** | `客户A = 42 笔 4200.00`、`净额 = 12345.678` | **写死**。它的作用就是在数据/规则被改动时立刻红 |
| **口径派生值** | 归并**组数**、排行**行数**、tag 文案 `已归并 9 组` | **从实际结果派生**（`st.merged.length`、`api.sourceStats()`） |

```js
// ✗ 归并组数从 11 掉到 9 时假红，而代码其实是对的
t('排行渲染出 srcrow 行', (sr.match(/class="srcrow/g)||[]).length >= 11);

// ✓ 派生：行数 = min(10, 归并组数) + 1 行聚合
const expRows = Math.min(10, st.merged.length) + (st.tailN > 0 ? 1 : 0);
t(`排行渲染出 ${expRows} 行`, (sr.match(/class="srcrow/g)||[]).length === expRows);
t('tag 说明已归并组数',
  el('srcTag').textContent.includes(`已归并 ${st.merged.length} 组`));
```

顺带一条：**断言标题里也别写死派生数字**。标题会成为失败信息的一部分，
标题写错会把人往错的方向引（"CSV 去重后 = 11 组"实际是 9 组）。
断言标题里的数一律用模板字符串插进去。

### 别写假断言（= 伪装成断言的注释）：恒等式，以及带后门的条件

**形态一：恒等式。** 写"分片 / 口径 / 守恒"类断言时，很容易顺手写出**数学上恒真**的式子。它永远绿，等于没写：

```js
// ✗ 恒等式。无论 split() 有没有丢记录、丢钱，它都通过。
t('本月 + 非本月 = 累计', pm.length + (pa.length - pm.length) === pa.length);
t('金额守恒', Math.abs(pm + (pa - pm) - pa) < 1e-9);

// ✓ 独立复算：用**另一条路径**算出期望值再比。
//    这才是"守恒断言"该有的样子 —— 它必须可能失败。
const ymk = api.todayStr().slice(0, 7);
const expect = raw.filter(e => e.date.startsWith(ymk));      // 不复用被测函数
t('分组结果 == 手算切片', got.length === expect.length && got.every((e, i) => e === expect[i]));
```

**形态二：带后门的条件。** 为了"让断言在各种数据下都能过"，很容易写出这种条件式：

```js
// ✗ 后门。模数 200000 是"正常代码应当算出的值"。
//    代码一旦坏掉，res.max 本身就变了 → 条件不成立 → 直接放行 → 永远绿。
t('量程在三种单位下指向同一区间', (() => {
  const r = {}; for (const u of UNITS) { api.setUnit(u); r[u] = api.spec(); }
  return r.yuan.max === 200000 ? (r.k.max * 1000 === r.yuan.max) : true;   // ← 这个 true 就是后门
})());

// ✓ 去掉门槛，无条件比对（容差只为吸收浮点误差，不承担"绕过检查"的作用）
const closeTo = (a, b) => Math.abs(a - b) <= 1e-6 * Math.max(1, Math.abs(b));
t('量程在三种单位下指向同一区间', (() => {
  const r = {}; for (const u of UNITS) { api.setUnit(u); r[u] = api.spec(); }
  return closeTo(r.k.max * 1000, r.yuan.max) && closeTo(r.wan.max * 10000, r.yuan.max);
})());
```

"要兼容多种数据"的正确做法是**把条件写进断言本身**（分支型断言），
而不是在断言外面加一个返回 `true` 的开关。

判别法还是那一句：**把被测函数故意改坏，这条断言会红吗？** 不会 → 它是注释，不是断言。
（同理，校验脚本也要做负向测试：手动把快照改错，确认真的报红，再改回来。）

> [!warning] 变异测试本身也要验
> 做"故意改坏"验证时，**先确认变异真的注入、且方向符合预期**。
> 有过一次：变异把 `return {min:0, max:max, step}` 误写成 `max:step`，改坏后的代码恰好量纲自洽，
> 于是"断言没红"被误读成"这条断言没用"，白折腾一轮。
> 落笔前先跑一次并**看一眼变异后的函数体**，再下结论。

### 分支型 UI 文案：断言必须按数据分情况写

当渲染逻辑**按数据分支给出不同文案**时（例：剩余天数 >3 天给"日均需 ¥X"，≤3 天改说"顺延到下月"），
写死一种文案的断言会在某些日期/数据下假红。正确写法是把分支条件也表达出来：

```js
const tooLate = left <= 3;
t(tooLate ? '剩 ≤3 天时不给「日均需」（算式对但无行动价值）'
          : '行动建议给出日均需 = 缺口/剩余天数',
  tooLate ? (act.includes('顺延到下月') && !act.includes('日均需'))
          : act.includes(fmt((goal - net) / left)));
```

配套的设计教训：**算式推得出 ≠ 值得展示**。`缺口 / 剩余天数` 在 `left=1` 时算出「日均需 ¥50,000」,
数学没错，但读者拿它做不了任何决定 —— 这时该换一句诚实的话，而不是把数字硬塞出去。

### 给用户看的结论数字：让脚本生成，不要手抄

写报告 / 评审页 / 给用户做判断依据的表格时，**任何数字都不要手工誊写**（包括我自己算出来的）。
本应用上因此连纠两次：一次是结论数字取自"未排重的粗匹配"，与表格里的口径不一致；
一次是用一句模板话盖住了不成立的事实。

**两种修法**：
- 结论句**由脚本按同一口径生成**（把判定逻辑写进生成器，而不是写死在文档里）；
- 或另写一个**独立脚本按同一口径复算一遍**再比。

配套加一条断言：**"算不平就喊出来"**。例如归并类页面在渲染前先校验
`|mergedV + tailV - total| < 0.005`，不为 0 就在页面上打红色警示块、
并说明"此表不可信"。同样地，规则/配置整个缺失时（`sourceMap` 不见了）
也要显示红色提示，而不是安静地退化成"每种写法各算一个来源"——**后者数字看着正常但全错**。


### 清单之外的另一类：降级模式必须"喊出来"，不能静默

如果页面读取的数据源**需要鉴权**（token / cookie），那么"读失败"极容易退化成
**"照常显示、但用的是本地缓存的旧数据"**——这是最难发现的一类，因为界面完全正常。

典型实现：`if(r.ok){ ...用线上数据... }`，然后**静默 fallthrough** 到 `localStorage`。

**两条必写断言**：

```js
// 环境：SERVED（http）但没有令牌，fetch 固定返回 401
t('TOKEN 为空且标记为缺失', flags().TOKEN === '' && flags().TOKEN_MISSING === true);
t('读失败时给出缓存数据（不至于白屏）', state().earnings.length > 0);
t('横幅明确告知"你看的是缓存旧数据"', el('banner').innerHTML.includes('缓存'));
t('横幅给出具体修复动作', el('banner').innerHTML.includes('open-workbench.sh'));
t('无令牌时"提交/同步"按钮先拦下，不发起请求', fetchCalls === before);
```

最后一条尤其值钱：**在发起请求前就先拦下并给出可操作提示**，比把裸的
`401 unauthorized` 甩给用户强得多，也省掉一轮排查。

**相关线索**：用户报的失败**耗时是 `0.0s`** → 请求根本没进业务逻辑，先查认证/路由/参数，
别去查网络和下游服务。

## 在线模式的真机集成测试

把 `fetch` 换成**真的发往本地服务**，并把相对路径补成绝对路径，就能把「点按钮」的整条链路测穿：

```js
const realFetch = (u, o) => fetch(String(u).startsWith('/') ? BASE + u : u, o);
const location = { protocol: 'http:', search: '?token=' + TOKEN, ... };   // 让页面进入 SERVED 分支
```

再补一条**落盘前/后对比**：记录数增减是否在预期内、关键字段是否被抹掉、金额精度是否被 `round` 破坏、
顶层键集是否变化。这是抓"UI 静默破坏数据"的最后一道网。

⚠️ 真机测试会真改数据，跑之前先备份/确认幂等。

## 桩的盲区：哪些逻辑**必须**上真浏览器

桩擅长「输入 → 输出」的纯逻辑。**只要一段逻辑的正确性依赖"浏览器在两次事件之间还会做别的事"，
桩就不够用。** 实测在桩全绿的 311 条断言之后，真浏览器一点又抓出 3 处：

| 缺陷 | 机制 | 为什么桩抓不到 |
|---|---|---|
| **滑动条正反馈** | 量程上限由"当前值"算出，而拖动条自己就在改这个值 → 鼠标停在原地不动，量程跟着涨，值自己飙（一次手势 30 万 → ¥1,554.50 万） | 桩里拖滑块是 `el.value='60000'`，没有"指针位置 → 值"的映射，那个循环**根本不会发生** |
| **同一屏多处不一致** | 同一件事（达成率不足 1%）在 A 处改了措辞，B/C 处没改 | 桩能验单点，但"三处必须一致"要靠眼睛扫一遍 |
| **数值不值得显示** | 「缺口约合 2820 笔」算式没错，但和"本月只成交 3 笔"摆在一起毫无行动价值 | 桩断言的是"有没有这个数"，不是"这个数值该不该出现" |

### 冒烟脚本怎么写（Playwright 最小版）

```js
const { chromium } = require('playwright');
const b = await chromium.launch({ executablePath: CHROME_BIN });   // 见下方"没有 headless_shell"的坑
const p = await b.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2 });
const errs = [];
p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
p.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));      // ← 必须挂，运行时异常只会出现在这里
await p.goto(URL, { waitUntil: 'networkidle' });

// 1) 交互要用**真鼠标**，不要直接改 value —— 直接改 value 就退化回"桩"，正反馈那类 bug 就测不出来
const box = await p.locator('#slider').boundingBox();
await p.mouse.move(box.x + box.width * 0.5, box.y + box.height / 2);
await p.mouse.down();
await p.mouse.move(box.x + box.width * 0.85, box.y + box.height / 2, { steps: 12 });
await p.mouse.up();

// 2) 同一屏多处一致性：一次 evaluate 把几处文本一起捞出来比
const snap = await p.evaluate(() => ({ a: document.getElementById('a').innerText,
                                       b: document.getElementById('b').innerText }));
// 3) 布局溢出：目标容器内的元素不许越过它的右边界
const overflow = await p.evaluate(() => {
  const host = document.getElementById('hero'), hr = host.getBoundingClientRect(), bad = [];
  host.querySelectorAll('*').forEach(el => { const r = el.getBoundingClientRect();
    if (r.width && r.right > hr.right + 1) bad.push(el.id || el.className || el.tagName); });
  return bad;
});
```

要点：
- **`pageerror` 必挂**：DOM 桩能吞掉的一切运行时异常，真浏览器会在这里报出来。控制台里剩下的 404 多半只是 `favicon.ico`，先去服务端确认再当问题。
- **交互一律用鼠标/键盘**，直接赋 `value` 就退回成桩了。
- **目标容器内做溢出扫描**比肉眼可靠，也顺便验证了新控件的排版。
- 没有 headless 浏览器时，用 `executablePath` 指向本机已缓存的那份完整 Chromium 即可，不必联网下载。

> [!warning] 真机冒烟会**写到真实数据**
> 拖动条的 `change`、按钮的提交都会真的落盘。实测第一次冒烟就把测试值写进了正式数据文件。
> 两条纪律：① 冒烟前想清楚哪些操作会落盘；② **收尾必须还原**，而且要用**应用自己的还原路径**
> （比如页面上的「清除」按钮）而不是手改 JSON —— 这样既还原了数据，又顺带把"清除"这条路径也验了。
> 还原后逐项核对数量与关键字段。

## 两个坑

- **静态 HTML 里的初始文案桩解析不出来**。例如 `<button>同步一次</button>` 的文案，
  页面 JS 会读 `btn.textContent` 当"原值"做恢复，桩里是空串 → 恢复后断言失败。
  手工补一次 `el('syncBtn').textContent='同步一次'` 即可。
- **`bash` 里的 `grep` 在某些环境反复返回空**（环境怪异）。改用专门的 Grep 工具或
  Python 正则，别在 `bash grep` 上浪费时间。
