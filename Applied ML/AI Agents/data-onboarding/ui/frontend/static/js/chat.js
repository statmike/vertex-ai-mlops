/**
 * Chat mode — renders a scrolling conversation thread.
 *
 * Each question becomes a "conversation entry" with its own hero,
 * thinking timeline, and response parts.  Previous entries auto-collapse
 * to keep focus on the latest response.
 *
 * Response parts arrive sequentially (sql → data → chart → text)
 * and each renders as its own visual block.  SQL and data blocks are
 * collapsible so the key insight (text) stays prominent.
 *
 * Per-entry state machine:
 *   asking → thinking → responding → done
 *
 * Entries can originate from text input (source: 'text') or
 * voice questions (source: 'voice') — both render identically
 * except for the icon indicator.
 */

const Chat = {
    entries: [],     // [{question, timelineSteps, stepCounter, responseParts, state, source, startTime, activePersona}]
    current: null,   // pointer to the active entry (last in entries[])

    /** Start a new question — previous entries stay on screen. */
    ask(question, source) {
        const src = source || 'text';
        const entry = {
            question,
            timelineSteps: [],
            stepCounter: 0,
            responseParts: [],   // [{type, content/image_src}]
            state: 'asking',
            source: src,
            startTime: Date.now(),
            activePersona: null,
            pipelineStages: _initPipeline(src),
        };
        this.entries.push(entry);
        this.current = entry;
        this.render();
    },

    /** Handle a parsed event from the WebSocket. */
    handleEvent(event) {
        const c = this.current;
        if (!c) return;

        switch (event.type) {
            case 'status':
                if (event.content === 'Processing...') {
                    c.state = 'thinking';
                    _setPipelineStage(c, 'orchestrator', 'active');
                    this.render();
                } else if (event.content === 'done') {
                    c.state = 'done';
                    _setPipelineStage(c, 'result', 'done');
                    this.render();
                }
                break;

            case 'transfer':
                c.state = 'thinking';
                c.activePersona = event.to;
                _setPipelineStage(c, 'orchestrator', 'done');
                _setPipelineStage(c, 'persona', 'active',
                    _agentLabel(event.to), _agentIcon(event.to));
                this._addStep(c, 'route',
                    `Routing to ${_agentLabel(event.to)}`,
                    _agentIcon(event.to));
                break;

            case 'thinking':
                c.state = 'thinking';
                _setPipelineStage(c, 'persona', 'done');
                _setPipelineStage(c, 'tools', 'active', event.label, _toolIcon(event.tool));
                this._addStep(c, 'tool', event.label, _toolIcon(event.tool));
                break;

            case 'sql':
                c.state = 'responding';
                _setPipelineStage(c, 'tools', 'done');
                _setPipelineStage(c, 'result', 'active');
                c.responseParts.push({ type: 'sql', content: event.content, persona: c.activePersona });
                this.render();
                break;

            case 'data':
                c.state = 'responding';
                _setPipelineStage(c, 'tools', 'done');
                _setPipelineStage(c, 'result', 'active');
                c.responseParts.push({ type: 'data', content: event.content, persona: c.activePersona });
                this.render();
                break;

            case 'chart':
                c.state = 'responding';
                _setPipelineStage(c, 'tools', 'done');
                _setPipelineStage(c, 'result', 'active');
                c.responseParts.push({
                    type: 'chart',
                    image_src: event.image_src || null,
                    vega_spec: event.vega_spec || null,
                    persona: c.activePersona,
                });
                this.render();
                break;

            case 'text':
                if (event.role === 'user') break;
                if (event.is_answer || c.state === 'thinking') {
                    c.state = 'responding';
                }
                _setPipelineStage(c, 'tools', 'done');
                _setPipelineStage(c, 'result', 'active');
                c.responseParts.push({ type: 'text', content: event.content, persona: c.activePersona });
                this.render();
                break;

            case 'error':
                c.responseParts.push({ type: 'text', content: `Error: ${event.content}`, persona: c.activePersona });
                c.state = 'done';
                this.render();
                break;
        }
    },

    /**
     * Backfill historical events — replays stored events to rebuild the
     * text panel when toggling it on after voice-only operation.
     */
    backfill(events) {
        for (const event of events) {
            if (event.type === 'question') {
                this.ask(event.content, event._source || 'text');
                if (this.current) this.current.state = 'thinking';
            } else {
                this.handleEvent(event);
            }
        }
    },

    /** Add a step to an entry's thinking timeline. */
    _addStep(entry, type, label, icon) {
        const now = Date.now();
        entry.stepCounter++;
        // Mark previous steps done and compute elapsed time
        entry.timelineSteps.forEach(s => {
            if (s.status === 'active') {
                s.status = 'done';
                s.elapsed = now - s.ts;
            }
        });
        entry.timelineSteps.push({
            num: entry.stepCounter,
            type,
            label,
            icon,
            status: 'active',
            ts: now,
            elapsed: null,
        });
        this.render();
    },

    /** Render the full conversation thread. */
    render() {
        const container = document.getElementById('chat-content');
        if (!container) return;

        // Empty state
        if (this.entries.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="material-symbols-outlined icon">auto_awesome</span>
                    <p>Ask a question about your onboarded data</p>
                    <div class="suggested-queries">
                        <button class="chip suggested-query">What tables are available?</button>
                        <button class="chip suggested-query">Show me the processing log</button>
                        <button class="chip suggested-query">What does this dataset contain?</button>
                    </div>
                </div>
            `;
            return;
        }

        let html = '';

        for (let i = 0; i < this.entries.length; i++) {
            const e = this.entries[i];
            const isLatest = i === this.entries.length - 1;
            const voiceCls = e.source === 'voice' ? ' voice-origin' : '';
            const cls = isLatest
                ? `conversation-entry latest${voiceCls}`
                : `conversation-entry previous${voiceCls}`;

            html += `<div class="${cls}">`;

            if (isLatest) {
                html += _renderFullEntry(e, i, true);
            } else {
                html += _renderCollapsedEntry(e, i);
            }

            html += '</div>'; // conversation-entry
        }

        // Smart auto-scroll: only scroll to bottom if user was already near bottom
        const wasNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
        container.innerHTML = '<div class="chat-spacer"></div>' + html;
        if (wasNearBottom) container.scrollTop = container.scrollHeight;

        // Wire up toggle buttons and render Vega charts after innerHTML is set
        _wireToggles(container);
        _renderVegaCharts(container);
    },
};


// --- Entry rendering ---

/** Icon for the source — mic for voice, sparkle for text. */
function _sourceIcon(source) {
    return source === 'voice' ? 'mic' : 'auto_awesome';
}

/** Format elapsed ms as human-readable. */
function _formatElapsed(ms) {
    if (ms == null) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
}

/** Render the full current entry with expandable details. */
function _renderFullEntry(e, idx, isLatest) {
    let html = '';
    const icon = _sourceIcon(e.source);

    // Question hero
    const channelLabel = e.source === 'voice' ? 'Voice Inquiry' : 'Text Inquiry';
    html += `
        <div class="question-hero">
            <div class="label">
                <span class="material-symbols-outlined" style="font-size: 0.75rem;">${icon}</span>
                ${channelLabel}
            </div>
            <h1>${_highlightQuestion(e.question)}</h1>
        </div>
    `;

    html += '<div class="response-layout">';

    // Pipeline bar — shows overall flow
    html += _renderPipelineBar(e.pipelineStages);

    // Timeline — collapsible
    if (e.timelineSteps.length > 0) {
        // Compute total elapsed
        const totalMs = Date.now() - e.startTime;
        const totalLabel = e.state === 'done' ? _formatElapsed(totalMs) : 'in progress';

        html += `
            <div class="collapsible">
                <button class="collapsible-toggle" data-target="timeline-${idx}">
                    <span class="material-symbols-outlined toggle-icon">expand_more</span>
                    <span>${e.timelineSteps.length} step${e.timelineSteps.length > 1 ? 's' : ''}</span>
                    <span class="step-timing">${totalLabel}</span>
                </button>
                <div class="collapsible-body open" id="timeline-${idx}">
                    <div class="timeline">
        `;
        for (const step of e.timelineSteps) {
            const timing = step.elapsed != null ? `<span class="step-timing">${_formatElapsed(step.elapsed)}</span>` : '';
            html += `
                <div class="timeline-step ${step.status}">
                    <div class="timeline-icon">
                        <span class="material-symbols-outlined">${step.icon}</span>
                    </div>
                    <div class="timeline-label">
                        <span class="step-num">Step ${String(step.num).padStart(2, '0')}</span>
                        <span class="step-text">${step.label}</span>
                    </div>
                    ${timing}
                </div>
            `;
        }
        html += '</div></div></div>';
    }

    // Response parts
    if (e.responseParts.length > 0) {
        html += '<div class="response-card"><div class="inner">';
        html += _renderParts(e.responseParts, idx, false);
        html += '</div></div>';
    } else if (e.state === 'thinking') {
        html += `
            <div class="response-card">
                <div class="inner" style="text-align: center; padding: 3rem;">
                    <span class="material-symbols-outlined" style="font-size: 2rem; color: var(--primary); opacity: 0.5;">hourglass_top</span>
                    <p style="color: var(--on-surface-variant); margin-top: 1rem;">Analyzing...</p>
                </div>
            </div>
        `;
    }

    html += '</div>'; // response-layout
    return html;
}


/** Render a collapsed previous entry — question + final answer only. */
function _renderCollapsedEntry(e, idx) {
    let html = '';
    const icon = _sourceIcon(e.source);
    const totalMs = e.startTime ? Date.now() - e.startTime : null;

    // Compact question
    const collapsedChannelLabel = e.source === 'voice' ? 'Voice' : 'Text';
    html += `
        <div class="question-hero compact">
            <div class="label">
                <span class="material-symbols-outlined" style="font-size: 0.75rem;">${icon}</span>
                ${collapsedChannelLabel} #${idx + 1}
                ${totalMs != null ? `<span class="step-timing">${_formatElapsed(totalMs)}</span>` : ''}
            </div>
            <h1>${_highlightQuestion(e.question)}</h1>
        </div>
    `;

    // Show only the last text part (the final answer) inline
    const textParts = e.responseParts.filter(p => p.type === 'text');
    const lastText = textParts.length > 0 ? textParts[textParts.length - 1].content : '';
    const hasDetails = e.responseParts.some(p => p.type === 'sql' || p.type === 'data' || p.type === 'chart');

    if (lastText) {
        html += `
            <div class="response-card compact">
                <div class="inner">
                    <div class="insight-card">
                        <div class="insight-icon">
                            <span class="material-symbols-outlined">${icon}</span>
                        </div>
                        <div class="insight-text markdown-content">
                            ${_renderMarkdown(lastText)}
                        </div>
                    </div>
        `;

        // Expandable detail section
        if (hasDetails) {
            const detailCount = e.responseParts.filter(p => p.type !== 'text').length;
            html += `
                <div class="collapsible" style="margin-top: 1rem;">
                    <button class="collapsible-toggle" data-target="details-${idx}">
                        <span class="material-symbols-outlined toggle-icon">chevron_right</span>
                        <span>${detailCount} detail${detailCount > 1 ? 's' : ''} (SQL, data${e.responseParts.some(p => p.type === 'chart') ? ', chart' : ''})</span>
                    </button>
                    <div class="collapsible-body" id="details-${idx}">
                        ${_renderParts(e.responseParts.filter(p => p.type !== 'text'), idx, true)}
                    </div>
                </div>
            `;
        }

        html += '</div></div>';
    }

    return html;
}


// --- Part rendering ---

/** Render a persona section header when the persona changes. */
function _renderPersonaSection(persona) {
    if (!persona) return '';
    const label = _agentLabel(persona);
    const icon = _agentIcon(persona);
    const cls = _personaClass(persona);
    return `<div class="persona-section ${cls}"><div class="persona-header"><span class="material-symbols-outlined">${icon}</span><span>${label}</span></div></div>`;
}

/** Render an ordered list of response parts as distinct visual blocks. */
function _renderParts(parts, entryIdx, collapsed) {
    let html = '';
    let sqlCount = 0;
    let dataCount = 0;
    let lastPersona = null;

    for (const part of parts) {
        // Show persona section header when it changes
        if (part.persona && part.persona !== lastPersona) {
            html += _renderPersonaSection(part.persona);
            lastPersona = part.persona;
        }

        switch (part.type) {
            case 'sql':
                sqlCount++;
                const sqlId = `sql-${entryIdx}-${sqlCount}`;
                html += `
                    <div class="part-sql collapsible">
                        <button class="collapsible-toggle" data-target="${sqlId}">
                            <span class="material-symbols-outlined toggle-icon">chevron_right</span>
                            <span class="material-symbols-outlined" style="font-size: 0.875rem; color: var(--primary);">code</span>
                            <span>SQL Query${sqlCount > 1 ? ' ' + sqlCount : ''}</span>
                        </button>
                        <div class="collapsible-body${collapsed ? '' : ' open'}" id="${sqlId}">
                            <pre><code>${_escapeHtml(part.content)}</code></pre>
                        </div>
                    </div>
                `;
                break;

            case 'data':
                dataCount++;
                const dataId = `data-${entryIdx}-${dataCount}`;
                html += `
                    <div class="part-data collapsible">
                        <button class="collapsible-toggle" data-target="${dataId}">
                            <span class="material-symbols-outlined toggle-icon">chevron_right</span>
                            <span class="material-symbols-outlined" style="font-size: 0.875rem; color: var(--primary);">table_chart</span>
                            <span>Query Results${dataCount > 1 ? ' ' + dataCount : ''}</span>
                        </button>
                        <div class="collapsible-body${collapsed ? '' : ' open'}" id="${dataId}">
                            ${_renderDataTable(part.content)}
                        </div>
                    </div>
                `;
                break;

            case 'chart':
                if (part.vega_spec) {
                    const specJson = JSON.stringify(part.vega_spec).replace(/'/g, '&#39;');
                    html += `<div class="vega-placeholder chart-container" data-spec='${specJson}'></div>`;
                } else if (part.image_src) {
                    html += `
                        <div class="chart-container">
                            <img src="${part.image_src}" alt="Chart" />
                        </div>
                    `;
                }
                break;

            case 'text':
                html += `
                    <div class="insight-card">
                        <div class="insight-icon">
                            <span class="material-symbols-outlined">auto_awesome</span>
                        </div>
                        <div class="insight-text markdown-content">
                            ${_renderMarkdown(part.content)}
                        </div>
                    </div>
                `;
                break;
        }
    }
    return html;
}


/** Detect and render Vega-Lite specs embedded in text. */
function _renderVegaCharts(container) {
    container.querySelectorAll('.vega-placeholder').forEach(el => {
        try {
            const spec = JSON.parse(el.dataset.spec);

            // Use the container's actual width (minus padding)
            const containerWidth = el.clientWidth - 32; // 1rem padding each side
            const chartWidth = Math.max(containerWidth, 400);

            // Apply dark theme defaults
            spec.background = 'transparent';
            spec.config = spec.config || {};
            spec.config.axis = { ...spec.config.axis, labelColor: '#a7abb6', titleColor: '#a7abb6', gridColor: 'rgba(68,72,82,0.2)' };
            spec.config.legend = { ...spec.config.legend, labelColor: '#a7abb6', titleColor: '#a7abb6' };
            spec.config.title = { ...spec.config.title, color: '#e0e2ea' };
            spec.config.view = { stroke: 'transparent' };
            spec.config.mark = { ...spec.config.mark, color: '#85adff' };
            spec.width = chartWidth;
            spec.height = Math.round(chartWidth * 0.5);
            spec.autosize = { type: 'fit', contains: 'padding' };

            vegaEmbed(el, spec, {
                actions: false,
                renderer: 'svg',
                theme: 'dark',
            }).catch(err => {
                el.innerHTML = `<p style="color: var(--error);">Chart render error: ${_escapeHtml(err.message)}</p>`;
            });
        } catch (err) {
            console.error('Vega parse error:', err);
        }
    });
}

/** Wire up all collapsible toggle buttons. */
function _wireToggles(container) {
    container.querySelectorAll('.collapsible-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;
            const body = document.getElementById(targetId);
            if (!body) return;
            const isOpen = body.classList.toggle('open');
            const icon = btn.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = isOpen ? 'expand_more' : 'chevron_right';
            }
        });
    });
}


/** Convert a plain-text table (from pandas .to_string()) into an HTML table. */
function _renderDataTable(text) {
    const lines = text.split('\n').filter(l => l.trim());

    // Skip header like "## Data retrieved"
    let start = 0;
    while (start < lines.length && lines[start].trim().startsWith('#')) start++;
    if (start >= lines.length) return `<pre>${_escapeHtml(text)}</pre>`;

    // First non-header line is column names (space-aligned)
    const headerLine = lines[start];
    const dataLines = lines.slice(start + 1);

    // Parse space-aligned columns by finding column boundaries
    const columns = headerLine.trim().split(/\s{2,}/);
    if (columns.length < 2) return `<pre>${_escapeHtml(text)}</pre>`;

    let html = '<div style="overflow-x: auto;"><table class="data-table"><thead><tr>';
    columns.forEach(c => html += `<th>${_escapeHtml(c)}</th>`);
    html += '</tr></thead><tbody>';

    for (const line of dataLines) {
        if (!line.trim()) continue;
        const cells = line.trim().split(/\s{2,}/);
        html += '<tr>';
        for (let i = 0; i < columns.length; i++) {
            html += `<td>${_escapeHtml(cells[i] || '')}</td>`;
        }
        html += '</tr>';
    }

    html += '</tbody></table></div>';
    return html;
}


// --- Label helpers ---

function _agentLabel(agentName) {
    const labels = {
        'agent_context': 'Data Analyst',
        'agent_convo': 'Data Analyst',
        'agent_engineer': 'Data Engineer',
        'agent_catalog': 'Catalog Explorer',
        'agent_orchestrator': 'Orchestrator',
        'agent_chat': 'Chat Agent',
    };
    return labels[agentName] || agentName;
}

function _agentIcon(agentName) {
    const icons = {
        'agent_context': 'analytics',
        'agent_convo': 'query_stats',
        'agent_engineer': 'engineering',
        'agent_catalog': 'menu_book',
        'agent_orchestrator': 'hub',
        'agent_chat': 'smart_toy',
    };
    return icons[agentName] || 'smart_toy';
}

function _personaClass(agentName) {
    const classes = {
        'agent_context': 'analyst',
        'agent_convo': 'analyst',
        'agent_engineer': 'engineer',
        'agent_catalog': 'catalog',
        'agent_orchestrator': 'orchestrator',
        'agent_chat': 'orchestrator',
    };
    return classes[agentName] || 'orchestrator';
}

function _toolIcon(toolName) {
    const icons = {
        'rerank_tables': 'filter_list',
        'conversational_chat': 'query_stats',
        'meta_chat': 'engineering',
        'search_context': 'search',
        'get_table_columns': 'table_chart',
        'list_all_tables': 'dataset',
    };
    return icons[toolName] || 'build';
}

// --- Pipeline helpers ---

function _initPipeline(source) {
    const stages = [
        { key: 'input', icon: _sourceIcon(source), label: source === 'voice' ? 'Voice' : 'Text', status: 'done' },
    ];
    if (source === 'voice') {
        stages.push({ key: 'voice_agent', icon: 'record_voice_over', label: 'Voice Agent', status: 'done' });
    }
    stages.push(
        { key: 'orchestrator', icon: 'hub', label: 'Orchestrator', status: 'pending' },
        { key: 'persona', icon: 'smart_toy', label: 'Routing...', status: 'pending' },
        { key: 'tools', icon: 'build', label: 'Tools', status: 'pending' },
        { key: 'result', icon: 'auto_awesome', label: 'Results', status: 'pending' },
    );
    return stages;
}

function _setPipelineStage(entry, key, status, label, icon) {
    if (!entry.pipelineStages) return;
    const stage = entry.pipelineStages.find(s => s.key === key);
    if (!stage) return;
    stage.status = status;
    if (label) stage.label = label;
    if (icon) stage.icon = icon;
}

function _renderPipelineBar(stages) {
    if (!stages || stages.length === 0) return '';
    let html = '<div class="pipeline-bar">';
    for (let i = 0; i < stages.length; i++) {
        const s = stages[i];
        html += `<div class="pipeline-stage ${s.status}">`;
        html += `<span class="material-symbols-outlined">${s.icon}</span>`;
        html += `<span class="pipeline-label">${s.label}</span>`;
        html += '</div>';
        if (i < stages.length - 1) {
            // Connector status: done if both sides done, active if next is active, else pending
            const nextStatus = stages[i + 1].status;
            const connStatus = s.status === 'done' && nextStatus !== 'pending' ? 'done'
                             : nextStatus === 'active' ? 'active' : 'pending';
            html += `<div class="pipeline-connector ${connStatus}"></div>`;
        }
    }
    html += '</div>';
    return html;
}

function _highlightQuestion(text) {
    return _escapeHtml(text).replace(
        /(&quot;.*?&quot;|&#39;.*?&#39;|\b(?:VIX|SPY|CBOE|FINRA|IBM|CAD|JPY|FX)\b)/gi,
        '<span class="highlight">$1</span>'
    );
}


// --- Markdown / text rendering ---

function _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function _renderMarkdown(text) {
    // Extract Vega-Lite JSON blocks before escaping
    const vegaCharts = [];
    let processed = text.replace(
        /```?json\s*\n?([\s\S]*?)\n?```?/gi,
        (match, jsonStr) => {
            try {
                const obj = JSON.parse(jsonStr.trim());
                if (obj.mark && obj.encoding) {
                    const id = `vega-${Date.now()}-${vegaCharts.length}`;
                    vegaCharts.push({ id, spec: jsonStr.trim() });
                    return `%%VEGA:${id}%%`;
                }
            } catch {}
            return match;
        }
    );

    // Also catch JSON without code fences (bare Vega-Lite in text)
    processed = processed.replace(
        /(\{[\s\S]*?"mark"\s*:\s*"[^"]+?"[\s\S]*?"encoding"\s*:\s*\{[\s\S]*?\}\s*\})/g,
        (match) => {
            try {
                const obj = JSON.parse(match);
                if (obj.mark && obj.encoding) {
                    const id = `vega-${Date.now()}-${vegaCharts.length}`;
                    vegaCharts.push({ id, spec: match });
                    return `%%VEGA:${id}%%`;
                }
            } catch {}
            return match;
        }
    );

    let html = _escapeHtml(processed)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');

    if (html.includes('|') && html.includes('---')) {
        html = _renderMarkdownTable(processed);
    }

    // Replace Vega placeholders with chart containers
    for (const chart of vegaCharts) {
        html = html.replace(
            `%%VEGA:${chart.id}%%`,
            `<div class="vega-placeholder chart-container" id="${chart.id}" data-spec='${chart.spec.replace(/'/g, "&#39;")}'></div>`
        );
    }

    return html;
}

