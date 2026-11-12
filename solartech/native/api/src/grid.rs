//! The energy grid: how energy moves between SolarTech's blocks.
//!
//! A block's tick is only handed its own block entity, so blocks can't write into each
//! other. Instead every block keeps a `Node` here: what it holds, and an inbox its
//! neighbours pay into. A block's tick first collects its inbox, does its own work, then
//! pays into the inboxes around it and publishes what it has left. Energy handed over this
//! way arrives one tick later.
//!
//! The grid is never saved. What a block holds is in its own NBT; the grid fills up again
//! as blocks tick after a load.
use std::collections::HashMap;
use std::time::{Duration, Instant};

/// A block's place: its dimension and position.
pub type Place = (&'static str, [i32; 3]);

/// What a block does with energy.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    /// Makes energy and gives it away (the solar panel). Takes none.
    Source,
    /// Passes energy on, levelling with the cables beside it.
    Cable,
    /// Uses energy (the electric furnace). Gives none.
    Sink,
}

/// The most one block pays into one neighbour in a tick.
pub const TRANSFER: i32 = 400;

/// A node that hasn't ticked for this long is gone (broken, or its chunk unloaded).
const STALE: Duration = Duration::from_secs(2);

#[derive(Clone, Copy, Debug)]
struct Node {
    kind: Kind,
    /// What it held at the end of its last tick.
    stored: i32,
    capacity: i32,
    /// Paid in by its neighbours since then.
    inbox: i32,
    seen: Instant,
}

impl Node {
    fn fresh(&self, now: Instant) -> bool {
        now.saturating_duration_since(self.seen) < STALE
    }
}

#[derive(Default)]
pub struct Grid {
    nodes: HashMap<Place, Node>,
    ticks: u64,
}

impl Grid {
    /// The start of a block's tick: what it holds once its inbox is collected. What
    /// doesn't fit stays in the inbox for a later tick.
    pub fn collect(&mut self, place: Place, stored: i32, capacity: i32) -> i32 {
        let Some(node) = self.nodes.get_mut(&place) else {
            return stored;
        };
        let taken = node.inbox.min(capacity - stored).max(0);
        node.inbox -= taken;
        stored + taken
    }

    /// The end of a block's tick: pays into the neighbours that take energy, then
    /// publishes what is left. Returns what is left.
    pub fn settle(
        &mut self,
        place: Place,
        kind: Kind,
        mut stored: i32,
        capacity: i32,
        now: Instant,
    ) -> i32 {
        if kind != Kind::Sink {
            // Machines first, so a cable feeds what it is plugged into before it
            // levels with the next cable.
            for to in [Kind::Sink, Kind::Cable] {
                for neighbour in neighbours(place.1) {
                    let target = self.nodes.get_mut(&(place.0, neighbour));
                    let Some(target) = target.filter(|t| t.kind == to && t.fresh(now)) else {
                        continue;
                    };
                    let held = target.stored + target.inbox;
                    let room = target.capacity - held;
                    let wanted = match (kind, to) {
                        // Cables level out: half the difference, so two never swap
                        // the same energy back and forth.
                        (Kind::Cable, Kind::Cable) => (stored - held) / 2,
                        _ => room,
                    };
                    let amount = wanted.min(room).min(TRANSFER).min(stored).max(0);
                    target.inbox += amount;
                    stored -= amount;
                }
            }
        }
        let inbox = self.nodes.get(&place).map_or(0, |n| n.inbox);
        self.nodes.insert(
            place,
            Node {
                kind,
                stored,
                capacity,
                inbox,
                seen: now,
            },
        );
        self.ticks += 1;
        if self.ticks % 4096 == 0 {
            self.nodes.retain(|_, n| n.fresh(now));
        }
        stored
    }
}

