//! Action EV and node EV extraction for solved games.
//!
//! Provides mathematically exact reach propagation and conditional action EV calculation.
//! For a decision node `u` with acting player `p`, given opponent reach `pi_{-p}`:
//!
//! - The opponent compatible mass for hero combo `i` is:
//!   `M(i) = sum_{j compatible with i} pi_{-p}(j)`
//! - The conditional expected value of taking action `a` leading to child `v_a` is:
//!   `EV(i, a) = CFV_p(v_a, i) / M(i)`
//! - The node strategy EV is:
//!   `EV(i) = sum_a sigma_p(u, a, i) * EV(i, a)`
//!
//! Identity: `sum_a sigma_p(u, a, i) * EV(i, a) == EV(i)` holds to machine precision.

use crate::br::{self, StrategyProfile};
use crate::game::{Game, NodeInfo};
use crate::nlhe::NlheGame;
use crate::solution::Solution;

impl StrategyProfile for Solution {
    fn strategy_into(&self, node: u32, out: &mut [f32]) {
        if let Some(ns) = self.nodes.iter().find(|n| n.node == node) {
            out.copy_from_slice(&ns.strategy);
        } else {
            panic!("node {node} not found in solution");
        }
    }
}

/// Propagates both players' reach vectors down the entire game tree.
/// Returns `[reach_0, reach_1]` where each is a `Vec<Vec<f32>>` of length `game.num_nodes()`.
/// Opponent reach carries chance edge weights.
pub fn compute_tree_reaches<P: StrategyProfile>(
    game: &NlheGame,
    profile: &P,
) -> [Vec<Vec<f32>>; 2] {
    let n = game.num_nodes();
    let mut r0: Vec<Vec<f32>> = vec![Vec::new(); n];
    let mut r1: Vec<Vec<f32>> = vec![Vec::new(); n];
    let root = game.root() as usize;
    r0[root] = game.root_weights(0).to_vec();
    r1[root] = game.root_weights(1).to_vec();

    for idx in 0..n {
        let node = idx as u32;
        match game.node(node) {
            NodeInfo::Decision { player, num_actions } => {
                let p = player as usize;
                let o = 1 - p;
                let combo_count = game.combo_count(node, player);
                let mut strat = vec![0.0f32; num_actions * combo_count];
                profile.strategy_into(node, &mut strat);

                for a in 0..num_actions {
                    let child = game.child(node, a) as usize;
                    // Opponent reach passes through unmodified
                    if o == 0 {
                        r0[child] = r0[idx].clone();
                    } else {
                        r1[child] = r1[idx].clone();
                    }

                    // Hero reach is multiplied by action probability
                    let p_parent = if p == 0 { &r0[idx] } else { &r1[idx] };
                    let mut p_child = vec![0.0f32; combo_count];
                    if !p_parent.is_empty() {
                        for i in 0..combo_count {
                            p_child[i] = p_parent[i] * strat[a * combo_count + i];
                        }
                    }
                    if p == 0 {
                        r0[child] = p_child;
                    } else {
                        r1[child] = p_child;
                    }
                }
            }
            NodeInfo::Chance { num_outcomes } => {
                for k in 0..num_outcomes {
                    let edge = game.chance_outcome(node, k);
                    let child = edge.child as usize;
                    for pl in 0..2u8 {
                        let map = edge.parent_of_child[pl as usize];
                        let p_reach = if pl == 0 { &r0[idx] } else { &r1[idx] };
                        let mut c_reach = vec![0.0f32; map.len()];
                        if !p_reach.is_empty() {
                            for (t, &parent_idx) in map.iter().enumerate() {
                                // Scale opponent reach by edge weight
                                c_reach[t] = p_reach[parent_idx as usize] * edge.weight;
                            }
                        }
                        if pl == 0 {
                            r0[child] = c_reach;
                        } else {
                            r1[child] = c_reach;
                        }
                    }
                }
            }
            NodeInfo::Terminal => {}
        }
    }

    [r0, r1]
}

/// Computes per-combo action EVs and node strategy EV for a decision node.
///
/// Returns `(action_evs, node_evs)`:
/// - `action_evs`: action-major `[a * combo_count + i]` in chips
/// - `node_evs`: per-combo `[i]` in chips
pub fn compute_decision_node_evs<P: StrategyProfile>(
    game: &NlheGame,
    profile: &P,
    node: u32,
    opp_reach: &[f32],
) -> (Vec<f32>, Vec<f32>) {
    let NodeInfo::Decision { player, num_actions } = game.node(node) else {
        panic!("node {node} is not a decision node");
    };
    let combo_count = game.combo_count(node, player);
    let mut strat = vec![0.0f32; num_actions * combo_count];
    profile.strategy_into(node, &mut strat);

    let mass = game.compatible_mass(node, player, opp_reach);
    let mut action_evs = vec![0.0f32; num_actions * combo_count];
    let mut node_evs = vec![0.0f32; combo_count];

    for a in 0..num_actions {
        let child = game.child(node, a);
        let mut cfv = vec![0.0f32; combo_count];
        br::subtree_values(game, child, player, profile, opp_reach, false, &mut cfv);
        for i in 0..combo_count {
            let ev = if mass[i] > 1e-9 { cfv[i] / mass[i] } else { 0.0 };
            action_evs[a * combo_count + i] = ev;
        }
    }

    for i in 0..combo_count {
        let mut sum = 0.0f32;
        for a in 0..num_actions {
            sum += strat[a * combo_count + i] * action_evs[a * combo_count + i];
        }
        node_evs[i] = sum;
    }

    (action_evs, node_evs)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cfr::{DcfrParams, Solver};
    use crate::config::SolveConfig;

    fn river_spot_cfg() -> SolveConfig {
        SolveConfig {
            board: "Qh 9s 4d Jc 2h".to_string(),
            oop_range: "AhKh,AhQh,9h9c".to_string(),
            ip_range: "KhQc,JhJd,4c4s".to_string(),
            effective_stack: 100.0,
            starting_pot: 20.0,
            raise_cap: 1,
            ..SolveConfig::default()
        }
    }

    #[test]
    fn test_action_ev_identity_and_consistency() {
        let cfg = river_spot_cfg();
        let g = NlheGame::new(&cfg).expect("builds");
        let mut s = Solver::new(g);
        s.run(200, &DcfrParams::default(), 0, |_, _, _| {});

        let reaches = compute_tree_reaches(s.game(), &s.average());

        for idx in 0..s.game().num_nodes() as u32 {
            if let NodeInfo::Decision { player, num_actions } = s.game().node(idx) {
                let opp = 1 - player;
                let opp_reach = &reaches[opp as usize][idx as usize];
                let combo_count = s.game().combo_count(idx, player);

                let (action_evs, node_evs) =
                    compute_decision_node_evs(s.game(), &s.average(), idx, opp_reach);

                let mut strat = vec![0.0f32; num_actions * combo_count];
                s.average().strategy_into(idx, &mut strat);

                // Verify identity: node_evs[i] == sum_a strat[a, i] * action_evs[a, i]
                for i in 0..combo_count {
                    let mut expected_node_ev = 0.0f32;
                    for a in 0..num_actions {
                        expected_node_ev += strat[a * combo_count + i] * action_evs[a * combo_count + i];
                    }
                    assert!(
                        (node_evs[i] - expected_node_ev).abs() < 1e-4,
                        "node {idx} combo {i}: node_ev {} != sum(f * ev) {}",
                        node_evs[i],
                        expected_node_ev
                    );
                }
            }
        }
    }
}
