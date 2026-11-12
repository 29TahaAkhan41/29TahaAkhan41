//! SolarTech: the code half of the mod. The launcher links this crate into the game and
//! calls `hooks()`; each method of `Hooks` is one of Horizon's hook points.
//!
//! The blocks themselves (their models, recipes and loot) are declared by the content mod
//! of the same id. This crate gives them their behaviour:
//!
//! - `solartech:solar_panel` turns sunlight into energy,
//! - `solartech:energy_cable` carries it,
//! - `solartech:electric_furnace` smelts with it.
//!
//! Each has a block entity that keeps its energy in the saved int `energy`, the field
//! Horizon's own energy buffers use, and moves it through the grid in `grid.rs`. The panel
//! and the furnace open a screen drawn in `screens.rs`.
mod grid;
mod screens;
mod smelting;

use std::sync::{Mutex, PoisonError};
use std::time::{Duration, Instant};

use horizon_client::mod_api::{
    BlockEntityContainerEvent, BlockEntityEnergyEvent, BlockEntityEvent, BlockEntityTickEvent,
    BlockEntityTicksEvent, Compound, Hooks, Host, ModContainer, ModEnergyBuffer, NativeScreen,
    ScreenDrawEvent, ScreenEvent, ScreenTooltipEvent, Tag,
};

use grid::{Grid, Kind, TRANSFER};
use smelting::{Recipes, Step};

/// The blocks, which are also the ids of their block entities and of their menu types.
const PANEL: &str = "solartech:solar_panel";
const CABLE: &str = "solartech:energy_cable";
const FURNACE: &str = "solartech:electric_furnace";

/// The saved int Horizon's energy helpers read and write (`native_block_entity_energy`).
const ENERGY: &str = "energy";
/// The furnace's saved smelting progress, in ticks.
const PROGRESS: &str = "progress";

/// How much each block holds.
const PANEL_CAPACITY: i32 = 100_000;
const CABLE_CAPACITY: i32 = 2_000;
const FURNACE_CAPACITY: i32 = 20_000;
/// What a panel makes each tick at noon, under a clear sky.
const PEAK_OUTPUT: i32 = 20;

/// The furnace's slots.
const INPUT: usize = 0;
const OUTPUT: usize = 1;

/// How long the furnace keeps the recipes it read before reading them again, so a data
/// pack's `/reload` reaches it.
const RECIPES_KEPT: Duration = Duration::from_secs(5);

pub fn hooks() -> Box<dyn Hooks> {
    Box::new(SolarTech::default())
}

#[derive(Default)]
struct SolarTech {
    grid: Mutex<Grid>,
    recipes: Mutex<Option<(Instant, Recipes)>>,
}

impl Hooks for SolarTech {
    /// Each block has a block entity: an empty buffer when it is placed.
    fn block_entity(
        &self,
        _host: &mut dyn Host,
        event: &mut BlockEntityEvent,
    ) -> Option<(String, Compound)> {
        matches!(event.block, PANEL | CABLE | FURNACE).then(|| {
            let mut nbt = Compound::new();
            nbt.insert(ENERGY.into(), Tag::Int(0));
            (event.block.to_owned(), nbt)
        })
    }

    /// They tick on the server.
    fn block_entity_ticks(&self, _host: &dyn Host, event: &mut BlockEntityTicksEvent) {
        if matches!(event.block, PANEL | CABLE | FURNACE) {
            event.ticks = true;
        }
    }

    /// Their buffers, for other mods' cables and machines: Horizon's energy helpers read
    /// them. A panel only gives, a furnace only takes, a cable does both.
    fn block_entity_energy(
        &self,
        _host: &dyn Host,
        event: &mut BlockEntityEnergyEvent,
    ) -> Option<ModEnergyBuffer> {
        // By `Direction`: down, up, north, south, west, east.
        let all = [true; 6];
        let none = [false; 6];
        let (capacity, insert_faces, extract_faces) = match event.block {
            PANEL => (PANEL_CAPACITY, none, [true, false, true, true, true, true]),
            CABLE => (CABLE_CAPACITY, all, all),
            FURNACE => (FURNACE_CAPACITY, all, none),
            _ => return None,
        };
        Some(ModEnergyBuffer {
            capacity,
            max_insert: if insert_faces == none { 0 } else { TRANSFER },
            max_extract: if extract_faces == none { 0 } else { TRANSFER },
            insert_faces,
            extract_faces,
        })
    }

    /// The panel and the furnace open a menu of their own type (the content mod's
    /// `data/solartech/horizon/menu/`), shown by the screens below.
    fn block_entity_container(
        &self,
        _host: &dyn Host,
        event: &mut BlockEntityContainerEvent,
    ) -> Option<ModContainer> {
        match event.block {
            // A menu needs a container. The panel's one slot is never shown, and no
            // face reaches it.
            PANEL => Some(ModContainer {
                slots: 1,
                menu: Some(PANEL.to_owned()),
                ..ModContainer::default()
            }),
            // Hoppers fill the input from above and the sides and empty the output
            // from below.
            FURNACE => Some(ModContainer {
                slots: 2,
                faces: [
                    vec![OUTPUT],
                    vec![INPUT],
                    vec![INPUT],
                    vec![INPUT],
                    vec![INPUT],
                    vec![INPUT],
                ],
                inputs: vec![INPUT],
                outputs: vec![OUTPUT],
                menu: Some(FURNACE.to_owned()),
            }),
            _ => None,
        }
    }