function _renderMarkdownTable(text) {
    const lines = text.split('\n');
    let inTable = false;
    let tableHtml = '';
    let otherHtml = '';

    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
            if (trimmed.replace(/[|\-\s]/g, '') === '') continue;
            if (!inTable) {
                inTable = true;
                tableHtml += '<div style="overflow-x: auto;"><table class="data-table"><thead><tr>';
                const cells = trimmed.split('|').filter(c => c.trim());
                cells.forEach(c => tableHtml += `<th>${_escapeHtml(c.trim())}</th>`);
                tableHtml += '</tr></thead><tbody>';
            } else {
                tableHtml += '<tr>';
                const cells = trimmed.split('|').filter(c => c.trim());
                cells.forEach(c => {
                    let val = _escapeHtml(c.trim())
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    tableHtml += `<td>${val}</td>`;
                });
                tableHtml += '</tr>';
            }
        } else {
            if (inTable) {
                tableHtml += '</tbody></table></div>';
                inTable = false;
            }
            let rendered = _escapeHtml(trimmed)
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/`(.*?)`/g, '<code>$1</code>');
            if (rendered) otherHtml += `<p>${rendered}</p>`;
        }
    }

    if (inTable) tableHtml += '</tbody></table></div>';
    return otherHtml + tableHtml;
}
