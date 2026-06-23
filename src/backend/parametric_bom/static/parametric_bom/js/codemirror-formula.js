/**
 * CodeMirror 5 Formula Editor — 参数化BOM公式编辑控件
 * 
 * 使用 CodeMirror 5（CDN 单文件），专门用于 esm.sh 不可用/不稳定的场景。
 * 提供：语法高亮、自动补全（函数+参数）、药丸插入。
 */

// ─── All Known Formula Functions ────────────────────────────────────────────

const FORMULA_FUNCTIONS = [
  { label:'ABS', detail:'绝对值', args:'(x)' }, { label:'CEIL', detail:'向上取整', args:'(x)' },
  { label:'FLOOR', detail:'向下取整', args:'(x)' }, { label:'ROUND', detail:'四舍五入', args:'(x, [n])' },
  { label:'MAX', detail:'最大值', args:'(a, b)' }, { label:'MIN', detail:'最小值', args:'(a, b)' },
  { label:'POW', detail:'幂运算', args:'(base, exp)' }, { label:'SQRT', detail:'平方根', args:'(x)' },
  { label:'MOD', detail:'取模', args:'(a, b)' }, { label:'PI', detail:'圆周率', args:'()' },
  { label:'RAND', detail:'随机数', args:'()' }, { label:'CONCAT', detail:'拼接', args:'(...vals)' },
  { label:'LEFT', detail:'取左侧', args:'(s, n)' }, { label:'RIGHT', detail:'取右侧', args:'(s, n)' },
  { label:'MID', detail:'截取', args:'(s, st, n)' }, { label:'LEN', detail:'长度', args:'(s)' },
  { label:'FIND', detail:'查找位置', args:'(sub, s)' }, { label:'UPPER', detail:'转大写', args:'(s)' },
  { label:'LOWER', detail:'转小写', args:'(s)' }, { label:'TRIM', detail:'去空格', args:'(s)' },
  { label:'REPLACE', detail:'替换', args:'(s,i,n,r)' }, { label:'SUBSTITUTE', detail:'替换全部', args:'(s,o,n)' },
  { label:'CONTAINS', detail:'包含', args:'(s,sub)' }, { label:'STARTSWITH', detail:'开头匹配', args:'(s,pre)' },
  { label:'ENDSWITH', detail:'结尾匹配', args:'(s,suf)' }, { label:'SUBSTR', detail:'截取子串', args:'(s,st,n)' },
  { label:'SIN', detail:'正弦', args:'(deg)' }, { label:'COS', detail:'余弦', args:'(deg)' },
  { label:'TAN', detail:'正切', args:'(deg)' }, { label:'ASIN', detail:'反正弦', args:'(x)' },
  { label:'ACOS', detail:'反余弦', args:'(x)' }, { label:'ATAN', detail:'反正切', args:'(x)' },
  { label:'ATAN2', detail:'反正切2', args:'(y,x)' }, { label:'DEGREES', detail:'弧度→角度', args:'(rad)' },
  { label:'RADIANS', detail:'角度→弧度', args:'(deg)' }, { label:'LOG', detail:'常用对数', args:'(x)' },
  { label:'LN', detail:'自然对数', args:'(x)' }, { label:'EXP', detail:'指数(e^x)', args:'(x)' },
  { label:'INTEGER', detail:'取整', args:'(x)' }, { label:'DECIMAL', detail:'小数部分', args:'(x)' },
  { label:'ABS2', detail:'绝对值', args:'(x)' }, { label:'IFNULL', detail:'空值默认', args:'(val,def)' },
  { label:'MIN2', detail:'最小值聚合', args:'(...vals)' }, { label:'MAX2', detail:'最大值聚合', args:'(...vals)' },
  { label:'IF', detail:'条件判断', args:'(c,t,f)' }, { label:'AND', detail:'逻辑与', args:'(...exprs)' },
  { label:'OR', detail:'逻辑或', args:'(...exprs)' }, { label:'NOT', detail:'逻辑非', args:'(x)' },
  { label:'LET', detail:'中间变量', args:'("n",v,e)' }, { label:'SWITCH', detail:'多分支', args:'(v,c1,r1,...)' },
  { label:'INT', detail:'转整型', args:'(x)' }, { label:'STR', detail:'转字符串', args:'(x)' },
  { label:'FLOAT', detail:'转浮点', args:'(x)' }, { label:'BOOL', detail:'转布尔', args:'(x)' },
]

