// Yıldız Yolu – özel eşyalar (KubeJS 2101 / Minecraft 1.21.1 NeoForge)
// İsimler ve açıklamalar assets/kubejs/lang/*.json dosyalarından gelir.

StartupEvents.registry('item', event => {
  // Ara malzemeler
  event.create('stellar_essence')
    .rarity('uncommon')
    .tooltip(Text.translatable('tooltip.kubejs.stellar_essence').gray())

  event.create('cosmic_core')
    .rarity('rare')
    .glow(true)
    .tooltip(Text.translatable('tooltip.kubejs.cosmic_core').gray())

  event.create('creative_catalyst')
    .rarity('epic')
    .glow(true)
    .tooltip(Text.translatable('tooltip.kubejs.creative_catalyst').lightPurple())

  // Yaratıcı uçuş yüzüğü (uçma mantığı server_scripts/ucus_yuzugu.js içinde)
  event.create('flight_ring')
    .rarity('epic')
    .maxStackSize(1)
    .glow(true)
    .tooltip(Text.translatable('tooltip.kubejs.flight_ring').aqua())

  // Final eşyası
  event.create('heart_of_the_stars')
    .rarity('epic')
    .maxStackSize(1)
    .glow(true)
    .fireResistant(true)
    .tooltip(Text.translatable('tooltip.kubejs.heart_of_the_stars').gold())

  // Paket bitirme ödülü – yalnızca final görevinden kazanılır, tarifi yoktur
  event.create('completion_medal')
    .rarity('epic')
    .maxStackSize(1)
    .glow(true)
    .fireResistant(true)
    .tooltip(Text.translatable('tooltip.kubejs.completion_medal.1').gold().bold())
    .tooltip(Text.translatable('tooltip.kubejs.completion_medal.2').gray().italic())
})
