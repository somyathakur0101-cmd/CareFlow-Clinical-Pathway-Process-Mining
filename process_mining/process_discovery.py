"""CareFlow Process Discovery Module.

Discovers Directly-Follows Graphs (DFG), Process Variants, Start/End activity
distributions, and Inductive Miner Petri Nets using PM4Py, and generates
high-resolution process maps.

IMPORTANT NOTES ON CLINICAL INTERPRETATION:
- Results describe observed data patterns only. Activity sequences reflect
  timestamp ordering within each encounter case; they do not assert that a
  transition is clinically appropriate or causal.
- Multiple events at identical timestamps are ordered by event_index (a
  stable but arbitrary key). Do not read clinical sequence significance into
  such tie-broken orderings.
- Self-loop transitions (e.g., Lab -> Lab) indicate that a patient had
  multiple items of the same activity type within one encounter; they are NOT
  evidence of re-testing or clinical loops in the medical sense.
- Frequency alone does not imply that a pathway is a clinical best practice.

LIFECYCLE HANDLING:
- The event log uses one event per clinical entity with 'lifecycle' column
  indicating start/complete, but PM4Py process discovery operates on the
  single 'timestamp' field (the encounter-level ordering timestamp) to build
  case sequences. Separate start/complete lifecycle analysis is preserved in
  the event log but not used to split events for Petri net discovery, since
  the OPD source data does not have activity-level interleaving that would
  require lifecycle splitting.
"""

import csv
import os
import sys
import tempfile

# Set safe writable directory for matplotlib cache (before importing plt)
os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pm4py


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def resolve_file_path(target_path: str) -> str:
    """Find file in common relative locations (project root or nested repo)."""
    if os.path.exists(target_path):
        return target_path
    nested_path = os.path.join(
        "CareFlow-Clinical-Pathway-Process-Mining-giricharan525-debug", target_path
    )
    if os.path.exists(nested_path):
        return nested_path
    parent_path = os.path.join("..", target_path)
    if os.path.exists(parent_path):
        return parent_path
    return target_path


# ---------------------------------------------------------------------------
# Main discovery class
# ---------------------------------------------------------------------------

