//! What the electric furnace does with its two slots: the recipes it reads and one tick
//! of smelting.
use std::collections::HashMap;

use horizon_client::mod_api::ItemStack;
use horizon_client::mod_api::serde_json::Value;

/// The recipe type the furnace runs: `data/<namespace>/recipe/*.json` files of this type,
/// in the content mod or a data pack.
pub const RECIPE_TYPE: &str = "solartech:electric_smelting";

/// The energy one tick of smelting uses.
pub const ENERGY_PER_TICK: i32 = 20;
/// The ticks one item takes: half a vanilla furnace's.
pub const TICKS_PER_ITEM: i32 = 100;

/// What an item smelts into, by the item's id.
pub type Recipes = HashMap<String, Smelted>;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Smelted {
    pub item: String,
    pub count: u32,
}

/// A recipe file: `{"ingredient": "minecraft:raw_iron", "result": {"id": "minecraft:iron_ingot"}}`,
/// with an optional `count` in `result`. A bare id is `minecraft:`.
pub fn recipe(json: &Value) -> Option<(String, Smelted)> {
    let ingredient = json.get("ingredient")?.as_str()?;
    let result = json.get("result")?;
    let item = result.get("id")?.as_str()?;
    let count = match result.get("count") {
        Some(count) => u32::try_from(count.as_u64()?).ok()?,
        None => 1,
    };
    (1..=64).contains(&count).then(|| {
        (
            qualified(ingredient),
            Smelted {
                item: qualified(item),
                count,
            },
        )
    })
}

fn qualified(id: &str) -> String {
    if id.contains(':') {
        id.to_owned()
    } else {
        format!("minecraft:{id}")
    }
}

/// What a tick of the furnace did.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Step {
    /// Nothing to smelt, or no room for the result: progress is lost.
    Idle,
    /// Something to smelt but not enough energy: progress waits.
    Starved,
    /// A tick of smelting, paid for.
    Worked,
}

/// One tick: smelts `input` into `output` when a recipe fits, there is room and the
/// energy is there. `max_stack` is the most of the result one slot holds.
pub fn step(
    recipes: &Recipes,
    input: &mut Option<ItemStack>,
    output: &mut Option<ItemStack>,
    energy: &mut i32,
    progress: &mut i32,
    max_stack: impl Fn(&str) -> u32,
) -> Step {
    let smelted = input
        .as_ref()
        .filter(|stack| stack.count > 0)
        .and_then(|stack| recipes.get(&*stack.item));
    let Some(smelted) = smelted.filter(|s| fits(output.as_ref(), s, max_stack(&s.item))) else {
        *progress = 0;
        return Step::Idle;
    };
    if *energy < ENERGY_PER_TICK {
        return Step::Starved;
    }
    *energy -= ENERGY_PER_TICK;
    *progress += 1;
    if *progress >= TICKS_PER_ITEM {
        *progress = 0;
        match output {
            Some(stack) => stack.count += smelted.count,
            None => *output = Some(ItemStack::new(&smelted.item, smelted.count)),
        }
        if let Some(stack) = input {
            stack.count -= 1;
            if stack.count == 0 {
                *input = None;
            }
        }
    }
    Step::Worked
}

/// Whether the result goes into the output slot: an empty slot, or a plain stack of the
/// same item with room.
fn fits(output: Option<&ItemStack>, smelted: &Smelted, max_stack: u32) -> bool {
    match output {
        None => true,
        Some(stack) => {
            &*stack.item == smelted.item
                && stack.damage == 0
                && stack.extra.is_none()
                && stack.count + smelted.count <= max_stack
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn recipes() -> Recipes {
        let mut recipes = Recipes::new();
        recipes.insert(
            "minecraft:raw_iron".into(),
            Smelted {
                item: "minecraft:iron_ingot".into(),
                count: 1,
            },
        );
        recipes
    }

    fn run(
        input: &mut Option<ItemStack>,
        output: &mut Option<ItemStack>,
        energy: &mut i32,
        progress: &mut i32,
    ) -> Step {
        step(&recipes(), input, output, energy, progress, |_| 64)
    }

    #[test]
    fn an_item_takes_its_ticks_and_its_energy() {
        let mut input = Some(ItemStack::new("minecraft:raw_iron", 2));
        let (mut output, mut energy, mut progress) = (None, 10_000, 0);
        for _ in 0..TICKS_PER_ITEM - 1 {
            assert_eq!(run(&mut input, &mut output, &mut energy, &mut progress), Step::Worked);
        }
        assert!(output.is_none());
        assert_eq!(run(&mut input, &mut output, &mut energy, &mut progress), Step::Worked);
        let made = output.as_ref().unwrap();
        assert_eq!((&*made.item, made.count), ("minecraft:iron_ingot", 1));
        assert_eq!(input.as_ref().unwrap().count, 1);
        assert_eq!(energy, 10_000 - ENERGY_PER_TICK * TICKS_PER_ITEM);
        assert_eq!(progress, 0);
    }

    #[test]
    fn the_last_item_empties_the_slot() {
        let mut input = Some(ItemStack::new("minecraft:raw_iron", 1));
        let (mut output, mut energy, mut progress) = (None, 10_000, TICKS_PER_ITEM - 1);
        run(&mut input, &mut output, &mut energy, &mut progress);
        assert!(input.is_none());
        assert_eq!(run(&mut input, &mut output, &mut energy, &mut progress), Step::Idle);
    }

    #[test]
    fn without_energy_progress_waits() {
        let mut input = Some(ItemStack::new("minecraft:raw_iron", 1));
        let (mut output, mut energy, mut progress) = (None, ENERGY_PER_TICK - 1, 40);
        assert_eq!(run(&mut input, &mut output, &mut energy, &mut progress), Step::Starved);
        assert_eq!((energy, progress), (ENERGY_PER_TICK - 1, 40));
    }

    #[test]
    fn an_item_with_no_recipe_or_a_full_output_does_nothing() {
        let mut dirt = Some(ItemStack::new("minecraft:dirt", 1));
        let (mut output, mut energy, mut progress) = (None, 10_000, 40);
        assert_eq!(run(&mut dirt, &mut output, &mut energy, &mut progress), Step::Idle);
        assert_eq!((energy, progress), (10_000, 0));

        let mut input = Some(ItemStack::new("minecraft:raw_iron", 1));
        let mut full = Some(ItemStack::new("minecraft:iron_ingot", 64));
        assert_eq!(run(&mut input, &mut full, &mut energy, &mut progress), Step::Idle);
        let mut other = Some(ItemStack::new("minecraft:gold_ingot", 1));
        assert_eq!(run(&mut input, &mut other, &mut energy, &mut progress), Step::Idle);
        assert_eq!(energy, 10_000);
    }
}
