import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import io
import base64
import json


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return data


BG     = '#0a1628'
BG2    = '#112240'
BG3    = '#162a4a'
GOLD   = '#c9a84c'
GOLD2  = '#e8c97a'
GREEN  = '#1db87a'
RED    = '#e05252'
AMBER  = '#f0a500'
BLUE   = '#4a9eff'
MUTED  = '#8892a4'
TEXT   = '#e8e4da'


def set_dark_style(fig, axes=None):
    fig.patch.set_facecolor(BG2)
    if axes is not None:
        for ax in (list(axes.flat) if hasattr(axes, "flat") else (axes if isinstance(axes, list) else [axes])):
            ax.set_facecolor(BG3)
            ax.tick_params(colors=MUTED, labelsize=9)
            ax.xaxis.label.set_color(MUTED)
            ax.yaxis.label.set_color(MUTED)
            for spine in ax.spines.values():
                spine.set_edgecolor('#1e3a5f')
            ax.grid(color='#1e3a5f', linestyle='--', linewidth=0.5, alpha=0.7)


# ── 1. RISK GAUGE CHART ──────────────────────────────────────────────────────
def generate_risk_gauge(credit_score: int, dti: float, lti: float) -> str:
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    set_dark_style(fig, axes)
    fig.suptitle('Risk Assessment Dashboard', color=TEXT, fontsize=13, fontweight='bold', y=1.02)

    configs = [
        {
            'ax': axes[0], 'title': 'Credit Score',
            'value': credit_score, 'min': 300, 'max': 900,
            'thresholds': [(600, RED), (700, AMBER), (900, GREEN)],
            'label': f'{credit_score}',
            'zones': ['Poor\n< 600', 'Fair\n600–700', 'Good\n> 700']
        },
        {
            'ax': axes[1], 'title': 'Debt-to-Income Ratio',
            'value': dti * 100, 'min': 0, 'max': 80,
            'thresholds': [(40, GREEN), (55, AMBER), (80, RED)],
            'label': f'{dti*100:.1f}%',
            'zones': ['Good\n< 40%', 'High\n40–55%', 'Risk\n> 55%']
        },
        {
            'ax': axes[2], 'title': 'Loan-to-Income Ratio',
            'value': lti, 'min': 0, 'max': 12,
            'thresholds': [(5, GREEN), (8, AMBER), (12, RED)],
            'label': f'{lti:.2f}x',
            'zones': ['Good\n< 5x', 'High\n5–8x', 'Risk\n> 8x']
        },
    ]

    for cfg in configs:
        ax = cfg['ax']
        ax.set_facecolor(BG3)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.axis('off')

        # Title
        ax.text(5, 5.5, cfg['title'], ha='center', va='center',
                color=TEXT, fontsize=10, fontweight='bold')

        # Background bar
        bar_y, bar_h = 3.0, 0.7
        ax.add_patch(mpatches.FancyBboxPatch((0.5, bar_y), 9, bar_h,
            boxstyle="round,pad=0.1", facecolor='#1e3a5f', edgecolor='none'))

        # Color zones
        mn, mx = cfg['min'], cfg['max']
        zone_colors = [GREEN, AMBER, RED]
        zone_bounds = [mn] + [t[0] for t in cfg['thresholds']]
        for i in range(len(zone_bounds) - 1):
            x0 = 0.5 + (zone_bounds[i] - mn) / (mx - mn) * 9
            w  = (zone_bounds[i+1] - zone_bounds[i]) / (mx - mn) * 9
            ax.add_patch(mpatches.FancyBboxPatch((x0, bar_y), w, bar_h,
                boxstyle="round,pad=0.05",
                facecolor=zone_colors[i], alpha=0.25, edgecolor='none'))

        # Fill to value
        fill_w = min((cfg['value'] - mn) / (mx - mn), 1.0) * 9
        # Pick fill color
        fill_color = RED
        for thresh, color in cfg['thresholds']:
            if cfg['value'] <= thresh:
                fill_color = color
                break
        ax.add_patch(mpatches.FancyBboxPatch((0.5, bar_y), fill_w, bar_h,
            boxstyle="round,pad=0.05", facecolor=fill_color, alpha=0.9, edgecolor='none'))

        # Needle / marker
        needle_x = 0.5 + fill_w
        ax.plot([needle_x, needle_x], [bar_y - 0.2, bar_y + bar_h + 0.2],
                color=TEXT, linewidth=2.5, zorder=5)
        ax.add_patch(plt.Circle((needle_x, bar_y + bar_h + 0.35), 0.18,
                                color=fill_color, zorder=6))

        # Value label
        ax.text(5, bar_y - 0.7, cfg['label'], ha='center', va='center',
                color=fill_color, fontsize=16, fontweight='bold')

        # Zone labels
        for i, zlabel in enumerate(cfg['zones']):
            x_pos = 0.5 + (zone_bounds[i] + zone_bounds[i+1]) / 2 / (mx - mn) * 9 - \
                    zone_bounds[0] / (mx - mn) * 9
            ax.text(x_pos, bar_y - 1.6, zlabel, ha='center', va='center',
                    color=MUTED, fontsize=7)

        for sp in ax.spines.values():
            sp.set_visible(False)

    plt.tight_layout(pad=1.5)
    return fig_to_base64(fig)