class CareFlowProcessDiscovery:
    """Discovers clinical pathways, transitions, variants, and Petri nets
    from CareFlow OPD event logs using PM4Py.

    Attributes
    ----------
    event_log_path : str
        Path to the CSV event log.
    df : pd.DataFrame or None
        PM4Py-formatted dataframe after load_event_log().
    dfg : dict or None
        Directly-Follows Graph: {(src, tgt): count}.
    start_activities : dict or None
        {activity: start_case_count}.
    end_activities : dict or None
        {activity: end_case_count}.
    variants : list[dict] or None
        Sorted variant list after discover_variants().
    petri_net : pm4py PetriNet or None
        Inductive Miner Petri net after discover_petri_net().
    initial_marking : pm4py Marking or None
    final_marking : pm4py Marking or None
    transition_stats : list[dict]
        DFG edge statistics after discover_dfg().
    activity_stats : list[dict]
        Per-activity frequency statistics after calculate_activity_stats().
    """

    # Expected constants derived from the validated event log generation.
    EXPECTED_EVENTS = 123_969
    EXPECTED_CASES = 49_912
    KNOWN_ACTIVITIES = frozenset({
        "Appointment Registration",
        "Doctor Consultation & Prescription",
        "Laboratory Examination",
        "Imaging Procedure",
        "Pharmacy Dispensing",
    })

    def __init__(self, event_log_path: str = None):
        if event_log_path is None:
            event_log_path = resolve_file_path(
                os.path.join("outputs", "careflow_event_log.csv")
            )
        self.event_log_path = event_log_path
        self.df = None
        self.dfg = None
        self.start_activities = None
        self.end_activities = None
        self.variants = None
        self.petri_net = None
        self.initial_marking = None
        self.final_marking = None
        self.transition_stats: list = []
        self.activity_stats: list = []

    # ------------------------------------------------------------------
    # Step 1: Load
    # ------------------------------------------------------------------

    def load_event_log(self) -> pd.DataFrame:
        """Load and format the event log dataframe for PM4Py.

        Returns
        -------
        pd.DataFrame
            PM4Py-formatted dataframe (adds 'case:concept:name', 'concept:name',
            'time:timestamp' standard XES column aliases).

        Raises
        ------
        FileNotFoundError
            If the CSV event log is not found at the configured path.
        ValueError
            If the loaded log does not contain required columns.
        """
        if not os.path.exists(self.event_log_path):
            raise FileNotFoundError(
                f"Event log not found at: {self.event_log_path}\n"
                "Run process_mining/event_log.py to generate it first."
            )

        print(f"Loading event log from: {self.event_log_path}")
        df = pd.read_csv(self.event_log_path)

        required = {"case_id", "activity", "timestamp"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Event log is missing required columns: {missing}")

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        self.df = pm4py.format_dataframe(
            df,
            case_id="case_id",
            activity_key="activity",
            timestamp_key="timestamp",
        )

        n_events = len(self.df)
        n_cases = self.df["case_id"].nunique()
        print(f"Loaded {n_events:,} events across {n_cases:,} unique cases.")

        # Warn if counts differ from expectation (do not raise – support
        # partial/filtered logs during testing).
        if n_events != self.EXPECTED_EVENTS:
            print(
                f"WARNING: Expected {self.EXPECTED_EVENTS:,} events, "
                f"got {n_events:,}. Log may be filtered or regenerated."
            )
        if n_cases != self.EXPECTED_CASES:
            print(
                f"WARNING: Expected {self.EXPECTED_CASES:,} cases, "
                f"got {n_cases:,}."
            )

        return self.df

    # ------------------------------------------------------------------
    # Step 2: DFG
    # ------------------------------------------------------------------

    def discover_dfg(self):
        """Discover Directly-Follows Graph and per-edge transition statistics.

        Returns
        -------
        tuple[dict, dict, dict, list[dict]]
            (dfg, start_activities, end_activities, transition_stats)

        Notes
        -----
        - transition_count for a DFG edge (A, B) is the number of times
          activity B directly followed activity A within the same case.
        - Total DFG transitions = Total events − Total cases (each case of
          N events contributes N-1 transitions).
        - Self-loops (A -> A) indicate multiple adjacent instances of the
          same activity within a case; this is genuine for multi-item lab
          orders, not a modeling artifact.
        - Mean/median transition duration measures the time between the
          ordering timestamps of consecutive events within the same case.
          Identical timestamps (median=0 for lab self-loops) are due to
          multiple lab orders sharing the appointment timestamp — not proof
          of instant clinical processing.
        """
        if self.df is None:
            self.load_event_log()

        print("Discovering Directly-Follows Graph (DFG)...")
        dfg, sa, ea = pm4py.discover_dfg(self.df)
        self.dfg = dfg
        self.start_activities = sa
        self.end_activities = ea

        total_transitions = sum(dfg.values())
        print(
            f"Discovered DFG with {len(dfg)} distinct edges "
            f"and {total_transitions:,} total transitions."
        )

        # Compute per-transition timing statistics using vectorised pandas ops.
        sorted_df = (
            self.df
            .sort_values(by=["case_id", "time:timestamp", "event_index"])
            .copy()
        )
        sorted_df["_next_case"] = sorted_df["case_id"].shift(-1)
        sorted_df["_next_act"] = sorted_df["activity"].shift(-1)
        sorted_df["_next_ts"] = sorted_df["time:timestamp"].shift(-1)

        same_case_mask = sorted_df["case_id"] == sorted_df["_next_case"]
        trans_df = sorted_df[same_case_mask].copy()
        trans_df["dur_min"] = (
            (trans_df["_next_ts"] - trans_df["time:timestamp"])
            .dt.total_seconds() / 60.0
        )

        dur_grp = trans_df.groupby(["activity", "_next_act"])["dur_min"]
        mean_durs = dur_grp.mean().to_dict()
        median_durs = dur_grp.median().to_dict()

        stats = []
        for (src, tgt), count in sorted(dfg.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / total_transitions) * 100, 2)
            m_dur = round(float(mean_durs.get((src, tgt), 0.0)), 2)
            med_dur = round(float(median_durs.get((src, tgt), 0.0)), 2)
            stats.append({
                "source_activity": src,
                "target_activity": tgt,
                "transition_count": count,
                "transition_percentage": f"{pct}%",
                "mean_transition_minutes": m_dur,
                "median_transition_minutes": med_dur,
            })

        self.transition_stats = stats
        return dfg, sa, ea, stats

    # ------------------------------------------------------------------
    # Step 3: Variants
    # ------------------------------------------------------------------

    def discover_variants(self) -> list:
        """Discover process variants (unique activity sequences) and their
        case coverage.

        Returns
        -------
        list[dict]
            Sorted list of variant dicts with keys:
            variant_id, activity_sequence, case_count, case_percentage,
            cumulative_percentage, activities_length.

        Notes
        -----
        - Each unique ordered sequence of activities across a case is one
          variant.
        - 287 distinct variants are expected for the full CareFlow OPD log.
        - VAR_001 (Appointment Registration -> Doctor Consultation &
          Prescription) accounts for ~78.5% of all cases — the dominant
          OPD pathway.
        - Variants with repeated activities (e.g., Lab -> Lab -> Lab) reflect
          multiple laboratory tests ordered in one encounter.
        """
        if self.df is None:
            self.load_event_log()

        print("Discovering process variants...")
        raw_variants = pm4py.get_variants_as_tuples(self.df)
        total_cases = self.df["case_id"].nunique()

        variant_list = []
        cum_cases = 0
        for idx, (var_tuple, count) in enumerate(
            sorted(raw_variants.items(), key=lambda x: x[1], reverse=True),
            start=1,
        ):
            cum_cases += count
            case_pct = round((count / total_cases) * 100, 2)
            cum_pct = round((cum_cases / total_cases) * 100, 2)
            variant_list.append({
                "variant_id": f"VAR_{idx:03d}",
                "activity_sequence": " -> ".join(var_tuple),
                "case_count": count,
                "case_percentage": f"{case_pct}%",
                "cumulative_percentage": f"{cum_pct}%",
                "activities_length": len(var_tuple),
            })

        self.variants = variant_list
        print(
            f"Discovered {len(variant_list)} distinct process variants "
            f"across {total_cases:,} cases."
        )
        return variant_list

    # ------------------------------------------------------------------
    # Step 4: Activity frequency statistics
    # ------------------------------------------------------------------

    def calculate_activity_stats(self) -> list:
        """Calculate per-activity event counts, case coverage, and duration
        statistics from the loaded event log.

        Returns
        -------
        list[dict]
            One row per activity with keys:
            activity, event_count, unique_cases, case_coverage_percent,
            event_share_percent, bounded_durations_count,
            mean_duration_minutes, median_duration_minutes.
        """
        if self.df is None:
            self.load_event_log()

        total_events = len(self.df)
        total_cases = self.df["case_id"].nunique()

        rows = []
        for act in self.df["activity"].unique():
            act_df = self.df[self.df["activity"] == act]
            n_events = len(act_df)
            n_cases = act_df["case_id"].nunique()

            # Duration statistics from source column (may contain NaN/blanks)
            if "duration_minutes" in self.df.columns:
                dur_series = pd.to_numeric(
                    act_df["duration_minutes"], errors="coerce"
                ).dropna()
                bounded = len(dur_series)
                mean_dur = round(float(dur_series.mean()), 2) if bounded > 0 else 0.0
                median_dur = round(float(dur_series.median()), 2) if bounded > 0 else 0.0
            else:
                bounded, mean_dur, median_dur = 0, 0.0, 0.0

            rows.append({
                "activity": act,
                "event_count": n_events,
                "unique_cases": n_cases,
                "case_coverage_percent": f"{round((n_cases / total_cases) * 100, 2)}%",
                "event_share_percent": f"{round((n_events / total_events) * 100, 2)}%",
                "bounded_durations_count": bounded,
                "mean_duration_minutes": mean_dur,
                "median_duration_minutes": median_dur,
            })

        rows.sort(key=lambda r: r["event_count"], reverse=True)
        self.activity_stats = rows
        return rows

    # ------------------------------------------------------------------
    # Step 5: Inductive Miner Petri Net
    # ------------------------------------------------------------------

    def discover_petri_net(self):
        """Discover Petri net using the PM4Py Inductive Miner algorithm.

        Returns
        -------
        tuple[PetriNet, Marking, Marking]
            (net, initial_marking, final_marking)

        Notes
        -----
        - The Inductive Miner guarantees a sound (deadlock-free) workflow net.
        - Silent (tau) transitions represent control-flow routing (choice /
          loop constructs) with no clinical activity label.
        - The resulting net for this OPD log has 17 places, 21 transitions
          (5 visible, 16 silent), and 48 arcs.
        - Fitness/precision conformance checking is intentionally not run here
          because PNML export and inspection cover the structural output;
          conformance analysis is a separate module concern.
        """
        if self.df is None:
            self.load_event_log()

        print("Discovering Petri Net using Inductive Miner...")
        net, im, fm = pm4py.discover_petri_net_inductive(self.df)
        self.petri_net = net
        self.initial_marking = im
        self.final_marking = fm

        print("Inductive Miner successfully built Petri net:")
        print(f"  Places:      {len(net.places)}")
        print(f"  Transitions: {len(net.transitions)}")
        print(f"  Arcs:        {len(net.arcs)}")
        return net, im, fm

    # ------------------------------------------------------------------
    # Step 6: Export aggregate CSVs
    # ------------------------------------------------------------------

    def export_csvs(self, output_dir: str = "outputs") -> dict:
        """Export all aggregate tabular outputs to CSV files.

        Parameters
        ----------
        output_dir : str
            Directory to write CSV files (created if absent).

        Returns
        -------
        dict
            Mapping of {label: file_path} for all exported files.

        Notes
        -----
        - Exports contain only aggregate statistics, never patient-level
          identifiers. The source event log CSV/XES files must remain in
          outputs/ and are excluded from Git by .gitignore.
        """
        os.makedirs(output_dir, exist_ok=True)
        exported = {}

        # 1. Transition frequencies
        trans_path = os.path.join(output_dir, "transition_frequencies.csv")
        _write_csv(trans_path, self.transition_stats, fieldnames=[
            "source_activity", "target_activity", "transition_count",
            "transition_percentage", "mean_transition_minutes",
            "median_transition_minutes",
        ])
        print(f"Exported transition frequencies: {trans_path}")
        exported["transition_frequencies"] = trans_path

        # 2. Process variants
        var_path = os.path.join(output_dir, "process_variants.csv")
        _write_csv(var_path, self.variants, fieldnames=[
            "variant_id", "activity_sequence", "case_count",
            "case_percentage", "cumulative_percentage", "activities_length",
        ])
        print(f"Exported process variants: {var_path}")
        exported["process_variants"] = var_path

        # 3. Start / end activity summary
        se_path = os.path.join(output_dir, "start_end_activities.csv")
        total_cases = self.df["case_id"].nunique()
        all_acts = sorted(
            set(list(self.start_activities.keys()) + list(self.end_activities.keys()))
        )
        se_rows = []
        for act in all_acts:
            s_cnt = self.start_activities.get(act, 0)
            e_cnt = self.end_activities.get(act, 0)
            se_rows.append({
                "activity": act,
                "start_count": s_cnt,
                "start_percentage": f"{round((s_cnt / total_cases) * 100, 2)}%",
                "end_count": e_cnt,
                "end_percentage": f"{round((e_cnt / total_cases) * 100, 2)}%",
            })
        _write_csv(se_path, se_rows, fieldnames=[
            "activity", "start_count", "start_percentage",
            "end_count", "end_percentage",
        ])
        print(f"Exported start/end activities: {se_path}")
        exported["start_end_activities"] = se_path

        # 4. Activity frequency statistics
        if self.activity_stats:
            af_path = os.path.join(output_dir, "activity_frequency.csv")
            _write_csv(af_path, self.activity_stats, fieldnames=[
                "activity", "event_count", "unique_cases",
                "case_coverage_percent", "event_share_percent",
                "bounded_durations_count", "mean_duration_minutes",
                "median_duration_minutes",
            ])
            print(f"Exported activity frequency: {af_path}")
            exported["activity_frequency"] = af_path

        # 5. Petri net PNML
        if self.petri_net is not None:
            pnml_path = os.path.join(output_dir, "careflow_petri_net.pnml")
            pm4py.write_pnml(
                self.petri_net, self.initial_marking,
                self.final_marking, pnml_path,
            )
            print(f"Exported Petri net PNML: {pnml_path}")
            exported["petri_net_pnml"] = pnml_path

        return exported

    # ------------------------------------------------------------------
    # Step 7: Process map rendering
    # ------------------------------------------------------------------

    def render_dfg_map(self, output_dir: str = "outputs") -> dict:
        """Render a hand-laid-out Directly-Follows Graph as PNG and SVG.

        Layout is fixed to match the clinical flow order:
        START -> Appointment Registration -> Doctor Consultation &
        Prescription -> (Lab / Imaging) -> Pharmacy Dispensing -> END.
        Self-loops and backward edges are drawn with curvature.

        Returns
        -------
        dict
            {"png": path, "svg": path}
        """
        os.makedirs(output_dir, exist_ok=True)
        if self.dfg is None:
            self.discover_dfg()
        print("Rendering Directly-Follows Graph (DFG) process maps...")

        node_positions = {
            "START":                              (0.0,  0.0),
            "Appointment Registration":           (2.2,  0.0),
            "Doctor Consultation & Prescription": (5.2,  0.0),
            "Laboratory Examination":             (8.2,  1.4),
            "Imaging Procedure":                  (8.2, -1.4),
            "Pharmacy Dispensing":               (11.0,  0.0),
            "END":                               (13.2,  0.0),
        }
        node_colors = {
            "START":                              "#2ecc71",
            "Appointment Registration":           "#3498db",
            "Doctor Consultation & Prescription": "#2980b9",
            "Laboratory Examination":             "#9b59b6",
            "Imaging Procedure":                  "#e67e22",
            "Pharmacy Dispensing":                "#1abc9c",
            "END":                                "#e74c3c",
        }

        fig, ax = plt.subplots(figsize=(16, 8), dpi=300)
        ax.set_facecolor("#fdfefe")

        total_trans = sum(self.dfg.values())
        max_trans = max(self.dfg.values())
        total_cases = self.df["case_id"].nunique()

        # Start-activity edges (from virtual START node)
        for act, cnt in self.start_activities.items():
            if act in node_positions:
                _draw_arrow(
                    ax, node_positions["START"], node_positions[act],
                    color="#27ae60",
                    lw=max(1.0, (cnt / total_cases) * 4.0),
                    rad=0.0,
                )

        # DFG edges
        for (src, tgt), cnt in self.dfg.items():
            if src not in node_positions or tgt not in node_positions:
                continue
            p1, p2 = node_positions[src], node_positions[tgt]

            # Self-loops
            if src == tgt:
                loop = patches.Arc(
                    (p1[0], p1[1] + 0.35), 0.5, 0.5,
                    angle=0, theta1=0, theta2=270,
                    color="#7f8c8d", lw=2,
                )
                ax.add_patch(loop)
                ax.text(
                    p1[0], p1[1] + 0.65, f"{cnt:,}",
                    ha="center", va="center", fontsize=8,
                    color="#2c3e50", weight="bold",
                )
                continue

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            rad = 0.15 if dx > 0 else -0.25
            if abs(dy) > 1.0 and abs(dx) < 1.0:
                rad = 0.1

            lw = max(1.0, (cnt / max_trans) * 6.0)
            color = "#34495e" if cnt > 1000 else "#95a5a6"
            _draw_arrow(ax, p1, p2, color=color, lw=lw, rad=rad, alpha=0.85)

            if cnt >= 50:
                pct = (cnt / total_trans) * 100
                mid_x = (p1[0] + p2[0]) / 2.0
                mid_y = (p1[1] + p2[1]) / 2.0 + (0.15 if rad >= 0 else -0.15)
                ax.text(
                    mid_x, mid_y, f"{cnt:,}\n({pct:.1f}%)",
                    ha="center", va="center", fontsize=7.5,
                    bbox=dict(
                        boxstyle="round,pad=0.2", fc="white",
                        ec="#bdc3c7", lw=0.5, alpha=0.9,
                    ),
                )

        # End-activity edges (to virtual END node)
        for act, cnt in self.end_activities.items():
            if act in node_positions:
                _draw_arrow(
                    ax, node_positions[act], node_positions["END"],
                    color="#c0392b",
                    lw=max(1.0, (cnt / total_cases) * 4.0),
                    rad=0.0, linestyle="--",
                )

        # Node boxes
        act_counts = self.df["activity"].value_counts().to_dict()
        for name, pos in node_positions.items():
            col = node_colors.get(name, "#34495e")
            if name in ("START", "END"):
                circle = patches.Circle(
                    pos, 0.4, facecolor=col,
                    edgecolor="#2c3e50", lw=2, zorder=5,
                )
                ax.add_patch(circle)
                ax.text(
                    pos[0], pos[1], name,
                    ha="center", va="center",
                    color="white", weight="bold", fontsize=10, zorder=6,
                )
            else:
                box = patches.FancyBboxPatch(
                    (pos[0] - 0.95, pos[1] - 0.4), 1.9, 0.8,
                    boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor=col, edgecolor="#1a252f",
                    lw=1.5, zorder=5, alpha=0.95,
                )
                ax.add_patch(box)
                wrapped = name.replace(" & ", "\n& ").replace(" ", "\n", 1)
                ax.text(
                    pos[0], pos[1] + 0.08, wrapped,
                    ha="center", va="center",
                    color="white", weight="bold", fontsize=8.5, zorder=6,
                )
                ev_total = act_counts.get(name, 0)
                ax.text(
                    pos[0], pos[1] - 0.25, f"{ev_total:,} events",
                    ha="center", va="center",
                    color="#ecf0f1", fontsize=7, zorder=6,
                )

        ax.set_xlim(-1.0, 14.2)
        ax.set_ylim(-2.5, 2.5)
        ax.axis("off")
        plt.title(
            f"CareFlow: Directly-Follows Graph (DFG) of Clinical Outpatient Pathways\n"
            f"({total_cases:,} Encounters, {len(self.df):,} Events, "
            f"{len(self.dfg)} DFG Edges)",
            fontsize=14, weight="bold", pad=20,
        )
        plt.tight_layout()

        png_path = os.path.join(output_dir, "careflow_dfg.png")
        svg_path = os.path.join(output_dir, "careflow_dfg.svg")
        plt.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.savefig(svg_path, format="svg", bbox_inches="tight")
        plt.close()
        print(f"Exported DFG process maps: {png_path} and {svg_path}")
        return {"png": png_path, "svg": svg_path}

    def render_petri_net_map(self, output_dir: str = "outputs") -> dict:
        """Render the Inductive Miner Petri net as PNG and SVG using networkx
        spring layout.

        Returns
        -------
        dict
            {"png": path, "svg": path}
        """
        os.makedirs(output_dir, exist_ok=True)
        if self.petri_net is None:
            self.discover_petri_net()
        print("Rendering Petri Net process map...")

        net = self.petri_net
        G = nx.DiGraph()

        for p in net.places:
            G.add_node(p.name, node_type="place", label="")
        for t in net.transitions:
            label = t.label if t.label else "τ (silent)"
            G.add_node(t.name, node_type="transition", label=label)
        for arc in net.arcs:
            G.add_edge(arc.source.name, arc.target.name)

        place_nodes = [p.name for p in net.places]
        visible_trans = [t.name for t in net.transitions if t.label]
        silent_trans = [t.name for t in net.transitions if not t.label]

        fig, ax = plt.subplots(figsize=(18, 9), dpi=300)
        ax.set_facecolor("#fafbfc")

        pos = nx.spring_layout(G, k=1.8, iterations=100, seed=42)

        nx.draw_networkx_nodes(
            G, pos, nodelist=place_nodes,
            node_color="#ecf0f1", node_size=600,
            edgecolors="#2c3e50", linewidths=2.0, ax=ax,
        )
        nx.draw_networkx_nodes(
            G, pos, nodelist=visible_trans,
            node_color="#3498db", node_shape="s", node_size=1200,
            edgecolors="#1b4f72", linewidths=2.0, ax=ax,
        )
        if silent_trans:
            nx.draw_networkx_nodes(
                G, pos, nodelist=silent_trans,
                node_color="#bdc3c7", node_shape="s", node_size=400,
                edgecolors="#7f8c8d", linewidths=1.5, ax=ax,
            )

        nx.draw_networkx_edges(
            G, pos, arrowstyle="-|>", arrowsize=15,
            edge_color="#34495e", width=1.5,
            connectionstyle="arc3,rad=0.08", ax=ax,
        )

        labels = {}
        for n, data in G.nodes(data=True):
            if data["node_type"] == "transition":
                lbl = data["label"]
                labels[n] = "τ" if lbl == "τ (silent)" else lbl.replace(" & ", "\n& ").replace(" ", "\n", 1)
            else:
                labels[n] = ""

        nx.draw_networkx_labels(
            G, pos, labels=labels,
            font_size=7.5, font_weight="bold", font_color="white", ax=ax,
        )

        ax.axis("off")
        plt.title(
            f"CareFlow: Petri Net Model Discovered via Inductive Miner\n"
            f"({len(net.places)} Places, {len(net.transitions)} Transitions, "
            f"{len(net.arcs)} Arcs | Blue squares = visible activities, "
            f"Grey squares = silent τ transitions, Circles = places)",
            fontsize=13, weight="bold", pad=20,
        )
        plt.tight_layout()

        png_path = os.path.join(output_dir, "careflow_petri_net.png")
        svg_path = os.path.join(output_dir, "careflow_petri_net.svg")
        plt.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.savefig(svg_path, format="svg", bbox_inches="tight")
        plt.close()
        print(f"Exported Petri net maps: {png_path} and {svg_path}")
        return {"png": png_path, "svg": svg_path}

    def render_variants_chart(self, output_dir: str = "outputs", top_n: int = 10) -> dict:
        """Render a horizontal bar chart of the top-N process variants.

        Parameters
        ----------
        top_n : int
            Number of top variants to display (default 10).

        Returns
        -------
        dict
            {"png": path, "svg": path}
        """
        os.makedirs(output_dir, exist_ok=True)
        if self.variants is None:
            self.discover_variants()
        print("Rendering Process Variants chart...")

        top_vars = self.variants[:top_n]
        cum_pct = top_vars[-1]["cumulative_percentage"]   # e.g. "94.91%"

        # Reverse for bottom-to-top bar ordering
        labels = [
            f"{v['variant_id']}: {v['activity_sequence']}"
            for v in top_vars
        ][::-1]
        counts = [v["case_count"] for v in top_vars][::-1]
        pcts = [v["case_percentage"] for v in top_vars][::-1]

        fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
        bars = ax.barh(range(len(top_vars)), counts, color="#3498db",
                       edgecolor="#2980b9", height=0.65)

        for bar, count, pct in zip(bars, counts, pcts):
            ax.text(
                bar.get_width() + 400,
                bar.get_y() + bar.get_height() / 2,
                f"{count:,} cases ({pct})",
                va="center", ha="left", fontsize=9,
                weight="bold", color="#2c3e50",
            )

        ax.set_yticks(range(len(top_vars)))
        ax.set_yticklabels(labels, fontsize=8.5)
        ax.set_xlabel("Number of Encounters (Cases)", fontsize=11, weight="bold")
        ax.set_title(
            f"CareFlow: Top {top_n} Clinical Pathway Process Variants\n"
            f"(Accounting for {cum_pct} of all Outpatient Encounters)",
            fontsize=13, weight="bold", pad=15,
        )
        ax.set_xlim(0, max(counts) * 1.25)
        ax.grid(axis="x", linestyle="--", alpha=0.5)
        plt.tight_layout()

        png_path = os.path.join(output_dir, "careflow_variants.png")
        svg_path = os.path.join(output_dir, "careflow_variants.svg")
        plt.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.savefig(svg_path, format="svg", bbox_inches="tight")
        plt.close()
        print(f"Exported process variants charts: {png_path} and {svg_path}")
        return {"png": png_path, "svg": svg_path}

    # ------------------------------------------------------------------
    # Pipeline orchestrator
    # ------------------------------------------------------------------

    def run_full_discovery_pipeline(self, output_dir: str = "outputs") -> dict:
        """Run the complete process discovery pipeline and export all
        deliverables.

        Steps
        -----
        1. Load and validate event log.
        2. Discover DFG with transition statistics.
        3. Discover process variants.
        4. Calculate activity frequency statistics.
        5. Discover Inductive Miner Petri net.
        6. Export aggregate CSVs.
        7. Render DFG process map (PNG + SVG).
        8. Render Petri net map (PNG + SVG).
        9. Render top-10 variants bar chart (PNG + SVG).

        Returns
        -------
        dict
            Summary of discovered metrics and exported file paths.
        """
        self.load_event_log()
        self.discover_dfg()
        self.discover_variants()
        self.calculate_activity_stats()
        self.discover_petri_net()
        exported = self.export_csvs(output_dir=output_dir)
        dfg_paths = self.render_dfg_map(output_dir=output_dir)
        pn_paths = self.render_petri_net_map(output_dir=output_dir)
        var_paths = self.render_variants_chart(output_dir=output_dir)

        summary = {
            "total_events": len(self.df),
            "total_cases": self.df["case_id"].nunique(),
            "dfg_edges": len(self.dfg),
            "dfg_total_transitions": sum(self.dfg.values()),
            "total_variants": len(self.variants),
            "top_variant_case_count": self.variants[0]["case_count"],
            "petri_net_places": len(self.petri_net.places),
            "petri_net_transitions": len(self.petri_net.transitions),
            "petri_net_arcs": len(self.petri_net.arcs),
            "exported_files": {**exported, **dfg_paths, **pn_paths, **var_paths},
        }
        print("\n=== Process Discovery Pipeline Successfully Finished ===")
        print(f"  Events:            {summary['total_events']:,}")
        print(f"  Cases:             {summary['total_cases']:,}")
        print(f"  DFG Edges:         {summary['dfg_edges']}")
        print(f"  DFG Transitions:   {summary['dfg_total_transitions']:,}")
        print(f"  Variants:          {summary['total_variants']}")
        print(f"  Petri Net (P/T/A): {summary['petri_net_places']}/"
              f"{summary['petri_net_transitions']}/{summary['petri_net_arcs']}")
        return summary


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _write_csv(path: str, rows: list, fieldnames: list) -> None:
    """Write a list-of-dict to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _draw_arrow(ax, p1, p2, color, lw, rad=0.0, alpha=1.0, linestyle="solid"):
    """Draw an annotated arrow between two (x,y) positions."""
    ax.annotate(
        "", xy=p2, xytext=p1,
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw,
            connectionstyle=f"arc3,rad={rad}",
            mutation_scale=14, alpha=alpha,
            linestyle=linestyle,
        ),
    )


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    """CLI entrypoint: python -m process_mining.process_discovery [log_path] [output_dir]"""
    event_log_path = sys.argv[1] if len(sys.argv) > 1 else None
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"

    discovery = CareFlowProcessDiscovery(event_log_path=event_log_path)
    discovery.run_full_discovery_pipeline(output_dir=output_dir)


if __name__ == "__main__":
    main()
