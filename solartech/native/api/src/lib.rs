//! SolarTech: the code half of the mod. The launcher links this crate into the game and
//! calls `hooks()`; each method of `Hooks` is one of Horizon's hook points.
//!
//! The block itself (`solartech:solar_panel`, its model, recipe and loot) is declared by
//! the content mod of the same id. This crate gives it:
//!
//! - a block entity that is saved with the chunk (`block_entity`),
//! - an energy buffer other mods' machines and cables can drain (`block_entity_energy`),
//! - a server tick that turns sunlight into energy (`block_entity_tick`),
//! - a read-out on the action bar when it is clicked with a stick (`use_item_on`).
use std::collections::HashMap;
use std::sync::{Mutex, PoisonError};

use horizon_client::mod_api::{
    BlockEntityEnergyEvent, BlockEntityEvent, BlockEntityTickEvent, BlockEntityTicksEvent,
    Compound, Flow, Hooks, Host, ModEnergyBuffer, Tag, Text, UseItemOnEvent,
};

/// The block, and the id of its block entity.
const PANEL: &str = "solartech:solar_panel";
/// The item that reads a panel's charge.
const METER: &str = "minecraft:stick";
/// The saved int Horizon's energy helpers read and write (`native_block_entity_energy`).
const ENERGY: &str = "energy";
/// How much one panel holds.
const CAPACITY: i32 = 100_000;
/// What it makes each tick at noon, under a clear sky.
const PEAK_OUTPUT: i32 = 20;
/// The most one extract takes.
const MAX_EXTRACT: i32 = 200;

pub fn hooks() -> Box<dyn Hooks> {
    Box::new(SolarTech::default())
}

/// A panel's place: its dimension and position.
type Place = (&'static str, [i32; 3]);

#[derive(Default)]
struct SolarTech {
    /// What each ticking panel holds and makes, for the stick's read-out: the hooks
    /// that hear a click are not handed the block entity. Never saved; a panel is
    /// back in it on its first tick after a load.
    panels: Mutex<HashMap<Place, Reading>>,
}

/// A panel's stored energy and what it made last tick.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Reading {
    stored: i32,
    output: i32,
}

impl Hooks for SolarTech {
    /// The panel has a block entity: an empty buffer when it is placed.
    fn block_entity(
        &self,
        _host: &mut dyn Host,
        event: &mut BlockEntityEvent,
    ) -> Option<(String, Compound)> {
        (event.block == PANEL).then(|| {
            let mut nbt = Compound::new();
            nbt.insert(ENERGY.into(), Tag::Int(0));
            (PANEL.to_owned(), nbt)
        })
    }

    /// It ticks on the server.
    fn block_entity_ticks(&self, _host: &dyn Host, event: &mut BlockEntityTicksEvent) {
        if event.block == PANEL {
            event.ticks = true;
        }
    }

    /// Its buffer: nothing goes in, and energy leaves by every face but the top.
    fn block_entity_energy(
        &self,
        _host: &dyn Host,
        event: &mut BlockEntityEnergyEvent,
    ) -> Option<ModEnergyBuffer> {
        (event.block == PANEL).then(|| ModEnergyBuffer {
            capacity: CAPACITY,
            max_insert: 0,
            max_extract: MAX_EXTRACT,
            insert_faces: [false; 6],
            // By `Direction`: down, up, north, south, west, east.
            extract_faces: [true, false, true, true, true, true],
        })
    }

    /// One server tick of a panel: make energy from the sky above it.
    fn block_entity_tick(&self, host: &mut dyn Host, event: &mut BlockEntityTickEvent) {
        if event.entity.id != PANEL {
            return;
        }
        let [x, y, z] = event.pos;
        let (_block_light, sky_light) = host.light([x, y + 1, z]);
        let (rain, thunder) = host.weather();
        let output = output(host.day_time(), sky_light, rain, thunder);

        let stored = int(&event.entity.nbt, ENERGY);
        let charged = (stored + output).min(CAPACITY);
        // Each write through `entity` marks it changed, so only write what moved.
        if charged != stored {
            event.entity.nbt.insert(ENERGY.into(), Tag::Int(charged));
        }
        let reading = Reading { stored: charged, output };
        self.panels
            .lock()
            .unwrap_or_else(PoisonError::into_inner)
            .insert((host.dimension(), event.pos), reading);
        // The cells light up while the sun is on them. A write that changes nothing
        // is refused by the game, so this costs a state change at dawn and dusk only.
        let active = if output > 0 { "true" } else { "false" };
        host.set_block_property(event.pos, "active", active);
    }