# ── 2. WORKFLOW TIMELINE CHART ────────────────────────────────────────────────
def generate_workflow_timeline(audit_trail: list) -> str:
    fig, ax = plt.subplots(figsize=(11, 4))
    set_dark_style(fig, ax)
    ax.set_facecolor(BG2)
    fig.patch.set_facecolor(BG2)

    stage_icons = {
        'intake': '📥', 'eligibility_check': '📋',
        'credit_check': '🏦', 'risk_assessment': '⚖️', 'final_decision': '🎯'
    }
    stage_labels = {
        'intake': 'Intake', 'eligibility_check': 'Eligibility',
        'credit_check': 'Credit\nBureau', 'risk_assessment': 'Risk\nAssessment',
        'final_decision': 'Final\nDecision'
    }

    status_colors = {
        'success': GREEN, 'pass': GREEN, 'approved': GREEN,
        'fail': RED, 'rejected': RED,
        'manual_review': AMBER,
    }

    n = len(audit_trail)
    xs = np.linspace(1, 9, n)

    # Connecting line
    ax.plot(xs, [2.5] * n, color='#1e3a5f', linewidth=3, zorder=1)

    from datetime import datetime
    times = []
    for entry in audit_trail:
        try:
            t = datetime.fromisoformat(entry['created_at'])
            times.append(t)
        except:
            times.append(None)

    for i, (entry, x) in enumerate(zip(audit_trail, xs)):
        color = status_colors.get(entry['status'], BLUE)
        label = stage_labels.get(entry['stage'], entry['stage'])

        # Circle node
        circle = plt.Circle((x, 2.5), 0.38, color=color, zorder=3, alpha=0.9)
        ax.add_patch(circle)
        outline = plt.Circle((x, 2.5), 0.42, fill=False, edgecolor=color, linewidth=2, zorder=2, alpha=0.4)
        ax.add_patch(outline)

        # Status icon inside circle
        status_sym = '✓' if color == GREEN else ('✗' if color == RED else '?')
        ax.text(x, 2.5, status_sym, ha='center', va='center',
                color='white', fontsize=11, fontweight='bold', zorder=4)

        # Stage label below
        ax.text(x, 1.5, label, ha='center', va='top',
                color=TEXT, fontsize=8, fontweight='bold', multialignment='center')

        # Time above (alternating)
        if times[i]:
            t_str = times[i].strftime('%H:%M:%S')
            y_pos = 3.5 if i % 2 == 0 else 4.1
            ax.text(x, y_pos, t_str, ha='center', va='bottom',
                    color=MUTED, fontsize=7.5)
            ax.plot([x, x], [2.9, y_pos - 0.05], color='#1e3a5f',
                    linewidth=1, linestyle=':', zorder=1)

        # Arrow between nodes
        if i < n - 1:
            x_next = xs[i + 1]
            ax.annotate('', xy=(x_next - 0.42, 2.5), xytext=(x + 0.42, 2.5),
                        arrowprops=dict(arrowstyle='->', color=MUTED,
                                        lw=1.5, mutation_scale=14), zorder=2)

    ax.set_xlim(0, 10)
    ax.set_ylim(0.8, 4.8)
    ax.axis('off')
    ax.set_title('Workflow Execution Timeline', color=TEXT, fontsize=12,
                 fontweight='bold', pad=10)

    # Legend
    legend_items = [
        mpatches.Patch(facecolor=GREEN, label='Passed'),
        mpatches.Patch(facecolor=AMBER, label='Manual Review'),
        mpatches.Patch(facecolor=RED,   label='Failed'),
    ]
    ax.legend(handles=legend_items, loc='lower right', framealpha=0.15,
              facecolor=BG3, edgecolor='#1e3a5f', labelcolor=MUTED, fontsize=8)

    plt.tight_layout(pad=1.2)
    return fig_to_base64(fig)