// ─── Syntax Highlighting (CM5 mode) ─────────────────────────────────────────

const FUNC_NAMES = FORMULA_FUNCTIONS.map(f => f.label)

// CM5 mode for formula syntax
function defineFormulaMode() {
  if (CodeMirror.modes?.formula) return
  CodeMirror.defineMode('formula', function() {
    return {
      token: function(stream) {
        if (stream.eatSpace()) return null
        // Strings
        if (stream.match(/^"([^"\\]|\\.)*"/)) return 'string'
        if (stream.match(/^'([^'\\]|\\.)*'/)) return 'string'
        // param.xxx
        if (stream.match(/^param\s*\.\s*[\u4e00-\u9fff\w]+/)) return 'property'
        // true/false
        if (stream.match(/^(true|false|TRUE|FALSE)\b/)) return 'atom'
        // Numbers
        if (stream.match(/^\d*\.?\d+([eE][+-]?\d+)?/)) return 'number'
        // Function names
        if (stream.match(/^[A-Z][A-Z0-9_]*/)) {
          const word = stream.current()
          if (FUNC_NAMES.includes(word)) return 'builtin'
          return 'variable'
        }
        // Identifiers (Chinese/word)
        if (stream.match(/^[\u4e00-\u9fff\w]+/)) return 'variable'
        // Operators
        if (stream.match(/^[+\-*/%^><=!&|]+/)) return 'operator'
        // Brackets
        if (stream.match(/^[(){}[\].,;:]/)) return 'bracket'
        stream.next()
        return null
      }
    }
  })
}

// ─── CM5 Instance Storage ───────────────────────────────────────────────────

const _cmInstances = new WeakMap()
let _cmReady = false

function ensureCmLoaded() {
  if (typeof CodeMirror !== 'undefined') {
    if (!_cmReady) {
      defineFormulaMode()
      _cmReady = true
    }
    return true
  }
  return false
}

// ─── Attach CM5 to Input ────────────────────────────────────────────────────

export function attachCmToInput(inputEl, opts = {}) {
  if (!inputEl || !ensureCmLoaded()) return null
  if (inputEl.dataset.cmInit) return _cmInstances.get(inputEl)

  const isInline = opts.inline !== false
  const minH = opts.minHeight || (isInline ? 32 : 64)

  const container = document.createElement('div')
  container.className = 'cm-formula-wrap'
  container.style.cssText = `border:1px solid #d1d5db;border-radius:6px;overflow:hidden;flex:1;min-height:${minH}px`

  inputEl.parentNode.insertBefore(container, inputEl)
  inputEl.style.display = 'none'
  inputEl.dataset.cmInit = '1'

  const editor = CodeMirror(container, {
    value: inputEl.value || '',
    mode: 'formula',
    theme: 'default',
    lineWrapping: true,
    viewportMargin: Infinity,
    extraKeys: {
      'Ctrl-Space': 'autocomplete',
    },
    styleActiveLine: false,
    matchBrackets: true,
    foldGutter: false,
    gutters: [],
    hintOptions: {
      completeSingle: false,
      closeOnBlur: false,
    },
  })

  // Auto-trigger autocomplete when typing
  let autoHintTimer
  editor.on('inputRead', function(cm, change) {
    clearTimeout(autoHintTimer)
    if (!change.text.length) return
    const ch = change.text[0]
    if (!ch || !/[\w.\u4e00-\u9fff]/.test(ch[ch.length - 1])) return
    autoHintTimer = setTimeout(function() {
      // Only trigger if cursor is on a word-like token
      const cursor = cm.getCursor()
      const token = cm.getTokenAt(cursor)
      if (token.string && token.string.length > 0) {
        cm.showHint({ hint: CodeMirror.hint.formula, completeSingle: false })
      }
    }, 250)
  })

  // Sync changes back to hidden input
  editor.on('change', function(cm) {
    inputEl.value = cm.getValue()
    inputEl.dispatchEvent(new Event('input', { bubbles: true }))
  })

  // Focus tracking
  editor.on('focus', function() {
    container.style.borderColor = '#3b82f6'
    container.style.boxShadow = '0 0 0 2px rgba(59,130,246,0.15)'
    if (inputEl.dataset.field) window.__activeBomField = inputEl.dataset.field
    if (inputEl.dataset.bom) window.__activeBomPk = inputEl.dataset.bom
  })
  editor.on('blur', function() {
    container.style.borderColor = '#d1d5db'
    container.style.boxShadow = 'none'
  })

  const instance = { editor, container, inputEl }
  _cmInstances.set(inputEl, instance)
  return instance
}

