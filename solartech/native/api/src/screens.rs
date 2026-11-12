//! The screens of the solar panel and the electric furnace, drawn over Horizon's plain
//! container panel with rectangles and text: no GUI textures.
//!
//! A screen only knows the menu's data slots, which the block's tick fills
//! (`block_entity_tick`): the energy in two slots, since a data slot is 16 bits wide on
//! the network, then the panel's output, or the furnace's progress and its total.
//! Positions are in GUI pixels from the screen's top left, as vanilla's slots are.
use horizon_client::mod_api::{Host, HudBatch, NativeScreen};

use crate::{FURNACE_CAPACITY, PANEL_CAPACITY};

/// Vanilla's container screens: 176 by 166, the inventory from 84 down.
const WIDTH: f32 = 176.0;
const HEIGHT: f32 = 166.0;
const INVENTORY_Y: f32 = 84.0;

const LABEL: u32 = 0x40_40_40;
const FRAME: u32 = 0xFF37_3737;
const TROUGH: u32 = 0xFF8B_8B8B;
const CHARGE: u32 = 0xFFE8_B020;
const ARROW: u32 = 0xFFFF_FFFF;

/// The panel's energy bar: `[x, y, width, height]`.
const PANEL_BAR: [f32; 4] = [20.0, 36.0, 136.0, 12.0];
/// The furnace's energy bar, filled from the bottom, and its progress bar.
const FURNACE_BAR: [f32; 4] = [20.0, 17.0, 12.0, 52.0];
const FURNACE_ARROW: [f32; 4] = [80.0, 40.0, 24.0, 6.0];
/// The furnace's slots, where a vanilla furnace has its input column and its result.
const FURNACE_INPUT: [f32; 2] = [56.0, 35.0];
const FURNACE_OUTPUT: [f32; 2] = [116.0, 35.0];

/// An amount in two data slots of 15 bits each.
pub fn split(amount: i32) -> [i32; 2] {
    let amount = amount.max(0);
    [amount & 0x7FFF, amount >> 15]
}

fn slot(data: &[i32], index: usize) -> i32 {
    data.get(index).copied().unwrap_or(0).max(0)
}

/// The amount `split` put in the first two data slots.
fn energy(data: &[i32]) -> i32 {
    (slot(data, 0) & 0x7FFF) | (slot(data, 1) << 15)
}

/// The panel has no slots to show: its one container slot is left out.
pub fn panel_layout() -> NativeScreen {
    NativeScreen {
        width: WIDTH,
        height: HEIGHT,
        slots: vec![None],
        inventory_y: INVENTORY_Y,
        inventory_x: 8.0,
        ..NativeScreen::default()
    }
}

pub fn furnace_layout() -> NativeScreen {
    NativeScreen {
        width: WIDTH,
        height: HEIGHT,
        slots: vec![Some(FURNACE_INPUT), Some(FURNACE_OUTPUT)],
        inventory_y: INVENTORY_Y,
        inventory_x: 8.0,
        ..NativeScreen::default()
    }
}

pub fn draw_panel(host: &dyn Host, batch: &mut HudBatch, origin: [f32; 2], data: &[i32]) {
    let (stored, output) = (energy(data), slot(data, 2));
    let line = format!("Depo: {stored} / {PANEL_CAPACITY} FE");
    host.text(batch, &line, at(origin, [PANEL_BAR[0], 22.0]), LABEL, false);
    let filled = fill_of(stored, PANEL_CAPACITY, PANEL_BAR[2]);
    bar(host, batch, origin, PANEL_BAR, [PANEL_BAR[0], PANEL_BAR[1], filled, PANEL_BAR[3]], CHARGE);
    let line = if output > 0 {
        format!("Üretim: +{output} FE/t")
    } else {
        "Üretim yok: güneş görmüyor".to_owned()
    };
    host.text(batch, &line, at(origin, [PANEL_BAR[0], 56.0]), LABEL, false);
}