# ── 3. RULES BREAKDOWN BAR CHART ─────────────────────────────────────────────
def generate_rules_breakdown(audit_trail: list) -> str:
    all_rules = []
    for entry in audit_trail:
        try:
            rules = json.loads(entry['rules_triggered'])
            for r in rules:
                status = 'pass'
                if 'FAIL' in r or 'REJECT' in r:
                    status = 'fail'
                elif 'MANUAL_REVIEW' in r:
                    status = 'review'
                label = r.split(':')[0].replace('_', ' ').title()
                all_rules.append({'label': label, 'status': status, 'stage': entry['stage']})
        except:
            pass

    if not all_rules:
        return None

    fig, ax = plt.subplots(figsize=(11, max(3.5, len(all_rules) * 0.45 + 1.5)))
    set_dark_style(fig, ax)

    colors_map = {'pass': GREEN, 'fail': RED, 'review': AMBER}
    labels = [r['label'] for r in all_rules]
    colors = [colors_map[r['status']] for r in all_rules]
    values = [1] * len(all_rules)

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=colors, alpha=0.8, height=0.6,
                   edgecolor='none')

    # Status text on bars
    for i, (bar, rule) in enumerate(zip(bars, all_rules)):
        sym = '✓ PASS' if rule['status'] == 'pass' else ('✗ FAIL' if rule['status'] == 'fail' else '⚠ REVIEW')
        ax.text(0.02, i, sym, va='center', color='white',
                fontsize=8, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT, fontsize=9)
    ax.set_xticks([])
    ax.set_xlim(0, 1.3)
    ax.set_title('Rule-by-Rule Evaluation Results', color=TEXT,
                 fontsize=12, fontweight='bold', pad=10)
    ax.invert_yaxis()

    # Legend
    legend_items = [
        mpatches.Patch(facecolor=GREEN, label='Pass'),
        mpatches.Patch(facecolor=AMBER, label='Manual Review'),
        mpatches.Patch(facecolor=RED,   label='Fail'),
    ]
    ax.legend(handles=legend_items, loc='lower right', framealpha=0.15,
              facecolor=BG3, edgecolor='#1e3a5f', labelcolor=MUTED, fontsize=9)

    for sp in ['top', 'right', 'bottom']:
        ax.spines[sp].set_visible(False)
    ax.spines['left'].set_edgecolor('#1e3a5f')

    plt.tight_layout(pad=1.2)
    return fig_to_base64(fig)


# ── 4. APPLICANT PROFILE RADAR ────────────────────────────────────────────────
def generate_applicant_radar(app_data: dict, metrics: dict) -> str:
    fig, ax = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(BG2)
    ax.set_facecolor(BG3)

    categories = ['Income\nStrength', 'Credit\nScore', 'Employment\nStability',
                  'Loan\nAffordability', 'Repayment\nCapacity']
    N = len(categories)

    # Normalize scores 0–1
    income    = min(app_data.get('annual_income', 0) / 2000000, 1.0)
    credit    = min((metrics.get('credit_score', 300) - 300) / 600, 1.0)
    employ    = min(app_data.get('employment_months', 0) / 120, 1.0)
    affordability = max(0, 1 - metrics.get('lti', 0) / 10)
    repayment = max(0, 1 - metrics.get('dti', 0) / 0.6)

    values = [income, credit, employ, affordability, repayment]
    values_pct = [round(v * 100) for v in values]

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    values_plot = values + [values[0]]
    angles_plot = angles + [angles[0]]

    # Grid rings
    for level in [0.25, 0.5, 0.75, 1.0]:
        ring = [level] * (N + 1)
        ax.plot(angles_plot, ring, color='#1e3a5f', linewidth=0.8, linestyle='--')
        ax.fill(angles_plot[:N], ring[:N], alpha=0.0)

    # Fill area
    ax.fill(angles_plot, values_plot, alpha=0.25, color=GOLD)
    ax.plot(angles_plot, values_plot, color=GOLD, linewidth=2.5)

    # Data points
    for angle, val, pct in zip(angles, values, values_pct):
        color = GREEN if val > 0.65 else (AMBER if val > 0.35 else RED)
        ax.plot(angle, val, 'o', color=color, markersize=8, zorder=5)
        ax.text(angle, val + 0.13, f'{pct}%',
                ha='center', va='center', color=color, fontsize=8, fontweight='bold')

    # Category labels
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, color=TEXT, fontsize=8.5, fontweight='bold')
    ax.set_yticklabels([])
    ax.set_ylim(0, 1.15)
    ax.spines['polar'].set_edgecolor('#1e3a5f')
    ax.grid(color='#1e3a5f', linewidth=0.5)
    ax.set_title('Applicant Financial Profile', color=TEXT,
                 fontsize=12, fontweight='bold', pad=20)

    plt.tight_layout()
    return fig_to_base64(fig)