// ─── Autocomplete ───────────────────────────────────────────────────────────

function setupAutocomplete(parameters) {
  const paramList = parameters || []

  CodeMirror.registerHelper('hint', 'formula', function(editor) {
    const cursor = editor.getCursor()
    const pos = cursor.ch
    const token = editor.getTokenAt(cursor)

    // Get word before cursor — use token or get word from line
    const start = token.start
    const word = token.string || ''
    const lower = word.toLowerCase()
    const options = []

    // 1. Show function suggestions (always, if word matches)
    for (const fn of FORMULA_FUNCTIONS) {
      if (fn.label.toLowerCase().startsWith(lower)) {
        options.push({
          text: `${fn.label}(`,
          displayText: fn.label,
          hint: `${fn.detail}`,
        })
      }
    }

    // 2. Show parameter suggestions
    const fullPrefix = editor.getRange({line:cursor.line,ch:Math.max(0,pos-30)}, cursor)
    // Check if we're typing param.xxx or just a word that could be a param
    const isParamContext = fullPrefix.includes('param') || lower.length >= 1
    if (isParamContext) {
      for (const p of paramList) {
        const name = p.name || p.parameter_name || p.key || ''
        // Only show if word matches param name OR word is very short (just started typing)
        if (name.toLowerCase().includes(lower) || lower.length <= 1) {
          options.push({
            text: `param.${name}`,
            displayText: `param.${name}`,
            hint: `${p.data_type || '?'}`,
          })
        }
      }
    }

    if (options.length) {
      return { list: options, from: { line: cursor.line, ch: start }, to: { line: cursor.line, ch: pos } }
    }
    return null
  })
}

// ─── Public API ─────────────────────────────────────────────────────────────

export function getCmInstance(inputEl) {
  return _cmInstances.get(inputEl) || null
}

export function insertAtCursor(inputEl, text) {
  const inst = _cmInstances.get(inputEl)
  if (!inst) return false
  inst.editor.replaceSelection(text)
  inst.editor.focus()
  return true
}

export function initFormulaEditors(parameters) {
  if (!ensureCmLoaded()) {
    console.warn('CodeMirror not available')
    return 0
  }
  setupAutocomplete(parameters || window.configuratorPartData?.parameters || [])

  const paramList = parameters || window.configuratorPartData?.parameters || []
  const selectors = [
    'input.bic-fmla-input',
    'textarea#fe-qty-formula',
    'textarea#fe-condition-formula',
    'input#fm-formula',
    'input#ap-formula',
    'input#qp-formula',
    'input#ar-value-formula',
    'input#pd-formula',
  ]
  let count = 0
  for (const sel of selectors) {
    document.querySelectorAll(sel).forEach(el => {
      if (!el.dataset.cmInit) {
        const inline = el.matches('.bic-fmla-input') ||
          ['fm-formula','ap-formula','qp-formula','ar-value-formula','pd-formula'].includes(el.id)
        attachCmToInput(el, { parameters: paramList, inline, minHeight: inline ? 32 : 64 })
        count++
      }
    })
  }
  // Dynamic BOM fields
  document.querySelectorAll('[id^="bic-fields-"] .bic-fmla-input').forEach(el => {
    if (!el.dataset.cmInit) {
      attachCmToInput(el, { parameters: paramList, inline: true, minHeight: 32 })
      count++
    }
  })
  return count
}

export function refreshAllEditors() {
  for (const [, inst] of _cmInstances) inst.editor.refresh()
}

export function destroyAllEditors() {
  for (const [el, inst] of _cmInstances) {
    const wrap = inst.editor.getWrapperElement()
    if (wrap && wrap.parentNode) wrap.parentNode.remove()
    el.style.display = ''
    delete el.dataset.cmInit
  }
  _cmInstances.clear()
}

// ─── Global API ─────────────────────────────────────────────────────────────

window.CmFormulaEditor = {
  attachCmToInput, getCmInstance, insertAtCursor, initFormulaEditors,
  refreshAllEditors, destroyAllEditors, FORMULA_FUNCTIONS,
}

console.log('🔧 CmFormulaEditor (CM5) loaded, CodeMirror available:', typeof CodeMirror !== 'undefined')