pub fn draw_furnace(host: &dyn Host, batch: &mut HudBatch, origin: [f32; 2], data: &[i32]) {
    let stored = energy(data);
    let [x, y, width, height] = FURNACE_BAR;
    let filled = fill_of(stored, FURNACE_CAPACITY, height);
    bar(host, batch, origin, FURNACE_BAR, [x, y + height - filled, width, filled], CHARGE);
    let [x, y, width, height] = FURNACE_ARROW;
    let done = fill_of(slot(data, 2), slot(data, 3), width);
    bar(host, batch, origin, FURNACE_ARROW, [x, y, done, height], ARROW);
}

pub fn panel_tooltip(at: [f32; 2], data: &[i32]) -> Option<String> {
    inside(at, PANEL_BAR).then(|| format!("{} / {PANEL_CAPACITY} FE", energy(data)))
}

pub fn furnace_tooltip(at: [f32; 2], data: &[i32]) -> Option<String> {
    if inside(at, FURNACE_BAR) {
        Some(format!("{} / {FURNACE_CAPACITY} FE", energy(data)))
    } else if inside(at, FURNACE_ARROW) && slot(data, 3) > 0 {
        Some(format!("%{}", slot(data, 2) * 100 / slot(data, 3)))
    } else {
        None
    }
}

/// A framed trough with `filled` (a rectangle inside it) in `colour`.
fn bar(
    host: &dyn Host,
    batch: &mut HudBatch,
    origin: [f32; 2],
    [x, y, width, height]: [f32; 4],
    filled: [f32; 4],
    colour: u32,
) {
    let [ox, oy] = origin;
    host.fill(batch, [ox + x - 1.0, oy + y - 1.0, width + 2.0, height + 2.0], FRAME);
    host.fill(batch, [ox + x, oy + y, width, height], TROUGH);
    if filled[2] > 0.0 && filled[3] > 0.0 {
        host.fill(batch, [ox + filled[0], oy + filled[1], filled[2], filled[3]], colour);
    }
}

/// How many of `length` pixels `amount` of `total` fills, in whole pixels.
fn fill_of(amount: i32, total: i32, length: f32) -> f32 {
    if total <= 0 {
        return 0.0;
    }
    let part = f64::from(amount.clamp(0, total)) / f64::from(total);
    (part * f64::from(length)).floor() as f32
}

fn at([ox, oy]: [f32; 2], [x, y]: [f32; 2]) -> [f32; 2] {
    [ox + x, oy + y]
}

fn inside([px, py]: [f32; 2], [x, y, width, height]: [f32; 4]) -> bool {
    (x..x + width).contains(&px) && (y..y + height).contains(&py)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn energy_survives_the_data_slots() {
        for amount in [0, 1, 32_767, 32_768, 20_000, PANEL_CAPACITY] {
            let data = split(amount);
            assert!(data.iter().all(|slot| (0..=i32::from(i16::MAX)).contains(slot)));
            assert_eq!(energy(&data), amount);
        }
    }

    #[test]
    fn data_that_has_not_arrived_reads_empty() {
        assert_eq!(energy(&[]), 0);
        assert_eq!(panel_tooltip([30.0, 40.0], &[]).as_deref(), Some("0 / 100000 FE"));
        assert_eq!(furnace_tooltip([90.0, 42.0], &[]), None);
    }

    #[test]
    fn bars_fill_in_whole_pixels_and_never_overflow() {
        assert_eq!(fill_of(0, 100, 52.0), 0.0);
        assert_eq!(fill_of(50, 100, 52.0), 26.0);
        assert_eq!(fill_of(100, 100, 52.0), 52.0);
        assert_eq!(fill_of(500, 100, 52.0), 52.0);
        assert_eq!(fill_of(50, 0, 52.0), 0.0);
    }

    #[test]
    fn tooltips_are_over_the_bars_only() {
        let data = [split(1_234)[0], 0, 25, 100];
        assert_eq!(furnace_tooltip([25.0, 30.0], &data).as_deref(), Some("1234 / 20000 FE"));
        assert_eq!(furnace_tooltip([90.0, 42.0], &data).as_deref(), Some("%25"));
        assert_eq!(furnace_tooltip([60.0, 40.0], &data), None);
        assert_eq!(panel_tooltip([10.0, 40.0], &data), None);
    }

    #[test]
    fn the_furnace_shows_both_its_slots() {
        assert_eq!(furnace_layout().slots.len(), 2);
        assert_eq!(panel_layout().slots, vec![None]);
    }
}