# ── 5. DECISION SUMMARY DONUT ─────────────────────────────────────────────────
def generate_decision_donut(audit_trail: list, final_status: str) -> str:
    pass_count    = sum(1 for e in audit_trail for r in json.loads(e.get('rules_triggered','[]'))
                        if 'PASS' in r or 'SUCCESS' in r or 'schema_validated' in r)
    fail_count    = sum(1 for e in audit_trail for r in json.loads(e.get('rules_triggered','[]'))
                        if 'FAIL' in r or 'REJECT' in r)
    review_count  = sum(1 for e in audit_trail for r in json.loads(e.get('rules_triggered','[]'))
                        if 'MANUAL_REVIEW' in r)

    total = pass_count + fail_count + review_count
    if total == 0:
        return None

    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor(BG2)
    ax.set_facecolor(BG2)

    sizes  = [pass_count, review_count, fail_count]
    colors = [GREEN, AMBER, RED]
    labels = [f'Passed ({pass_count})', f'Review ({review_count})', f'Failed ({fail_count})']

    # Remove zero slices
    filtered = [(s, c, l) for s, c, l in zip(sizes, colors, labels) if s > 0]
    if not filtered:
        return None
    sizes, colors, labels = zip(*filtered)

    wedges, texts = ax.pie(
        sizes, colors=colors, startangle=90,
        wedgeprops=dict(width=0.55, edgecolor=BG2, linewidth=3),
        pctdistance=0.85
    )

    # Center text
    status_display = {'approved': ('✅', 'Approved', GREEN),
                      'rejected': ('❌', 'Rejected', RED),
                      'manual_review': ('🔍', 'Review', AMBER)}.get(
        final_status, ('⏳', final_status, BLUE))
    ax.text(0, 0.1,  status_display[0], ha='center', va='center', fontsize=22)
    ax.text(0, -0.2, status_display[1], ha='center', va='center',
            fontsize=12, fontweight='bold', color=status_display[2])
    ax.text(0, -0.45, f'{total} rules checked', ha='center', va='center',
            fontsize=9, color=MUTED)

    ax.legend(wedges, labels, loc='lower center', bbox_to_anchor=(0.5, -0.12),
              framealpha=0.1, facecolor=BG3, edgecolor='#1e3a5f',
              labelcolor=TEXT, fontsize=9, ncol=len(labels))

    ax.set_title('Rules Outcome Summary', color=TEXT,
                 fontsize=12, fontweight='bold', pad=10)

    plt.tight_layout()
    return fig_to_base64(fig)


# ── MASTER FUNCTION ────────────────────────────────────────────────────────────
def generate_all_charts(audit_data: dict, app_data: dict) -> dict:
    audit_trail  = audit_data.get('audit_trail', [])
    state_history = audit_data.get('state_history', [])
    final_status = state_history[-1]['to_status'] if state_history else 'unknown'

    # Extract metrics from risk stage
    metrics = {}
    for entry in audit_trail:
        if entry['stage'] == 'risk_assessment':
            try:
                metrics = json.loads(entry['data_snapshot'])
            except:
                pass

    charts = {}

    if metrics.get('credit_score') and metrics.get('dti') and metrics.get('lti'):
        charts['gauge']   = generate_risk_gauge(metrics['credit_score'], metrics['dti'], metrics['lti'])
        charts['radar']   = generate_applicant_radar(app_data, metrics)

    charts['timeline'] = generate_workflow_timeline(audit_trail)
    charts['rules']    = generate_rules_breakdown(audit_trail)
    charts['donut']    = generate_decision_donut(audit_trail, final_status)

    return charts