    /// A stick on a panel reads its charge on the action bar.
    fn use_item_on(&self, host: &mut dyn Host, event: &mut UseItemOnEvent) -> Flow {
        if &*event.stack.item != METER || host.block(event.pos) != PANEL {
            return Flow::Continue;
        }
        let Some(player) = host.acting_player() else {
            return Flow::Continue;
        };
        let reading = self
            .panels
            .lock()
            .unwrap_or_else(PoisonError::into_inner)
            .get(&(host.dimension(), event.pos))
            .copied();
        let line = match reading {
            Some(Reading { stored, output }) => {
                format!("Solar Panel: {stored} / {CAPACITY} FE  (+{output} FE/t)")
            }
            // Placed this tick: it hasn't ticked yet.
            None => format!("Solar Panel: 0 / {CAPACITY} FE"),
        };
        host.action_bar(player.uuid, Text::colored(line, 0xFFD24A));
        Flow::Cancel
    }
}

/// The energy a panel makes this tick: the sun's height, dimmed by what is above the
/// panel and by the weather.
fn output(day_time: i64, sky_light: u8, rain: f32, thunder: f32) -> i32 {
    // A day is 24000 ticks: 0 is sunrise, 6000 noon, 12000 sunset. The sun gives light
    // a little before and after, so the curve runs from 23500 to 12500.
    let time = day_time.rem_euclid(24_000);
    let since_dawn = (time + 500).rem_euclid(24_000) as f32;
    if since_dawn > 13_000.0 {
        return 0;
    }
    let sun = (std::f32::consts::PI * since_dawn / 13_000.0).sin();
    let sky = f32::from(sky_light.min(15)) / 15.0;
    let weather = (1.0 - 0.6 * rain.clamp(0.0, 1.0) - 0.3 * thunder.clamp(0.0, 1.0)).max(0.1);
    (PEAK_OUTPUT as f32 * sun * sky * weather).round() as i32
}

/// The key type of a `Compound`, which `mod_api` doesn't name.
trait Keyed {
    type Key;
}
impl<K, V> Keyed for std::collections::BTreeMap<K, V> {
    type Key = K;
}
type Key = <Compound as Keyed>::Key;

/// An int of a compound, 0 when it has none.
fn int(nbt: &Compound, name: &str) -> i32 {
    match nbt.get(&Key::from(name)) {
        Some(Tag::Int(value)) => *value,
        _ => 0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn noon_under_a_clear_sky_is_the_peak() {
        assert_eq!(output(6_000, 15, 0.0, 0.0), PEAK_OUTPUT);
    }

    #[test]
    fn night_makes_nothing() {
        assert_eq!(output(18_000, 15, 0.0, 0.0), 0);
        assert_eq!(output(24_000 + 18_000, 15, 0.0, 0.0), 0);
    }

    #[test]
    fn a_roof_stops_it() {
        assert_eq!(output(6_000, 0, 0.0, 0.0), 0);
    }

    #[test]
    fn weather_dims_it() {
        let clear = output(6_000, 15, 0.0, 0.0);
        let rain = output(6_000, 15, 1.0, 0.0);
        let storm = output(6_000, 15, 1.0, 1.0);
        assert!(storm < rain && rain < clear, "{storm} {rain} {clear}");
        assert!(storm > 0);
    }

    #[test]
    fn a_missing_int_reads_zero() {
        let mut nbt = Compound::new();
        assert_eq!(int(&nbt, ENERGY), 0);
        nbt.insert(ENERGY.into(), Tag::Int(42));
        assert_eq!(int(&nbt, ENERGY), 42);
    }
}