    /// One server tick of a block: collect what the neighbours paid in, do the block's
    /// own work, pay the neighbours.
    fn block_entity_tick(&self, host: &mut dyn Host, event: &mut BlockEntityTickEvent) {
        let (kind, capacity) = match event.entity.id.as_str() {
            PANEL => (Kind::Source, PANEL_CAPACITY),
            CABLE => (Kind::Cable, CABLE_CAPACITY),
            FURNACE => (Kind::Sink, FURNACE_CAPACITY),
            _ => return,
        };
        let place = (host.dimension(), event.pos);
        let before = int(&event.entity.nbt, ENERGY);
        let mut energy = self.grid().collect(place, before, capacity);

        match kind {
            Kind::Source => {
                let [x, y, z] = event.pos;
                let (_block_light, sky_light) = host.light([x, y + 1, z]);
                let (rain, thunder) = host.weather();
                let output = output(host.day_time(), sky_light, rain, thunder);
                energy = (energy + output).min(capacity);
                // The cells light up while the sun is on them. The game refuses a
                // write that changes nothing, so this is a state change at dawn and
                // dusk only.
                let active = if output > 0 { "true" } else { "false" };
                host.set_block_property(event.pos, "active", active);
                // What the screen shows: data slots are 16 bits wide.
                let [low, high] = screens::split(energy);
                set_data(event, vec![low, high, output]);
            }
            Kind::Cable => {}
            Kind::Sink => {
                let recipes = self.recipes(&*host);
                let mut progress = int(&event.entity.nbt, PROGRESS);
                let was = progress;
                if event.entity.items.len() <= OUTPUT {
                    event.entity.items.resize(OUTPUT + 1, None);
                }
                // Smelt on copies and write back what changed: a write through
                // `entity` marks it changed.
                let mut input = event.entity.items[INPUT].clone();
                let mut output = event.entity.items[OUTPUT].clone();
                let step = smelting::step(
                    &recipes,
                    &mut input,
                    &mut output,
                    &mut energy,
                    &mut progress,
                    |item| host.max_stack_size(item).unwrap_or(64),
                );
                if input != event.entity.items[INPUT] {
                    event.entity.items[INPUT] = input;
                }
                if output != event.entity.items[OUTPUT] {
                    event.entity.items[OUTPUT] = output;
                }
                if progress != was {
                    event.entity.nbt.insert(PROGRESS.into(), Tag::Int(progress));
                }
                let lit = if step == Step::Worked { "true" } else { "false" };
                host.set_block_property(event.pos, "lit", lit);
                let [low, high] = screens::split(energy);
                set_data(event, vec![low, high, progress, smelting::TICKS_PER_ITEM]);
            }
        }

        let energy = self
            .grid()
            .settle(place, kind, energy, capacity, Instant::now());
        if energy != before {
            event.entity.nbt.insert(ENERGY.into(), Tag::Int(energy));
        }
    }

    /// Where the slots of a block's screen are. The server asks too: a slot left out
    /// here is not in its menu either.
    fn screen(&self, _host: &dyn Host, event: &mut ScreenEvent) -> Option<NativeScreen> {
        match event.block {
            PANEL => Some(screens::panel_layout()),
            FURNACE => Some(screens::furnace_layout()),
            _ => None,
        }
    }

    /// Draws a block's screen from its menu's data slots.
    fn screen_draw(&self, host: &dyn Host, event: &mut ScreenDrawEvent) {
        match event.block {
            PANEL => screens::draw_panel(host, event.batch, event.origin, event.data),
            FURNACE => screens::draw_furnace(host, event.batch, event.origin, event.data),
            _ => {}
        }
    }

    /// The exact numbers, over a screen's bars.
    fn screen_tooltip(&self, _host: &dyn Host, event: &mut ScreenTooltipEvent) {
        let line = match event.block {
            PANEL => screens::panel_tooltip(event.at, event.data),
            FURNACE => screens::furnace_tooltip(event.at, event.data),
            _ => None,
        };
        event.lines.extend(line);
    }
}

impl SolarTech {
    fn grid(&self) -> std::sync::MutexGuard<'_, Grid> {
        self.grid.lock().unwrap_or_else(PoisonError::into_inner)
    }

    /// The furnace's recipes: the files of its type in the content mod and the world's
    /// data packs, read again every few seconds.
    fn recipes(&self, host: &dyn Host) -> Recipes {
        let mut kept = self.recipes.lock().unwrap_or_else(PoisonError::into_inner);
        let now = Instant::now();
        match &*kept {
            Some((read, recipes)) if now.saturating_duration_since(*read) < RECIPES_KEPT => {
                recipes.clone()
            }
            _ => {
                let recipes: Recipes = host
                    .recipes_of_type(smelting::RECIPE_TYPE)
                    .iter()
                    .filter_map(|recipe| smelting::recipe(&recipe.json))
                    .collect();
                *kept = Some((now, recipes.clone()));
                recipes
            }
        }
    }
}

/// Sets the data slots a block's menu shows, when they changed.
fn set_data(event: &mut BlockEntityTickEvent, data: Vec<i32>) {
    if event.entity.data != data {
        event.entity.data = data;
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

    #[test]
    fn one_panel_at_noon_keeps_one_furnace_running() {
        assert!(PEAK_OUTPUT >= smelting::ENERGY_PER_TICK);
    }
}