fn neighbours([x, y, z]: [i32; 3]) -> [[i32; 3]; 6] {
    [
        [x, y - 1, z],
        [x, y + 1, z],
        [x, y, z - 1],
        [x, y, z + 1],
        [x - 1, y, z],
        [x + 1, y, z],
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    const DIM: &str = "minecraft:overworld";

    /// One tick of a block that does no work of its own.
    fn tick(grid: &mut Grid, x: i32, kind: Kind, stored: i32, capacity: i32, now: Instant) -> i32 {
        let place = (DIM, [x, 0, 0]);
        let stored = grid.collect(place, stored, capacity);
        grid.settle(place, kind, stored, capacity, now)
    }

    #[test]
    fn a_panel_feeds_a_furnace_beside_it() {
        let (mut grid, now) = (Grid::default(), Instant::now());
        let mut furnace = tick(&mut grid, 1, Kind::Sink, 0, 1_000, now);
        let panel = tick(&mut grid, 0, Kind::Source, 100, 10_000, now);
        assert_eq!(panel, 0);
        furnace = tick(&mut grid, 1, Kind::Sink, furnace, 1_000, now);
        assert_eq!(furnace, 100);
    }

    #[test]
    fn energy_crosses_a_line_of_cables_and_none_is_lost() {
        let (mut grid, now) = (Grid::default(), Instant::now());
        // panel(0) - cable(1) - cable(2) - cable(3) - furnace(4)
        let mut held = [5_000, 0, 0, 0, 0];
        let kinds = [Kind::Source, Kind::Cable, Kind::Cable, Kind::Cable, Kind::Sink];
        let caps = [10_000, 2_000, 2_000, 2_000, 20_000];
        for _ in 0..200 {
            for i in 0..5 {
                held[i] = tick(&mut grid, i as i32, kinds[i], held[i], caps[i], now);
            }
        }
        // One more round of collecting, so nothing is left in an inbox.
        for i in 0..5 {
            held[i] = grid.collect((DIM, [i as i32, 0, 0]), held[i], caps[i]);
        }
        assert_eq!(held.iter().sum::<i32>(), 5_000, "{held:?}");
        assert_eq!(held[0], 0, "{held:?}");
        assert!(held[4] > 4_900, "{held:?}");
    }

    #[test]
    fn nothing_flows_into_a_panel_or_out_of_a_furnace() {
        let (mut grid, now) = (Grid::default(), Instant::now());
        // panel(0) - cable(1) - furnace(2)
        let furnace = tick(&mut grid, 2, Kind::Sink, 0, 20_000, now);
        let panel = tick(&mut grid, 0, Kind::Source, 0, 10_000, now);
        let cable = tick(&mut grid, 1, Kind::Cable, 500, 2_000, now);
        // The cable paid the furnace, not the panel.
        assert_eq!(cable, 100);
        assert_eq!(tick(&mut grid, 0, Kind::Source, panel, 10_000, now), 0);
        let furnace = tick(&mut grid, 2, Kind::Sink, furnace, 20_000, now);
        assert_eq!(furnace, 400);
        // A furnace keeps what it has: an empty cable beside it stays empty.
        assert_eq!(tick(&mut grid, 1, Kind::Cable, 0, 2_000, now), 0);
        assert_eq!(tick(&mut grid, 1, Kind::Cable, 0, 2_000, now), 0);
        assert_eq!(tick(&mut grid, 2, Kind::Sink, furnace, 20_000, now), 400);
    }

    #[test]
    fn a_full_block_takes_no_more() {
        let (mut grid, now) = (Grid::default(), Instant::now());
        tick(&mut grid, 1, Kind::Sink, 990, 1_000, now);
        let panel = tick(&mut grid, 0, Kind::Source, 100, 10_000, now);
        assert_eq!(panel, 90);
    }

    #[test]
    fn a_block_that_stopped_ticking_is_paid_nothing() {
        let (mut grid, then) = (Grid::default(), Instant::now());
        tick(&mut grid, 1, Kind::Sink, 0, 1_000, then);
        let later = then + Duration::from_secs(5);
        let panel = tick(&mut grid, 0, Kind::Source, 100, 10_000, later);
        assert_eq!(panel, 100);
    }

    #[test]
    fn other_dimensions_are_apart() {
        let (mut grid, now) = (Grid::default(), Instant::now());
        let nether = ("minecraft:the_nether", [1, 0, 0]);
        grid.settle(nether, Kind::Sink, 0, 1_000, now);
        let panel = tick(&mut grid, 0, Kind::Source, 100, 10_000, now);
        assert_eq!(panel, 100);
    }
}
