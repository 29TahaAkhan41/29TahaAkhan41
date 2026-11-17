// Yıldız Yolu – özel tarifler
// Yüklü olmayan bir modun tarifi atlanır, böylece paket mod eksikliğinde çökmez.

ServerEvents.recipes(event => {
  const has = id => Platform.isLoaded(id)

  // --- Ara malzemeler -------------------------------------------------------
  // Yıldız Özü: Astral Sorcery malzemeleri
  event.shaped(Item.of('kubejs:stellar_essence', 2), [
    'DSD',
    'LGL',
    'DSD'
  ], {
    D: 'astralsorcery:stardust',
    S: 'astralsorcery:starmetal_ingot',
    L: 'astralsorcery:lumen_crystal',
    G: 'astralsorcery:resonating_gem'
  }).id('kubejs:stellar_essence')

  // Kozmik Çekirdek: her bölümden bir parça
  event.shaped('kubejs:cosmic_core', [
    'EME',
    'ANB',
    'ECE'
  ], {
    E: 'kubejs:stellar_essence',
    N: 'minecraft:nether_star',
    M: has('mekanism') ? 'mekanism:ultimate_control_circuit' : 'minecraft:netherite_ingot',
    A: has('ae2') ? 'ae2:singularity' : 'minecraft:diamond_block',
    B: has('botania') ? 'botania:terrasteel_ingot' : 'minecraft:emerald_block',
    C: has('create') ? 'create:brass_casing' : 'minecraft:gold_block'
  }).id('kubejs:cosmic_core')

  // Yaratıcı Katalizör
  event.shaped('kubejs:creative_catalyst', [
    'CXC',
    'KAK',
    'CDC'
  ], {
    C: 'kubejs:cosmic_core',
    X: 'astralsorcery:artifact',
    K: 'astralsorcery:akashic_singularity',
    A: 'astralsorcery:attuned_celestial_crystal',
    D: 'minecraft:dragon_egg'
  }).id('kubejs:creative_catalyst')

  // --- Yaratıcı eşyalar -----------------------------------------------------
  const creative = (result, center, key) => {
    event.shaped(result, [
      'SES',
      'ZCZ',
      'SES'
    ], {
      C: 'kubejs:creative_catalyst',
      Z: center,
      E: 'kubejs:stellar_essence',
      S: 'minecraft:nether_star'
    }).id('kubejs:creative/' + key)
  }

  creative('kubejs:flight_ring', 'minecraft:elytra', 'flight_ring')

  if (has('mekanism')) {
    creative('mekanism:creative_energy_cube', 'mekanism:ultimate_energy_cube', 'energy_cube')
    creative('mekanism:creative_fluid_tank', 'mekanism:ultimate_fluid_tank', 'fluid_tank')
    creative('mekanism:creative_bin', 'mekanism:ultimate_bin', 'bin')
  }
  if (has('ae2')) {
    creative('ae2:creative_energy_cell', 'ae2:dense_energy_cell', 'energy_cell')
  }
  if (has('create')) {
    creative('create:creative_motor', 'create:rotation_speed_controller', 'motor')
    creative('create:creative_crate', 'create:item_vault', 'crate')
  }
  if (has('botania')) {
    creative('botania:creative_pool', 'botania:fabulous_pool', 'mana_pool')
  }
  if (has('ars_nouveau')) {
    creative('ars_nouveau:creative_source_jar', 'ars_nouveau:source_jar', 'source_jar')
  }

  // --- Final: Yıldızların Kalbi ---------------------------------------------
  const heartKey = {
    C: 'kubejs:creative_catalyst',
    X: 'astralsorcery:artifact',
    R: 'kubejs:flight_ring',
    E: has('mekanism') ? 'mekanism:creative_energy_cube' : 'minecraft:nether_star',
    M: has('create') ? 'create:creative_motor' : 'minecraft:nether_star',
    P: has('botania') ? 'botania:creative_pool' : 'minecraft:nether_star',
    J: has('ars_nouveau') ? 'ars_nouveau:creative_source_jar' : 'minecraft:nether_star',
    A: has('ae2') ? 'ae2:creative_energy_cell' : 'minecraft:nether_star',
    T: has('twilightforest') ? 'twilightforest:snow_queen_trophy' : 'minecraft:dragon_egg'
  }
  event.shaped('kubejs:heart_of_the_stars', [
    'EMP',
    'RXJ',
    'ACT'
  ], heartKey).id('kubejs:heart_of_the_stars')
})
