// Yıldız Yolu – oyun sonu tarifleri (Extended Crafting masaları)
//
// Zincir:
//   Yıldız Özü (3x3) ─┐
//   Teknoloji Çekirdeği   (Advanced 5x5)  ─┐
//   Dünya Çekirdeği       (Advanced 5x5)  ─┤
//   Büyü Çekirdeği        (Elite 7x7)     ─┼─► Kozmik Çekirdek (Elite 7x7) ─► Yaratıcı Katalizör x4 (Ultimate 9x9)
//   Doğa ve Macera Çekirdeği (Elite 7x7)  ─┘
//   Yaratıcı Katalizör ─► 18 yaratıcı eşya (Elite 7x7)
//   18 yaratıcı eşya + 5 çekirdek + ... ─► Yıldızların Kalbi (Ultimate 9x9)
//
// Bir mod yüklü değilse onun eşyası yerine Nether Yıldızı kullanılır; paket çökmez.

ServerEvents.recipes(event => {
  const it = id => Platform.isLoaded(id.split(':')[0]) ? id : 'minecraft:nether_star'
  const TIER = { basic: 1, advanced: 2, elite: 3, ultimate: 4 }

  // Extended Crafting masa tarifi. key: { harf: 'mod:eşya' }
  const table = (tier, result, count, pattern, key, id) => {
    const k = {}
    Object.keys(key).forEach(c => { k[c] = { item: it(key[c]) } })
    event.custom({
      type: 'extendedcrafting:shaped_table',
      tier: TIER[tier],
      pattern: pattern,
      key: k,
      result: { id: result, count: count }
    }).id('kubejs:' + id)
  }

  // --- Yıldız Özü (Astral Sorcery) – normal çalışma masası --------------------
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

  // --- Teknoloji Çekirdeği – Advanced 5x5 (20 teknoloji modu) ----------------
  table('advanced', 'kubejs:tech_core', 1, [
    'ABCDE',
    'FGHIJ',
    'KLXMN',
    'OPQRS',
    'TUVWY'
  ], {
    A: 'create:precision_mechanism',
    B: 'createaddition:electrum_ingot',
    C: 'mekanism:alloy_atomic',
    D: 'mekanismgenerators:turbine_casing',
    E: 'ae2:singularity',
    F: 'extendedae:entro_crystal',
    G: 'appmek:chemical_storage_cell_64k',
    H: 'powah:crystal_nitro',
    I: 'immersiveengineering:heavy_engineering',
    J: 'industrialforegoing:pink_slime_ingot',
    K: 'enderio:end_steel_ingot',
    L: 'pipez:ultimate_upgrade',
    X: 'mekanism:ultimate_control_circuit',
    M: 'ironfurnaces:netherite_furnace',
    N: 'modularrouters:speed_upgrade',
    O: 'laserio:laser_node',
    P: 'justdirethings:celestigem',
    Q: 'buildinggadgets2:template_manager',
    R: 'fluxnetworks:flux_controller',
    S: 'create_astral:starmetal_casing',
    T: 'appliedas:astral_processor',
    U: 'create:brass_casing',
    V: 'mekanism:pellet_polonium',
    W: 'ae2:engineering_processor',
    Y: 'powah:energy_cell_nitro'
  }, 'tech_core')

  // --- Dünya Çekirdeği – Advanced 5x5 (depolama, inşaat, kolaylık) -----------
  table('advanced', 'kubejs:world_core', 1, [
    'ABCDE',
    'FGHIJ',
    'KLXMN',
    'OPQRS',
    'TUVWY'
  ], {
    A: 'sophisticatedbackpacks:netherite_backpack',
    B: 'sophisticatedstorage:netherite_chest',
    C: 'functionalstorage:netherite_upgrade',
    D: 'storagedrawers:netherite_storage_upgrade',
    E: 'ironchest:diamond_chest',
    F: 'toms_storage:storage_terminal',
    G: 'torchmaster:megatorch',
    H: 'waystones:warp_stone',
    I: 'comforts:sleeping_bag_red',
    J: 'chipped:bordered_amethyst_block',
    K: 'rechiseled:netherite_block_chiseled',
    L: 'handcrafted:oak_table',
    X: 'extendedcrafting:crystaltine_ingot',
    M: 'framedblocks:framed_cube',
    N: 'supplementaries:speaker_block',
    O: 'quark:dragon_scale',
    P: 'mcwfurnitures:oak_desk',
    Q: 'mcwdoors:oak_barn_door',
    R: 'mcwwindows:oak_window',
    S: 'mcwroofs:oak_roof',
    T: 'mcwbridges:rope_oak_bridge',
    U: 'mcwlights:oak_tiki_torch',
    V: 'mcwfences:oak_picket_fence',
    W: 'biomesoplenty:rose_quartz_block',
    Y: 'minecraft:beacon'
  }, 'world_core')

  // --- Büyü Çekirdeği – Elite 7x7 (büyü modları + Astral) --------------------
  table('elite', 'kubejs:magic_core', 1, [
    'ABCDCBA',
    'BEFGFEB',
    'CFHIHFC',
    'DGJXJGD',
    'CFHIHFC',
    'BEFGFEB',
    'ABCDCBA'
  ], {
    A: 'evilcraft:dark_power_gem',
    B: 'malum:soul_stained_steel_ingot',
    C: 'ars_nouveau:source_gem_block',
    D: 'irons_spellbooks:arcane_ingot',
    E: 'ars_elemental:anima_essence',
    F: 'forbidden_arcanus:deorum_ingot',
    G: 'naturesaura:sky_ingot',
    H: 'malum:hallowed_gold_ingot',
    I: 'occultism:iesnium_ingot',
    J: 'apotheosis:gem_dust',
    X: 'kubejs:stellar_essence'
  }, 'magic_core')

  // --- Doğa ve Macera Çekirdeği – Elite 7x7 ----------------------------------
  table('elite', 'kubejs:nature_core', 1, [
    'ABCDCBA',
    'EFGHGFE',
    'IJKLKJI',
    'MNOXONM',
    'IJKLKJI',
    'EFGHGFE',
    'ABCDCBA'
  ], {
    A: 'twilightforest:knightmetal_ingot',
    B: 'aether:enchanted_gravitite',
    C: 'undergarden:forgotten_ingot',
    D: 'deeperdarker:soul_crystal',
    E: 'the_bumblezone:honey_crystal_shards',
    F: 'eternal_starlight:aethersent_ingot',
    G: 'cataclysm:ignitium_ingot',
    H: 'mowziesmobs:ice_crystal',
    I: 'mysticalagriculture:supremium_essence',
    J: 'naturalist:antler',
    K: 'productivebees:honey_treat',
    L: 'botanypots:terracotta_botany_pot',
    M: 'farmersdelight:rich_soil',
    N: 'croptopia:nether_star_cake',
    O: 'cookingforblockheads:fridge',
    X: 'twilightforest:fiery_ingot'
  }, 'nature_core')

  // --- Kozmik Çekirdek – Elite 7x7: dört çekirdek + yıldızlar -----------------
  table('elite', 'kubejs:cosmic_core', 1, [
    'ABCBCBA',
    'BEFEFEB',
    'CFTGMFC',
    'BEGXGEB',
    'CFZGWFC',
    'BEFEFEB',
    'ABCBCBA'
  ], {
    A: 'minecraft:nether_star',
    B: 'extendedcrafting:crystaltine_ingot',
    C: 'astralsorcery:starmetal_ingot',
    E: 'astralsorcery:lumen_crystal',
    F: 'extendedcrafting:elite_component',
    G: 'astralsorcery:celestial_crystal',
    T: 'kubejs:tech_core',
    M: 'kubejs:magic_core',
    Z: 'kubejs:nature_core',
    W: 'kubejs:world_core',
    X: 'mysticalagradditions:insanium_ingot'
  }, 'cosmic_core')

  // --- Yaratıcı Katalizör – Ultimate 9x9 (4 adet verir) ----------------------
  table('ultimate', 'kubejs:creative_catalyst', 4, [
    'NEEEDEEEN',
    'ECCCLCCCE',
    'ECKAAAKCE',
    'ECAGQGACE',
    'DLAQXQALD',
    'ECAGQGACE',
    'ECKAAAKCE',
    'ECCCLCCCE',
    'NEEEDEEEN'
  ], {
    N: 'minecraft:nether_star',
    E: 'extendedcrafting:crystaltine_ingot',
    D: 'minecraft:dragon_head',
    C: 'minecraft:netherite_ingot',
    L: 'astralsorcery:akashic_singularity',
    K: 'astralsorcery:attuned_celestial_crystal',
    A: 'extendedcrafting:ultimate_component',
    G: 'mekanism:pellet_antimatter',
    Q: 'kubejs:stellar_essence',
    X: 'kubejs:cosmic_core'
  }, 'creative_catalyst')

  // --- Yaratıcı eşyalar – Elite 7x7 ------------------------------------------
  // Ortada katalizör, çevresinde o modun en üst seviye eşyasından 4 tane.
  const creative = (result, top, key) => {
    table('elite', result, 1, [
      'NSSSSSN',
      'SEIIIES',
      'SIIZIIS',
      'SIZCZIS',
      'SIIZIIS',
      'SEIIIES',
      'NSSSSSN'
    ], {
      N: 'extendedcrafting:crystaltine_ingot',
      S: 'extendedcrafting:black_iron_ingot',
      E: 'kubejs:stellar_essence',
      I: 'extendedcrafting:elite_component',
      Z: top,
      C: 'kubejs:creative_catalyst'
    }, 'creative/' + key)
  }

  creative('kubejs:flight_ring', 'minecraft:elytra', 'flight_ring')
  const CREATIVE = [
    ['mekanism:creative_energy_cube', 'mekanism:ultimate_energy_cube', 'energy_cube'],
    ['mekanism:creative_fluid_tank', 'mekanism:ultimate_fluid_tank', 'fluid_tank'],
    ['mekanism:creative_bin', 'mekanism:ultimate_bin', 'bin'],
    ['mekanism:creative_chemical_tank', 'mekanism:ultimate_chemical_tank', 'chemical_tank'],
    ['ae2:creative_energy_cell', 'ae2:dense_energy_cell', 'energy_cell'],
    ['create:creative_motor', 'create:rotation_speed_controller', 'motor'],
    ['create:creative_crate', 'create:item_vault', 'crate'],
    ['create:creative_fluid_tank', 'create:fluid_tank', 'create_fluid_tank'],
    ['create:creative_blaze_cake', 'create:blaze_cake', 'blaze_cake'],
    ['evilcraft:creative_blood_drop', 'evilcraft:dark_tank', 'blood_drop'],
    ['ars_nouveau:creative_source_jar', 'ars_nouveau:source_jar', 'source_jar'],
    ['ars_nouveau:creative_spell_book', 'ars_nouveau:archmage_spell_book', 'spell_book'],
    ['powah:energy_cell_creative', 'powah:energy_cell_nitro', 'powah_cell'],
    ['immersiveengineering:capacitor_creative', 'immersiveengineering:capacitor_hv', 'capacitor'],
    ['storagedrawers:creative_storage_upgrade', 'storagedrawers:netherite_storage_upgrade', 'drawer_upgrade'],
    ['functionalstorage:creative_vending_upgrade', 'functionalstorage:netherite_upgrade', 'vending_upgrade'],
    ['mysticalagradditions:creative_essence', 'mysticalagradditions:insanium_ingot', 'creative_essence']
  ]
  CREATIVE.forEach(c => {
    if (Platform.isLoaded(c[0].split(':')[0])) creative(c[0], c[1], c[2])
  })

  // --- Final: Yıldızların Kalbi – Ultimate 9x9 -------------------------------
  table('ultimate', 'kubejs:heart_of_the_stars', 1, [
    'NSSSSSSSN',
    'SabcdefgS',
    'ShTPPPMiS',
    'SjPFQAPkS',
    'SlPGXGPmS',
    'SnPAEFPoS',
    'SpWJLOZqS',
    'SrBCKDIHS',
    'NSSSSSSSN'
  ], {
    N: 'minecraft:nether_star',
    S: 'extendedcrafting:crystaltine_ingot',
    P: 'extendedcrafting:ultimate_component',
    a: 'kubejs:flight_ring',
    b: 'mekanism:creative_energy_cube',
    c: 'mekanism:creative_fluid_tank',
    d: 'mekanism:creative_bin',
    e: 'mekanism:creative_chemical_tank',
    f: 'ae2:creative_energy_cell',
    g: 'create:creative_motor',
    h: 'create:creative_crate',
    i: 'create:creative_fluid_tank',
    j: 'create:creative_blaze_cake',
    k: 'evilcraft:creative_blood_drop',
    l: 'ars_nouveau:creative_source_jar',
    m: 'ars_nouveau:creative_spell_book',
    n: 'powah:energy_cell_creative',
    o: 'immersiveengineering:capacitor_creative',
    p: 'storagedrawers:creative_storage_upgrade',
    q: 'functionalstorage:creative_vending_upgrade',
    r: 'mysticalagradditions:creative_essence',
    T: 'kubejs:tech_core',
    M: 'kubejs:magic_core',
    Z: 'kubejs:nature_core',
    W: 'kubejs:world_core',
    K: 'kubejs:cosmic_core',
    F: 'astralsorcery:artifact',
    Q: 'twilightforest:snow_queen_trophy',
    A: 'astralsorcery:akashic_singularity',
    G: 'mekanism:pellet_antimatter',
    E: 'minecraft:dragon_egg',
    X: 'kubejs:creative_catalyst',
    B: 'mekanismtools:refined_obsidian_sword',
    C: 'mekanismadditions:aqua_plastic',
    D: 'apothic_enchanting:draconic_endshelf',
    I: 'naturescompass:naturescompass',
    J: 'explorerscompass:explorerscompass',
    L: 'akashictome:tome',
    O: 'gravestone:gravestone',
    H: 'artifacts:crystal_heart'
  }, 'heart_of_the_stars')
})
